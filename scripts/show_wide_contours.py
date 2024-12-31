"""
Show Wide Contours

This script highlights the contours that are considered by the OCR engine to be "wide".

It is used for evaluating and debugging the segmentation logic.

Usage: python show_wide_contours.py image.png
"""

import cv2
import sys

sys.path.append("../src")
from segmentation import segment, find_wide_contours


def show_wide_contours(img_path, output_path):
    img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
    binary = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
    segmentation = segment(binary)
    contours = find_wide_contours(binary)

    # Read the image in color
    img = cv2.imread(img_path)

    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        cv2.rectangle(img, (x, y), (x + w, y + h), (203, 192, 255), 3)

    cv2.imwrite(output_path, img)

    print(segmentation)

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

    show_wide_contours(filepath, output_filepath)
