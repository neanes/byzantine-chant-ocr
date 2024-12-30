import cv2
import numpy as np
import sys

sys.path.append("../src")
from segmentation import segment
from text_removal import remove_text
from util import find_contours


def transform(img, segmentation):
    contours = find_contours(img)

    _, contours = filter(contours, img, segmentation)

    # Find contours that are slanted up to the right
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 0), cv2.FILLED)

    return img


def filter(contours, img, segmentation):
    passed = []
    failed = []

    for c in contours:
        x, y, w, h = cv2.boundingRect(c)

        # Filter out contours that touch the baseline
        if any(y <= line and line <= y + h for line in segmentation.baselines):
            failed.append(c)
            continue

        # Filter out contours that are not very rectangular
        if w / h >= 1.2 or w / h <= 0.8:
            failed.append(c)
            continue

        # Filter out contours that have pixels in the center
        moments = cv2.moments(c)

        if moments["m00"] != 0:
            # Calculate centroid
            cX = int(moments["m10"] / moments["m00"])
            cY = int(moments["m01"] / moments["m00"])

            # Get the pixel color at the centroid
            color = img[cY, cX]  # Note: OpenCV uses (row, column) indexing

            if color != 0:
                failed.append(c)
                continue

        passed.append(c)

    return passed, failed


def show_ypsili(img_path, output_path):
    img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
    img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
    segmentation = segment(img)

    img = remove_text(img, segmentation)
    img = transform(img, segmentation)

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

    show_ypsili(filepath, output_filepath)
