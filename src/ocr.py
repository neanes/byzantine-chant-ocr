import cv2
import numpy as np
import pymupdf
import torch
from PIL import Image
import torch.nn as nn

from model import get_transform
import util
from segmentation import segment
from text_removal import remove_text


class Rect:
    def __init__(self, rect):
        x, y, w, h = rect
        self.x = x
        self.y = y
        self.w = w
        self.h = h


class Circle:
    def __init__(self, circle):
        (x, y), r = circle
        self.x = x
        self.y = y
        self.r = r


class ContourMatch:
    def __init__(self):
        self.bounding_circle = None
        self.bounding_rect = None
        self.test_image = None
        self.label = None
        self.confidence = 0
        self.line = -1
        self.grouped = False

    def to_dict(self):
        return {
            "label": self.label,
            "confidence": self.confidence,
            "bounding_rect": self.bounding_rect,
            "bounding_circle": self.bounding_circle,
            "line": self.line,
            "grouped": self.grouped,
        }


class NeumeGroup:
    def __init__(self):
        self.line = None
        self.base = None
        self.support = []

    def to_dict(self):
        return {
            "line": self.line,
            "base": self.base.to_dict(),
            "support": [x.to_dict() for x in self.support],
        }


class Analysis:
    def __init__(self):
        self.model_version = None
        self.neume_groups = []
        self.segmentation = None
        self.matches = []
        self.image_with_text_removed = None

    def to_dict(self):
        return {
            "model_version": self.model_version,
            "neume_groups": [x.to_dict() for x in self.neume_groups],
            "segmentation": self.segmentation,
        }


def process_pdf(filepath, page_range, model, classes):
    doc = pymupdf.open(filepath)
    pages = []
    for page_num in page_range:
        if page_num < 0 or page_num >= len(doc):
            print(f"Page {page_num} is out of range. Skipping.")
            continue
        page = doc.load_page(page_num)
        pix = page.get_pixmap(dpi=300, colorspace="GRAY")  # High DPI for quality

        # convert to numpy format so opencv can understand it
        image = np.frombuffer(pix.samples, dtype=np.uint8)
        image = image.reshape((pix.height, pix.width, pix.n))

        pages.append(process_image(image, model, classes))

    return pages


def process_image(image, model, classes):
    results = prepare_image(image)

    recognize_contours(results.matches, model, classes)
    results.neume_groups = group_matches(results.matches)

    # TODO store model version in the metadata and read it here
    # results.model_version = _model_data.version

    return results


def prepare_image(image):
    results = Analysis()
    binary = util.to_binary(image)

    results.segmentation = segment(binary)
    results.image_with_text_removed = remove_text(binary, results.segmentation)
    results.matches = prepare_matches_from_contours(results.image_with_text_removed)
    assign_lines_to_matches(results.matches, results.segmentation.baselines)
    sort_matches(results.matches)

    return results


def prepare_matches_from_contours(
    image,
    target_size=224,
    min_contour_width=5,
    max_contour_width=120,
    min_contour_height=5,
    max_contour_height=120,
):
    contours = util.find_contours(image)

    contour_matches = []

    # calculate bounding rectangles and enclosing circles for the contours
    for c in contours:
        match = ContourMatch()

        # calculate bounding rectangles and enclosing circles for the contours
        rect = cv2.boundingRect(c)
        match.bounding_rect = Rect(rect)
        match.bounding_circle = Circle(cv2.minEnclosingCircle(c))

        x, y, w, h = rect

        # If the contour is big enough for us to care about, process it
        if (
            w >= min_contour_width
            and w <= max_contour_width
            and h >= min_contour_height
            and h <= max_contour_height
        ):
            # Crop the region of interest
            roi = image[y : y + h, x : x + w]

            scale = target_size / max(h, w)
            new_w = int(w * scale)
            new_h = int(h * scale)

            if new_w > 0 and new_h > 0:
                resized = cv2.resize(roi, (new_w, new_h), interpolation=cv2.INTER_CUBIC)

                (tH, tW) = resized.shape
                dX = int(max(0, target_size - tW) / 2.0)
                dY = int(max(0, target_size - tH) / 2.0)
                # pad the image and force dimensions
                padded = cv2.copyMakeBorder(
                    resized,
                    top=dY,
                    bottom=dY,
                    left=dX,
                    right=dX,
                    borderType=cv2.BORDER_CONSTANT,
                    value=(0, 0, 0),
                )
                padded = cv2.resize(
                    padded, (target_size, target_size), interpolation=cv2.INTER_CUBIC
                )

                match.test_image = padded

        contour_matches.append(match)

    return contour_matches


