import cv2
import sys

sys.path.append("../src")
import util


def go(img_path, output_path):
    img = cv2.imread(img_path)
    resized = util.downsize(img)

    cv2.imwrite(output_path, resized)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please specify an image file path.")
        exit(1)

    filepath = sys.argv[1]

    output_filepath = "output.png"

    if len(sys.argv) > 3:
        output_filepath = sys.argv[2]

    go(filepath, output_filepath)
