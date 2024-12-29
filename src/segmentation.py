"""
Segmentation

This script contains utilities for detecting baselines, textlines
and other dimensional properties in scanned documents using OpenCV 
and mathematical tools.
"""

import cv2
import numpy as np
import math
from scipy import signal, stats

import util


class Segmentation:
    """
    Contains segmentation information for a single page of a scanned document
    """

    def __init__(self):
        self.oligon_height = None
        self.oligon_width = None
        self.avg_text_height = None
        self.avg_baseline_gap = None
        self.baselines = None
        self.textlines = None
        self.textlines_adj = None
        self.page_height = None
        self.page_width = None

    def __str__(self):
        return f"""oligon: ({self.oligon_width},{self.oligon_height})
avg_text_height: {self.avg_text_height}
avg_baseline_gap: {self.avg_baseline_gap}
baselines: {self.baselines}
textlines: {self.textlines}
textlines_adj: {self.textlines_adj}
"""

    def to_dict(self):
        return {
            "page_width": self.page_width,
            "page_height": self.page_height,
            "oligon_width": self.oligon_width,
            "oligon_height": self.oligon_height,
            "avg_text_height": self.avg_text_height,
            "avg_baseline_gap": self.avg_baseline_gap,
            "baselines": self.baselines,
            "textlines": self.textlines,
            "textlines_adj": self.textlines_adj,
        }


def segment(binary_image):
    """
    Segments an image

    Parameters
    ----------
    binary_image: MatLike
        The image to segment. Must be binary.

    Returns
    -------
    Segmentation
        The segmentation information
    """
    result = Segmentation()

    result.page_height = binary_image.shape[0]
    result.page_width = binary_image.shape[1]

    wide_contours = find_wide_contours(binary_image)

    result.oligon_height = find_oligon_height(binary_image, wide_contours)

    result.oligon_width = find_oligon_width(wide_contours, result.oligon_height)

    find_baselines(binary_image, result)

    # Re-estimate the oligon height and width using only contours that
    # 1) touch the baseline
    # 2) are less than 3 times the current estimated oligon width
    def wide_contour_filter(wide_contour, baselines):
        x, y, w, h = cv2.boundingRect(wide_contour)
        return (
            any(y <= line and line <= y + h for line in baselines)
            and w <= 3 * result.oligon_width
        )

    wide_contours = [
        wide_contour
        for wide_contour in wide_contours
        if wide_contour_filter(wide_contour, result.baselines)
    ]

    result.oligon_height = find_oligon_height(binary_image, wide_contours)
    result.oligon_width = find_oligon_width(wide_contours, result.oligon_height)

    find_textlines(binary_image, result)
    find_adjusted_textlines(binary_image, result)

    result.avg_text_height = find_average_text_height(binary_image, result.textlines)

    return result


def find_wide_contours(binary_image, cutoff_ratio=3.0):
    """
    Finds contours in a binary image that satisfy width/height >= cutoff_ratio.

    Parameters
    ----------
    binary_image: MatLike
        The image to search. Must be binary.

    cutoff_ratio: float
        The cutoff ratio to use

    Returns
    -------
    list
        A list of wide contours
    """
    contours = util.find_contours(binary_image)

    wide_contours = list()

    for c in contours:
        x, y, w, h = cv2.boundingRect(c)

        if w / h >= cutoff_ratio:
            wide_contours.append(c)

    return wide_contours


def find_oligon_height(binary_image, wide_contours):
    """
    Estimates the oligon height by finding the most frequent vertical run of ink among all wide contours

    Parameters
    ----------
    binary_image: MatLike
        The image to search. Must be binary.

    wide_contours: list
        The list of wide countors

    Returns
    -------
    int
        The estimated height of the oligon
    """
    heights = list()

    for c in wide_contours:
        x, y, w, h = cv2.boundingRect(c)

        roi = binary_image[y : y + h, x : x + w]

        runs = util.vertical_runs(roi, 255)

        heights.extend(runs)

    if len(heights) == 0:
        return 0

    return stats.mode(heights)[0].item()


def find_oligon_width(wide_contours, oligon_height):
    """
    Estimates the oligon width by finding the median width among all wide contours that are of similar height to the calculated `oligon_height`
    Parameters
    ----------
    binary_image: MatLike
        The image to search. Must be binary.

    wide_contours: list
        The list of wide countors

    oligon_height: int
        The estimated height of the oligon

    Returns
    -------
    int
        The estimated width of the oligon
    """
    widths = list()

    for c in wide_contours:
        x, y, w, h = cv2.boundingRect(c)

        if oligon_height <= h and h <= math.ceil(oligon_height * 1.5):
            widths.append(w)

    if len(widths) == 0:
        return 0

    return int(np.median(widths))


def find_average_text_height(image, textlines):
    """
    Finds the average height of all contours that touch textlines
    """
    contours = util.find_contours(image)

    heights = list()

    # Find the height of each contour that touches a textline
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)

        if any(y <= line and line <= y + h for line in textlines):
            heights.append(h)

    # Find the average height
    return int(np.median(heights))


def find_baselines(
    binary_image, segmentation, narrow_contour_cutoff=2.0, min_contour_height=5
):
    masked = util.mask_narrow_contours(binary_image, narrow_contour_cutoff)
    masked = util.mask_thin_contours(masked, min_contour_height)
    masked = util.mask_wide_contours(masked, segmentation.oligon_width * 10)

    oligon_width = segmentation.oligon_width

    # Find the number of pixels in each row.
    pixels_in_row = util.pixels_in_row(masked)

    # Find the local maxima where the number of pixels is greater than 0.8 * oligon_width
    lines, _ = signal.find_peaks(
        pixels_in_row,
        height=0.8 * oligon_width,
        distance=oligon_width - 1,
    )

    lines = lines.tolist()

    # Calculate the average distance between baselines
    distances = list()

    for i in range(len(lines) - 1):
        distances.append(lines[i + 1] - lines[i])

    avg_distance = (
        int(np.median(distances)) if len(distances) != 0 else oligon_width * 2
    )
    segmentation.avg_baseline_gap = avg_distance

    # Next, search for any baselines that we may have missed
    missed_lines = list()

    for i in range(len(lines)):
        height = binary_image.shape[0]
        distance = height - lines[i] if i == len(lines) - 1 else lines[i + 1] - lines[i]

        if distance > 1.5 * avg_distance:
            start = max(
                lines[i] + avg_distance - oligon_width * 3 // 4,
                lines[i] + oligon_width // 2,
            )

            end = min(
                lines[i] + avg_distance + oligon_width * 3 // 4,
                height - oligon_width // 2,
            )

            peaks, _ = signal.find_peaks(
                pixels_in_row[start:end],
                height=0.4 * oligon_width,
                distance=oligon_width // 2,
            )

            peaks = peaks + start

            missed_lines.extend(peaks.tolist())

    if missed_lines:
        lines.extend(missed_lines)

        # Sort the lines vector since it may have had new lines
        # added to it at the end out of order
        lines.sort()

    # Remove lines that are too close together.
    pruned = list()

    last = -oligon_width

    for y in lines:
        # If this line is within oligon_width of the previous
        # ignore it.
        if y - last > oligon_width:
            pruned.append(y)
            last = y

    segmentation.baselines = pruned


def find_textlines(binary_image, segmentation, min_contour_height=5):
    """
    Finds texts textlines by finding the rows with the most black pixels that appear between baselines
    """
    textlines = list()

    height = binary_image.shape[0]

    oligon_width = segmentation.oligon_width
    baselines = segmentation.baselines
    avg_baseline_gap = segmentation.avg_baseline_gap

    # Mask thin contour so that we don't detect melismatic underscores as textlines.
    # We want the textline to run through the letters, not the melismas.
    masked = util.mask_thin_contours(binary_image, min_contour_height)
    masked = util.mask_wide_contours(masked, segmentation.oligon_width * 10)

    # Find the number of pixels in each row.
    pixels_in_row = util.pixels_in_row(masked)

    # Find the local maxima between each baseline
    for i in range(len(baselines)):
        baseline = baselines[i]

        # Search between [first baseline + oligon_width / 2, second baseline - oligon_width / 2]
        start = baseline + oligon_width // 2

        # For the last baseline, search to the end of the page
        if i == len(baselines) - 1:
            end = height
            gap = height - baseline
        else:
            next_baseline = baselines[i + 1]
            end = next_baseline - oligon_width // 2
            gap = next_baseline - baseline

        # If the gap is larger than usual, the narrow the search to
        # [first baseline + oligon_width / 2, baseline - avg_baseline_gap - oligon_width]
        # TODO should this actually be baseline - avg_baseline_gap - oligon_width / 2?
        if gap > 1.5 * avg_baseline_gap:
            end = baseline + avg_baseline_gap - oligon_width

        # Find the maxima between between the baselines

        if end - start > 0:
            maxima, _ = signal.find_peaks(
                pixels_in_row[start:end],
                height=1,
                distance=end - start,
            )

            maxima = maxima + start

            # We should only find one maximum
            if maxima.any():
                textlines.append(maxima.tolist()[0])

    # Find textlines before the first baselines. These could be titles, mode keys, etc
    if baselines:
        end = max(0, baselines[0] - oligon_width)

        maxima, _ = signal.find_peaks(
            pixels_in_row[0:end],
            height=oligon_width / 2,
            distance=oligon_width / 2,
        )

        if maxima.any():
            textlines.extend(maxima.tolist())
            textlines.sort()

    segmentation.textlines = textlines


def find_adjusted_textlines(image, segmentation):
    contours = util.find_contours(image)

    textlines_adj = []
    for line in segmentation.textlines:
        midpoints = []
        for c in contours:
            rect = cv2.boundingRect(c)
            x, y, w, h = rect

            if y <= line and line <= y + h:
                midpoints.append(y + h / 2)

        if len(midpoints) > 0:
            textlines_adj.append(int(np.median(midpoints)))

    segmentation.textlines_adj = textlines_adj