def assign_lines_to_matches(matches, baselines):
    if len(baselines) == 0:
        return

    for m in matches:
        m.line = -1

        # First look for a baseline that overlaps the contour
        for i, b in enumerate(baselines):
            # If the baseline is inside the bounding box, we've found the line number
            if m.bounding_rect.y <= b and b <= m.bounding_rect.y + m.bounding_rect.h:
                m.line = i
                break

        # If we assigned a line, move to the next contour
        if m.line != -1:
            continue

        # The neume is between two base lines.
        for i, b in enumerate(baselines):
            # The neume is either part of this baseline or the previous
            if m.bounding_circle.y <= b:
                if i == 0:
                    m.line = i
                    break

                bp = baselines[i - 1]

                # TODO if center is equidistant to each baseline, use entire bounding box
                # to break the tie
                if b - m.bounding_circle.y < m.bounding_circle.y - bp:
                    m.line = i
                    break
                else:
                    m.line = i - 1
                    break

        # If we assigned a line, move to the next contour
        if m.line != -1:
            continue

        # This neume must be part of the last baseline
        if m.bounding_circle.y > baselines[len(baselines) - 1]:
            m.line = len(baselines) - 1


def sort_matches(matches):
    matches.sort(key=lambda p: (p.line, p.bounding_rect.x))


def recognize_contours(matches, model, classes):
    transform = get_transform()

    for m in matches:
        if m.test_image is None or m.test_image.size == 0:
            continue

        img = cv2.cvtColor(m.test_image, cv2.COLOR_GRAY2RGB)
        img = Image.fromarray(img)

        tensor = transform(img).unsqueeze(0)

        with torch.no_grad():
            output = model(tensor)

        probabilities = nn.functional.softmax(output[0], dim=0)
        class_id = torch.argmax(probabilities).item()

        m.label = classes[class_id]
        m.confidence = probabilities[class_id].item()

        # For debugging
        # cv2.namedWindow(m.label, cv2.WINDOW_NORMAL)
        # cv2.imshow(m.label, m.test_image)
        # cv2.waitKey()
        # cv2.destroyAllWindows()


def group_matches(matches, confidence_threshold=0):
    groups = []

    for m in matches:
        if m.label is None or m.grouped or m.confidence < confidence_threshold:
            continue

        # TODO maybe be more careful about multipe bases (e.g. ison + petaste)
        if is_base(m.label):
            g = NeumeGroup()
            g.line = m.line
            g.base = m
            m.grouped = True

            # Find the supporting neumes
            for s in matches:
                # Skip neumes that are too high or that have a low confidence
                # Also skip neumes that were already classified as a base.
                if (
                    s.line < m.line
                    or s.label is None
                    or s.confidence < confidence_threshold
                    or s.grouped
                ):
                    continue

                # Stop if we have reached neumes that are too low
                if s.line > m.line:
                    break

                if (
                    m.bounding_rect.x <= s.bounding_circle.x
                    and s.bounding_circle.x <= (m.bounding_rect.x + m.bounding_rect.w)
                ):
                    g.support.append(s)
                    s.grouped = True

            groups.append(g)

    return groups


def is_base(neume):
    return neume in [
        "ison",
        "oligon",
        "petaste",
        "apostrofos",
        "elafron",
        "vareia",
        "kentima",
    ]
