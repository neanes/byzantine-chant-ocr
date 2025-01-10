import cv2
from pathlib import Path
import sys


def split(img_path, output_path_left, output_path_right):
    img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)

    width = img.shape[1]
    left = img[:, : width // 2]
    right = img[:, width // 2 :]

    cv2.imwrite(output_path_left, left)
    cv2.imwrite(output_path_right, right)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please specify an image file path.")
        exit(1)

    filepath = sys.argv[1]

    output_filepath_left = Path(filepath).stem + ".left.png"
    output_filepath_right = Path(filepath).stem + ".right.png"

    if len(sys.argv) > 3:
        output_filepath_left = sys.argv[2]

    if len(sys.argv) > 4:
        output_filepath_right = sys.argv[3]

    split(filepath, output_filepath_left, output_filepath_right)
