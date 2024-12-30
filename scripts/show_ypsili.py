import cv2
import numpy as np
import sys

sys.path.append("../src")
from segmentation import segment
from text_removal import remove_text
from util import apply_mask, find_contours


def transform(img, segmentation):
    # remove all contours that touch the baseline or that are not taller than wide
    img = apply_mask(
        img,
        lambda x, y, w, h: w * 0.8 > h
        or any(y <= line and line <= y + h for line in segmentation.baselines),
    )

    contours = find_contours(img)

    # only keep the tallest contours
    heights = []

    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        heights.append(h)

    heights.sort()

    p = np.percentile(heights, 90)

    img = apply_mask(img, lambda x, y, w, h: h < p)

    # Find contours that are slanted up to the right
    for c in contours:
        rect = cv2.minAreaRect(c)
        _, (width, height), angle = rect

        if not 30 <= angle <= 70:
            x, y, w, h = cv2.boundingRect(c)
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 0), cv2.FILLED)

    return img


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
