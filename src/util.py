import cv2
import imutils
import math
import numpy as np
from scipy.ndimage import interpolation as inter


def to_binary(image):
    return cv2.threshold(image, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]


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
    Returns a binary representation of the image with thin contours removed. Contours height <= cutoff are removed.
    """
    return apply_mask(binary_image, lambda x, y, w, h: h <= cutoff)


def mask_wide_contours(binary_image, cutoff):
    """
    Returns a binary representation of the image with thin contours removed. Contours width >= cutoff are removed.
    """
    return apply_mask(binary_image, lambda x, y, w, h: w >= cutoff)


def mask_narrow_contours(binary_image, cutoff_ratio):
    """
    Returns a binary representation of the image with narrow contours removed. Contours with width/height <= cutoff_ratio are removed.
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


def find_skew_angles(binary_image, lower_limit, upper_limit, delta):
    def determine_score(arr, angle):
        data = inter.rotate(arr, angle, reshape=False, order=0)
        histogram = np.sum(data, axis=1, dtype=float)
        score = np.sum((histogram[1:] - histogram[:-1]) ** 2, dtype=float)
        return score

    scores = []
    angles = np.arange(-lower_limit, upper_limit + delta, delta)
    for angle in angles:
        score = determine_score(binary_image, angle)
        scores.append(score)

    angle_score_pairs = sorted(zip(scores, angles), reverse=True, key=lambda x: x[0])

    sorted_scores, sorted_angles = zip(*angle_score_pairs)

    return sorted_angles


invphi = (math.sqrt(5) - 1) / 2  # 1 / phi


def gss_max(f, a, b, tolerance=1e-5):
    while b - a > tolerance:
        c = b - (b - a) * invphi
        d = a + (b - a) * invphi
        if f(c) > f(d):
            b = d
        else:
            a = c

    return (b + a) / 2


def deskew(img, limit, delta):
    binary_image = to_binary(img)

    sorted_angles = find_skew_angles(binary_image, limit, limit, delta)

    upper_limit = max(sorted_angles[:3])
    lower_limit = min(sorted_angles[:3])

    def determine_score(angle):
        data = inter.rotate(binary_image, angle, reshape=False, order=0)
        histogram = np.sum(data, axis=1, dtype=float)
        score = np.sum((histogram[1:] - histogram[:-1]) ** 2, dtype=float)
        return score

    best_angle = gss_max(determine_score, lower_limit, upper_limit, 0.1)

    (h, w) = binary_image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, best_angle, 1.0)
    corrected = cv2.warpAffine(
        img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
    )

    return best_angle, corrected
