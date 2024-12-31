"""
Show Text Regions

This script highlights the regions that are considered to be occupied by text, 
as determined by the OCR engine. Text regions are defined as regions that are
localized around the calculated textlines.

It is used for evaluating and debugging the segmentation logic.

Usage: python show_text_regions.py image.png
"""

import cv2
import sys

sys.path.append("../src")
from segmentation import segment


def show_text_regions(img_path, output_path):
    img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
    binary = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
    segmentation = segment(binary)

    # Read the image in color
    img = cv2.imread(img_path)

    img_width = img.shape[1]

    for line in segmentation.textlines_adj:
        cv2.rectangle(
            img,
            (0, line - segmentation.avg_text_height // 2),
            # (img_width, line + math.ceil(segmentation.avg_text_height * 1.2)),
            (img_width, line + segmentation.avg_text_height // 2),
            (203, 192, 255),
            3,
        )

    cv2.imwrite(output_path, img)

    cv2.namedWindow("img", cv2.WINDOW_GUI_NORMAL)
    cv2.imshow("img", img)
    cv2.waitKey()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please specify an image file path.")
        exit(1)

    filepath = sys.argv[1]

    output_filepath = "output.png"

    if len(sys.argv) > 3:
        output_filepath = sys.argv[2]

    show_text_regions(filepath, output_filepath)
