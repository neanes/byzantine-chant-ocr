import cv2
import sys

sys.path.append("../src")
from segmentation import segment
from text_removal import remove_text


def test_segmentation(img_path, output_path):
    img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)

    binary = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]

    segmentation = segment(binary)

    print(segmentation)

    no_text = remove_text(binary, segmentation)
    cv2.imwrite(output_path, no_text)

    cv2.namedWindow("with text removed", cv2.WINDOW_NORMAL)
    cv2.imshow("with text removed", no_text)
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

    test_segmentation(filepath, output_filepath)
