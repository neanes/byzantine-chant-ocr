import cv2
import sys

sys.path.append("../src")
import util


def show_median_blur(img_path, output_path):
    img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
    resized = util.downsize(img)
    binary = util.to_binary(resized)
    blurred = cv2.medianBlur(binary, 3)

    cv2.imwrite(output_path, blurred)

    cv2.namedWindow("img", cv2.WINDOW_GUI_NORMAL)
    cv2.imshow("img", blurred)
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

    show_median_blur(filepath, output_filepath)
