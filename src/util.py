import cv2
import imutils


def find_contours(image):
    blurred = cv2.GaussianBlur(image, (5, 5), 0)
    edged = cv2.Canny(blurred, 30, 150)
    contours = cv2.findContours(
        edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    contours = imutils.grab_contours(contours)

    return contours


def apply_mask(image, condition):
    copy = image.copy()
    contours = find_contours(copy)

    for c in contours:
        x, y, w, h = cv2.boundingRect(c)

        if condition(x, y, w, h):
            # Mask the contour by drawing a filled rectangle over it
            cv2.rectangle(copy, (x, y), (x + w, y + h), (0, 0, 0), cv2.FILLED)

    return copy


def mask_thin_contours(binary_image, cutoff):
    """
    Returns a binary representation of the image with thin contours removed. Contours height < cutoff are removed.
    """
    return apply_mask(binary_image, lambda x, y, w, h: h <= cutoff)


def mask_narrow_contours(binary_image, cutoff_ratio):
    """
    Returns a binary representation of the image with narrow contours removed. Contours with width/height < cutoff_ratio are removed.
    """
    return apply_mask(binary_image, lambda x, y, w, h: w / h <= cutoff_ratio)


def vertical_runs(image, color):
    runs = list()

    current_run = 0

    rows, cols = image.shape

    for col in range(cols):
        for row in range(rows):
            if image[row, col] == color:
                current_run = current_run + 1
            elif current_run != 0:
                runs.append(current_run)
                current_run = 0

        if current_run != 0:
            runs.append(current_run)
            current_run = 0

    return runs


def pixels_in_row(binary_image):
    pixels_in_row = list()

    rows, _ = binary_image.shape

    for r in range(rows):
        pixels_in_row.append(cv2.countNonZero(binary_image[r, :]))

    return pixels_in_row
