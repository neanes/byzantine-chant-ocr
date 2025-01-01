"""
Predict Image

This script runs a single image through the model and outputs the predicted label and confidence.

Usage: python predict_image.py image.png
"""

import argparse
import cv2
import json
import sys
import torch
import torch.nn as nn
from PIL import Image

from torch_model import load_model

sys.path.append("../src")
from model import load_classes, get_transform


def predict_image(model, classes, img_path):
    transform = get_transform()

    model.eval()

    img = cv2.imread(img_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(img)

    tensor = transform(img).unsqueeze(0)

    with torch.no_grad():
        output = model(tensor)

    probabilities = nn.functional.softmax(output[0], dim=0)
    class_id = torch.argmax(probabilities).item()
    confidence = probabilities[class_id].item()

    return {
        "filepath": img_path,
        "prediction": classes[class_id],
        "confidence": confidence,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Creates makes a prediction for a single image"
    )
    parser.add_argument("infile", help="Relative path to the image file")

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

    args = parser.parse_args()

    classes = load_classes(args.classes)
    model = load_model(args.model, classes)
    model.eval()

    prediction = predict_image(model, classes, args.infile)
    print(json.dumps(prediction, indent=2))
