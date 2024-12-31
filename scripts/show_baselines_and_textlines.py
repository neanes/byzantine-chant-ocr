"""
Show Baselines and Textlines

This script draws an overlay of the baselines and textlines calculated by the OCR engine. 

It is used for evaluating and debugging the segmentation logic.

Usage: python show_baselines_and_textlines.py image.png
"""

import cv2
import sys

sys.path.append("../src")
from segmentation import segment


def show_baselines_and_textlines(img_path, output_path):
    img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
    binary = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
    segmentation = segment(binary)

    img_width = img.shape[1]

    # Read the image in color
    img = cv2.imread(img_path)

    for baseline in segmentation.baselines:
        cv2.line(img, (0, baseline), (img_width, baseline), (230, 216, 173), 3)

    for textline in segmentation.textlines_adj:
        cv2.line(img, (0, textline), (img_width, textline), (203, 192, 255), 3)

    print(segmentation)

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

    show_baselines_and_textlines(filepath, output_filepath)
