import numpy as np
import onnxruntime as ort


def load_onnx_model(model_path):
    return ort.InferenceSession(model_path)


def transform(img):
    transformed = img.copy()
    transformed = transformed / 255.0  # Normalize to [0, 1]
    transformed = (transformed - np.array([0.485, 0.456, 0.406])) / np.array(
        [0.229, 0.224, 0.225]
    )  # Apply mean/std

    # Rearrange the dimensions to (channels, height, width)
    transformed = np.transpose(transformed, (2, 0, 1))  # Convert HWC to CHW

    # Add the batch dimension (1, channels, height, width)
    transformed = np.expand_dims(transformed, axis=0)

    return transformed
