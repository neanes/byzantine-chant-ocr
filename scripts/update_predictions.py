import json
import sys
import cv2
from torch.utils.data import DataLoader
from torchvision import transforms, datasets
import torchvision.models as models
import torch
from torch import nn
from PIL import Image


def update_predictions(model, classes, dataset):
    transform = transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )

    model.eval()

    for sample in dataset:
        img_path = sample.filepath
        img = cv2.imread(img_path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(img)

        tensor = transform(img).unsqueeze(0)

        with torch.no_grad():
            output = model(tensor)

        probabilities = nn.functional.softmax(output[0], dim=0)
        class_id = torch.argmax(probabilities).item()

        sample["prediction"] = fo.Classification(
            label=classes[class_id], confidence=probabilities[class_id]
        )
        sample.save()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please specify the name of the dataset.")
        exit(1)

    dataset_name = sys.argv[1]

    print("Loading FiftyOne...")
    import fiftyone as fo

    print("Loading dataset...")
    dataset = fo.load_dataset(dataset_name)
    print("Adding files...")

    print("Loading model...")
    # Load the model
    with open("../models/classes.json") as f:
        classes = json.load(f)

    model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.DEFAULT)
    num_features = model.last_channel  # Get the size of the last layer
    model.classifier[1] = nn.Linear(num_features, len(classes))  # Replace classifier
    model.load_state_dict(torch.load("../models/current_model.pth"))

    print("Updating dataset...")
    update_predictions(model, classes, dataset)
    print("Done.")
