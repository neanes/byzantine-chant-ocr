import torch
from torchvision import models
from torchvision import transforms


def load_model(model_path, classes):
    model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.DEFAULT)
    num_features = model.last_channel  # Get the size of the last layer
    model.classifier[1] = torch.nn.Linear(
        num_features, len(classes)
    )  # Replace classifier
    model.load_state_dict(torch.load(model_path, weights_only=False))
    model.to(torch.device("cuda" if torch.cuda.is_available() else "cpu"))
    return model


def get_transform():
    return transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )
