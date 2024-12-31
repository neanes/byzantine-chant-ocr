"""
Outline

This script draws a rectangle on an image. It is useful when you have a contour in a dataset but 
you are not sure exactly what it is. You can use the rectangle information encoded in the file name
to outline the contour on the page.

Usage: python outline.py image.png x y w h

(x,y): the upper left corner of the rectangle
(w,h): the width and height of the rectangle.
"""

import cv2
import sys


def show_all_contours(img_path, output_path, x, y, w, h):
    img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)

    # Read the image in color
    img = cv2.imread(img_path)

    cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 255), 3)

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

    x = int(sys.argv[2])
    y = int(sys.argv[3])
    w = int(sys.argv[4])
    h = int(sys.argv[5])

    output_filepath = "output.png"

    if len(sys.argv) > 6:
        output_filepath = sys.argv[6]

    show_all_contours(filepath, output_filepath, x, y, w, h)
