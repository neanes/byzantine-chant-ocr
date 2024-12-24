import argparse
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
from torchvision import transforms

sys.path.append("../src")
from model import load_classes, load_model
from segmentation import segment
from text_removal import remove_text


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
    transform = transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )

    predictions = []
    model.eval()

    files = os.listdir(image_folder)

    for img_name in files:
        img_path = os.path.join(image_folder, img_name)
        img = cv2.imread(img_path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(img)

        tensor = transform(img).unsqueeze(0)

        with torch.no_grad():
            output = model(tensor)

        probabilities = nn.functional.softmax(output[0], dim=0)
        class_id = torch.argmax(probabilities).item()
        confidence = probabilities[class_id]

        predictions.append(
            {
                "filepath": img_path,
                "prediction": classes[class_id],
                "confidence": confidence,
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Creates a dataset from a PDF file with page range [start, end]"
    )
    parser.add_argument("infile", help="Relative path to the PDF file")
    parser.add_argument("start", help="The first page to use", type=int)
    parser.add_argument("end", help="The last page to use", type=int)
    parser.add_argument(
        "--pages",
        help="Relative path to the folder where page images will be saved",
        default="../data/__pages",
    )
    parser.add_argument(
        "-o",
        help="Relative path to the folder where the dataset will be saved",
        default="../data/__unclassified",
    )
    parser.add_argument(
        "--classes",
        help="Relative path to the classes JSON file",
        default="../models/classes.json",
    )
    parser.add_argument(
        "--model",
        help="Relative path to the model PTH file",
        default="../models/current_model.pth",
    )
    parser.add_argument(
        "--compute-similarity", help="Computes similarity between contours (SLOW)"
    )

    args = parser.parse_args()

    start = args.start - 1
    end = args.end - 1

    page_range = list(range(start, end + 1))

    # Run contour extraction
    print("Extracting...")

    total = process_pdf(args.infile, page_range, args.pages, args.o)

    print(f"Done. Extracted {total} contours")

    classes = load_classes(args.classes)
    model = load_model(args.model, classes)
    model.eval()

    print("Making predictions...")

    predictions = predict_images(model, classes, args.o)
    print(f"{len(predictions)} predictions created for {args.o}.")

    dataset = create_fo_dataset(predictions)

    print(f"Created dataset {dataset.name}")

    if args.compute_similarity:
        print("Computing similiarity. This could take a while.")
        import fiftyone.brain as fob

        fob.compute_similarity(
            dataset,
            model="clip-vit-base32-torch",
            brain_key="img_sim",
        )

        print("Done computing similiarity.")
