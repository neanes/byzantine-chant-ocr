import json
from torch.utils.data import DataLoader
from torchvision import transforms, datasets
import torchvision.models as models
import torch
from torch import nn


def test_model(model, test_loader, device):
    model.eval()
    correct = 0
    total = 0
    criterion = nn.CrossEntropyLoss()

    test_loss = 0.0
    with torch.no_grad():  # No gradients needed for testing
        for images, labels in test_loader:
            images, labels = images.to(device), labels.to(device)

            # Forward pass
            outputs = model(images)
            loss = criterion(outputs, labels)
            test_loss += loss.item()

            # Calculate accuracy
            _, predicted = torch.max(outputs, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

    accuracy = 100 * correct / total
    average_loss = test_loss / len(test_loader)

    print(f"Test Accuracy: {accuracy:.2f}%")
    print(f"Average Test Loss: {average_loss:.4f}")
    return accuracy, average_loss


if __name__ == "__main__":
    transform = transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )

    # Load test dataset
    test_dataset = datasets.ImageFolder("data/test", transform=transform)
    test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    with open("models/classes.json") as f:
        classes = json.load(f)

    model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.DEFAULT)
    num_features = model.last_channel  # Get the size of the last layer
    model.classifier[1] = nn.Linear(num_features, len(classes))  # Replace classifier

    model.load_state_dict(torch.load("../models/current_model.pth"))

    model.to(device)

    # Test the model
    test_accuracy, test_loss = test_model(model, test_loader, device)
