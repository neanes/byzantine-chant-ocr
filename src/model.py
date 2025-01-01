import json
import onnxruntime as ort
from torchvision import models
from torchvision import transforms


def load_onnx_model(model_path):
    return ort.InferenceSession(model_path)


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
