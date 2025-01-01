"""
Do OCR

This is the main script. 

Usage: python do_ocr.py infile start end

infile: The PDF or image file to analyze.
start: The first page of the PDF to process.
end: The last page of the PDF to process.
"""

import cv2
import sys
import yaml

sys.path.append("../src")
from model import load_metadata, load_onnx_model
from ocr import process_image, process_pdf

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please specify the file path")
        exit(1)

    filepath = sys.argv[1]

    metadata = load_metadata("../models/metadata.json")
    model = load_onnx_model("../models/current_model.onnx")

    if filepath.endswith(".pdf"):
        start = int(sys.argv[2]) - 1
        end = int(sys.argv[3]) - 1 if len(sys.argv) >= 4 else start

        page_range = range(start, end + 1)

        results = process_pdf(filepath, page_range, model, metadata)
    else:
        image = cv2.imread(filepath, cv2.IMREAD_GRAYSCALE)
        results = process_image(image, model, metadata)

    with open("output.yaml", "w") as outfile:
        yaml.safe_dump(
            results.to_dict(), outfile, sort_keys=False, default_flow_style=False
        )
