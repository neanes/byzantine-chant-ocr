import cv2
import sys

sys.path.append("../src")
from segmentation import segment
from text_removal import remove_text
from util import find_contours


def find_closest_baseline(c, baselines):
    (cx, cy), r = cv2.minEnclosingCircle(c)
    for i, b in enumerate(baselines):
        # The neume is either part of this baseline or the previous
        if cy <= b:
            if i == 0:
                return b

            bp = baselines[i - 1]

            # TODO if center is equidistant to each baseline, use entire bounding box
            # to break the tie
            if b - cy < cy - bp:
                return b
            else:
                return bp

    # This neume must be part of the last baseline
    if cy > baselines[len(baselines) - 1]:
        return baselines[len(baselines) - 1]


def transform(img, segmentation):
    contours = find_contours(img)

    _, contours = filter(contours, img, segmentation)

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

        # We only want neumes below the baseline
        if y < find_closest_baseline(c, segmentation.baselines):
            failed.append(c)
            continue

        if h <= segmentation.oligon_height * 2:
            failed.append(c)
            continue

        if w < segmentation.oligon_width * 0.5 or h > 35:
            failed.append(c)
            continue

        moments = cv2.moments(c)

        if moments["m00"] != 0:
            # Calculate centroid
            cX = int(moments["m10"] / moments["m00"])
            cY = int(moments["m01"] / moments["m00"])

            # Get the pixel color at the centroid
            color = img[cY, cX]  # Note: OpenCV uses (row, column) indexing

            if color == 0:
                failed.append(c)
                continue

        passed.append(c)

    return passed, failed


def show(img_path, output_path):
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

    show(filepath, output_filepath)
