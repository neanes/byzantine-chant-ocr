import argparse
import sys
import torch
import torch.nn as nn
import torchvision.models as models

sys.path.append("../src")
from model import load_classes, load_model


def convert_to_onnx(model, onnx_path):
    model.eval()

    size = 224
    dummy_input = torch.randn(1, 3, size, size)

    torch.onnx.export(
        model,
        dummy_input,
        onnx_path,
        export_params=True,  # Store the trained parameters in the model file
        opset_version=11,  # ONNX version to use (11 is commonly supported)
        input_names=["input"],  # Name of input layer(s)
        output_names=["output"],  # Name of output layer(s)
        dynamic_axes={
            "input": {0: "batch_size", 2: "height", 3: "width"},
        },
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Converts a PTH model to the ONNX format"
    )

    parser.add_argument(
        "-i",
        help="Relative path to the PTH model file",
        default="../models/current_model.pth",
    )

    parser.add_argument(
        "-o",
        help="Relative path to the output file",
        default="../models/current_model.onnx",
    )

    parser.add_argument(
        "--classes",
        help="Relative path to the classes.json file",
        default="../models/classes.json",
    )
    args = parser.parse_args()
    classes = load_classes(args.classes)
    model = load_model(args.i, classes)

    convert_to_onnx(model, args.o)
