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
from ocr import PreprocessOptions, process_image, process_pdf

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

    parser.add_argument(
        "--deskew",
        help="Use this flag if the image is significantly skewed",
        action="store_true",
    )

    parser.add_argument(
        "--deskew-max-angle",
        help="The maximum tilt angle to consider when attempting to deskew. The larger this angle, the slower the deskewing process will be.",
        type=int,
    )

    parser.add_argument(
        "--despeckle",
        help="Use this flag if the image contains a lot of salt-and-pepper noise. Performs a median blur.",
        action="store_true",
    )

    parser.add_argument(
        "--despeckle-ksize",
        help="The kernel size for despeckling. E.g. 3 indicates a 3x3 kernel.",
        type=int,
    )

    parser.add_argument(
        "--close",
        help="Use this flag if the neumes contain a lot of small gaps. Performs a morphological closing transformation.",
        action="store_true",
    )

    parser.add_argument(
        "--close-ksize",
        help="The kernel size for morphological closing. E.g. 3 indicates a 3x3 kernel.",
        type=int,
    )

    args = parser.parse_args()

    metadata = load_metadata("../models/metadata.json")
    model = load_onnx_model("../models/current_model.onnx")

    preprocess_options = PreprocessOptions()

    preprocess_options.deskew = args.deskew
    preprocess_options.despeckle = args.despeckle
    preprocess_options.close = args.close

    if args.despeckle_ksize:
        preprocess_options.despeckle_kernel_size = args.despeckle_ksize

    if args.close_ksize:
        preprocess_options.close_kernel_size = args.close_ksize

    if args.deskew_max_angle:
        preprocess_options.deskew_max_angle = args.deskew_max_angle

    if args.filepath.endswith(".pdf"):
        if args.start == -1:
            print("Please provide a page number")
            exit()

        start = args.start - 1
        end = args.end - 1 if args.end != -1 else start

        page_range = range(start, end + 1)

        results = process_pdf(
            args.filepath,
            page_range,
            model,
            metadata,
            preprocess_options=preprocess_options,
            split_lr=args.split_lr,
        )
    else:
        image = cv2.imread(args.filepath, cv2.IMREAD_GRAYSCALE)
        results = process_image(
            image,
            model,
            metadata,
            preprocess_options=preprocess_options,
            split_lr=args.split_lr,
        )

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
