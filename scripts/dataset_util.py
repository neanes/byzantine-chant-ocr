import cv2
import datetime
import imutils
import os
import pymupdf
import sys
import torch
import torch.nn as nn
from pathlib import Path
from PIL import Image
from torch.utils.data import DataLoader, Dataset

sys.path.append("../src")
from model import get_transform
from segmentation import segment
from text_removal import remove_text


class ImageDataset(Dataset):
    def __init__(self, image_folder, transform):
        self.image_paths = [
            os.path.join(image_folder, img_name)
            for img_name in os.listdir(image_folder)
        ]
        self.transform = transform

    def __len__(self):
        return len(self.image_paths)

    def __getitem__(self, idx):
        img_path = self.image_paths[idx]
        img = cv2.imread(img_path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(img)
        img_tensor = self.transform(img)
        return img_tensor, img_path


def process_pdf(pdf_path, page_range, pdf_folder, contour_folder, target_size=224):
    doc = pymupdf.open(pdf_path)
    total = 0
    for page_num in page_range:
        if page_num < 0 or page_num >= len(doc):
            print(f"Page {page_num} is out of range. Skipping.")
            continue
        page = doc.load_page(page_num)
        pix = page.get_pixmap(dpi=300)  # High DPI for quality
        filename = Path(pdf_path).stem
        img_path = os.path.join(pdf_folder, f"{filename}_p{page_num+1:04}.png")
        pix.save(img_path)

        # Resize the image
        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)

        img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
        segmentation = segment(img)
        img = remove_text(img, segmentation)

        blurred = cv2.GaussianBlur(img, (5, 5), 0)

        edged = cv2.Canny(blurred, 30, 150)

        contours = cv2.findContours(
            edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        contours = imutils.grab_contours(contours)

        for contour in contours:
            # Get the bounding box for each contour
            x, y, w, h = cv2.boundingRect(contour)
            (cx, cy), r = cv2.minEnclosingCircle(contour)
            cx = int(cx)
            cy = int(cy)
            r = int(r)

            # Filter out very small contours
            if w < 5:
                continue

            # Crop the region of interest (ROI) from the original image
            roi = img[y : y + h, x : x + w]

            scale = target_size / max(h, w)
            new_w = int(w * scale)
            new_h = int(h * scale)

            if new_w > 0 and new_h > 0:
                resized = cv2.resize(roi, (new_w, new_h), interpolation=cv2.INTER_CUBIC)

                (tH, tW) = resized.shape
                dX = int(max(0, target_size - tW) / 2.0)
                dY = int(max(0, target_size - tH) / 2.0)
                # pad the image and force dimensions
                padded = cv2.copyMakeBorder(
                    resized,
                    top=dY,
                    bottom=dY,
                    left=dX,
                    right=dX,
                    borderType=cv2.BORDER_CONSTANT,
                    value=(0, 0, 0),
                )
                padded = cv2.resize(
                    padded, (target_size, target_size), interpolation=cv2.INTER_CUBIC
                )

                img_path = os.path.join(
                    contour_folder,
                    f"{filename}_p{page_num+1:04}_x{x:04}_y{y:04}_w{w:04}_h{h:04}_cx{cx:04}_cy{cy:04}_r{r:04}.png",
                )
                cv2.imwrite(img_path, padded)

                total = total + 1

    return total


def predict_images(model, classes, image_folder):
    dataset = ImageDataset(image_folder, get_transform())
    data_loader = DataLoader(dataset, batch_size=32, shuffle=False)

    predictions = []
    model.eval()

    with torch.no_grad():
        for batch in data_loader:
            tensors, img_paths = batch
            outputs = model(tensors)

            probabilities = nn.functional.softmax(outputs, dim=1)
            class_ids = torch.argmax(probabilities, dim=1)
            confidences = probabilities[range(probabilities.size(0)), class_ids]

            for img_path, class_id, confidence in zip(
                img_paths, class_ids, confidences
            ):
                predictions.append(
                    {
                        "filepath": img_path,
                        "prediction": classes[class_id.item()],
                        "confidence": confidence.item(),
                    }
                )

    return predictions


def create_fo_dataset(predictions):
    import fiftyone as fo

    samples = []
    for pred in predictions:
        sample = fo.Sample(filepath=pred["filepath"])
        sample["prediction"] = fo.Classification(
            label=pred["prediction"], confidence=pred["confidence"]
        )
        samples.append(sample)

    # Create or load a FiftyOne dataset
    now = datetime.datetime.now()
    datetime_string = now.strftime("%Y%m%d%H%M%S")

    dataset_name = f"predictions_{datetime_string}"

    dataset = fo.Dataset(dataset_name)
    dataset.add_samples(samples)
    dataset.persistent = True
    dataset.save()

    return dataset
