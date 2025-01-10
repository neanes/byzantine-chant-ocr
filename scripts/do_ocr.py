"""
Do OCR

This is the main script. 

Usage: python do_ocr.py infile start end

infile: The PDF or image file to analyze.
start: The first page of the PDF to process.
end: The last page of the PDF to process.
"""

import argparse
import cv2
import sys
import yaml

sys.path.append("../src")
from model_metadata import load_metadata
from model import load_onnx_model
from ocr import process_image, process_pdf

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Performs OCR on an image or PDF")

    parser.add_argument("filepath")
    parser.add_argument("start", type=int, nargs="?", default=-1)
    parser.add_argument("end", type=int, nargs="?", default=-1)

    parser.add_argument(
        "-o",
        help="Relative path to the output file",
        default="output.yaml",
    )

    parser.add_argument(
        "--stdout",
        help="Print to stdout instead of to a file",
        action="store_true",
    )

    parser.add_argument(
        "--split-lr",
        help="Use this flag if each PDF page contains two side-by-side pages",
        action="store_true",
    )

    args = parser.parse_args()

    metadata = load_metadata("../models/metadata.json")
    model = load_onnx_model("../models/current_model.onnx")

    if args.filepath.endswith(".pdf"):
        if args.start == -1:
            print("Please provide a page number")
            exit()

        start = args.start - 1
        end = args.end - 1 if args.end != -1 else start

        page_range = range(start, end + 1)

        results = process_pdf(args.filepath, page_range, model, metadata, args.split_lr)
    else:
        image = cv2.imread(args.filepath, cv2.IMREAD_GRAYSCALE)
        results = process_image(image, model, metadata, args.split_lr)

    if args.stdout:
        stream = yaml.safe_dump(
            results.to_dict(), sort_keys=False, default_flow_style=False
        )
        print(
            stream,
            flush=True,
        )
    else:
        with open(args.o, "w") as outfile:
            yaml.safe_dump(
                results.to_dict(), outfile, sort_keys=False, default_flow_style=False
            )
