import json
import torch
import torch.nn as nn
from torchvision import models
from torchvision import transforms


def load_model(model_path, classes):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.DEFAULT)
    num_features = model.last_channel  # Get the size of the last layer
    model.classifier[1] = nn.Linear(num_features, len(classes))  # Replace classifier
    model.load_state_dict(torch.load(model_path, weights_only=False))
    model.to(device)
    return model


def load_classes(classes_path):
    with open(classes_path) as f:
        return json.load(f)


def get_transform():
    return transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )
