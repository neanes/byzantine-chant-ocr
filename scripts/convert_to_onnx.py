"""
ONNX conversion

This script converts a PTH model into the ONNX format.
"""

import argparse
import sys

import torch
from torch_model import load_model

sys.path.append("../src")
from model_metadata import load_metadata


def convert_to_onnx(model, onnx_path):
    # Export on CPU: PyTorch CUDA matmul uses TF32 (10-bit mantissa) while ORT
    # CPU uses full fp32, so verify=True would flag spurious ~1e-2 drift on a
    # CUDA-loaded model. The exported .onnx is device-agnostic regardless.
    model = model.cpu()
    model.eval()

    size = 224
    dummy_input = torch.randn(1, 3, size, size)

    onnx_program = torch.onnx.export(
        model,
        (dummy_input,),
        input_names=["input"],
        output_names=["output"],
        # Positional tuple, not a dict: dict keys for dynamic_shapes must match the
        # forward() parameter name ("x" for MobileNetV2), not input_names.
        dynamic_shapes=({0: "batch", 2: "height", 3: "width"},),
        verify=True,
    )
    # input_names/output_names are hints the dynamo exporter may override on conflicts;
    # src/ocr.py hardcodes these strings, so guard the contract.
    assert onnx_program.model.graph.inputs[0].name == "input"
    assert onnx_program.model.graph.outputs[0].name == "output"
    onnx_program.save(onnx_path, external_data=False)


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
        "--meta",
        help="Relative path to the model's metatdata file",
        default="../models/metadata.json",
    )
    args = parser.parse_args()
    metadata = load_metadata(args.meta)
    model = load_model(args.i, metadata.classes)

    convert_to_onnx(model, args.o)
