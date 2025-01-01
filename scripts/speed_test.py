import argparse
import cv2
import os
import sys
import torch
import torch.nn as nn
from PIL import Image
from torch.utils.data import DataLoader, Dataset

from torch_model import load_model

sys.path.append("../src")
from model import load_classes, get_transform
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


def predict_images(model, classes, image_folder, num_workers=0):
    dataset = ImageDataset(image_folder, get_transform())
    data_loader = DataLoader(
        dataset, batch_size=16, shuffle=False, num_workers=num_workers
    )

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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Used to find the optimal arguments to the dataloader"
    )
    parser.add_argument(
        "--num-workers", help="The number of workers to use", type=int, default=0
    )
    args = parser.parse_args()
    classes = load_classes("../models/classes.json")
    model = load_model("../models/current_model.pth", classes)
    model.eval()

    print("Making predictions...")

    predictions = predict_images(
        model, classes, "../data/__unclassified", num_workers=args.num_workers
    )
    print(f"{len(predictions)} predictions created for ../data/__unclassified.")
