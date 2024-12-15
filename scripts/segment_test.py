import cv2
import sys

sys.path.append("../src")
from segmentation import segment
from text_removal import remove_text

img_path = "../data/pages/heirmologion_john.pdf_page_6.png"

img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)

binary = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]

segmentation = segment(binary)

print(segmentation)

cv2.namedWindow("with text removed", cv2.WINDOW_NORMAL)
cv2.imshow("with text removed", remove_text(binary, segmentation))
cv2.waitKey()
cv2.destroyAllWindows()
