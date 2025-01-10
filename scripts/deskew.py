import cv2
import sys

from show_baselines_and_textlines import show_baselines_and_textlines

sys.path.append("../src")
from util import to_binary, deskew


def correct_skew(img_path, output_path):
    img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)

    import time

    print("starting deskew")
    start = time.time()
    angle, corrected = deskew(img, limit=5, delta=1)
    end = time.time()
    print(f"finished in {end - start} s")

    print(f"skew angle: {angle} deg")

    cv2.imwrite(output_path, corrected)

    show_baselines_and_textlines(output_path, output_path)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please specify an image file path.")
        exit(1)

    filepath = sys.argv[1]

    output_path = "output.png"

    if len(sys.argv) > 3:
        output_path = sys.argv[2]

    correct_skew(filepath, output_path)
