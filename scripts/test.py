"""
Test

This script test the model based on the dataset found in data/dataset.

Usage: python test.py
"""

import json
import sys
from torch.utils.data import DataLoader
import torch
from torch import nn
import torch.nn.functional as F

from ImageFolderWithPaths import ImageFolderWithPaths
from torch_model import get_transform, load_model

sys.path.append("../src")
from model_metadata import load_metadata


class IncorrectPrediction:

    def __init__(self, filepath, actual, predicted, confidence):
        self.filepath = filepath
        self.actual = actual
        self.predicted = predicted
        self.confidence = confidence


def test_model(model, test_loader, device):
    model.eval()
    correct = 0
    total = 0
    criterion = nn.CrossEntropyLoss()

    incorrect_predictions = []

    test_loss = 0.0
    with torch.no_grad():  # No gradients needed for testing
        for images, labels, paths in test_loader:
            images, labels = images.to(device), labels.to(device)

            # Forward pass
            outputs = model(images)
            probabilities = F.softmax(outputs, dim=1)
            loss = criterion(outputs, labels)
            test_loss += loss.item()

            # Calculate accuracy
            _, predicted = torch.max(outputs, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

            incorrect_indices = (predicted != labels).nonzero(as_tuple=True)[0]
            for idx in incorrect_indices:
                incorrect_predictions.append(
                    IncorrectPrediction(
                        paths[idx],
                        labels[idx].item(),
                        predicted[idx].item(),
                        probabilities[idx, predicted[idx]].item(),
                    )
                )

    accuracy = 100 * correct / total
    average_loss = test_loss / len(test_loader)

    return accuracy, average_loss, incorrect_predictions


if __name__ == "__main__":
    metadata = load_metadata("../models/metadata.json")

    # Load test dataset
    full_dataset = ImageFolderWithPaths("../data/dataset", transform=get_transform())

    train_dataset, val_dataset, test_dataset = torch.utils.data.random_split(
        full_dataset,
        [0.7, 0.15, 0.15],
        generator=torch.Generator().manual_seed(255247200),
    )
    test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model = load_model("../models/current_model.pth", metadata.classes)

    model.to(device)

    # Test the model
    test_accuracy, test_loss, incorrect = test_model(model, test_loader, device)

    incorrect_formatted = []

    for p in incorrect:
        incorrect_formatted.append(
            {
                "filepath": p.filepath,
                "actual": metadata.classes[p.actual],
                "predicted": metadata.classes[p.predicted],
                "confidence": p.confidence,
            }
        )

    print(
        json.dumps(
            {
                "incorrect_predictions": incorrect_formatted,
                "acc": test_accuracy,
                "loss": test_loss,
            },
            indent=2,
        )
    )
