import cv2
import numpy as np
import pymupdf
import yaml

import util
from model import transform
from segmentation import segment
from text_removal import remove_text


class Rect:
    def __init__(self, rect):
        x, y, w, h = rect
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    def to_dict(self):
        return {
            "x": self.x,
            "y": self.y,
            "w": self.w,
            "h": self.h,
        }


class Circle:
    def __init__(self, circle):
        (x, y), r = circle
        self.x = x
        self.y = y
        self.r = r

    def to_dict(self):
        return {
            "x": self.x,
            "y": self.y,
            "r": self.r,
        }


class ContourMatch:
    def __init__(self):
        self.id = -1
        self.bounding_circle = None
        self.bounding_rect = None
        self.test_image = None
        self.label = None
        self.confidence = 0
        self.line = -1
        self.grouped = False

    def to_dict(self):
        return {
            "id": self.id,
            "label": self.label,
            "confidence": self.confidence,
            "line": self.line,
            "bounding_rect": self.bounding_rect.to_dict(),
            "bounding_circle": self.bounding_circle.to_dict(),
            # "grouped": self.grouped,
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


class PageAnalysis:
    def __init__(self):
        self.id = 0
        self.original_page_num = None
        self.page_area = None
        self.neume_groups = []
        self.segmentation = None
        self.matches = []
        self.image_with_text_removed = None

    def to_dict(self):
        result = {
            "id": self.id,
        }

        if self.original_page_num is not None:
            result["original_page_num"] = self.original_page_num

        if self.page_area is not None:
            result["page_area"] = self.page_area

        result["segmentation"] = self.segmentation.to_dict()
        result["matches"] = [x.to_dict() for x in self.matches]
        # "neume_groups": [x.to_dict() for x in self.neume_groups],

        return result


class Analysis:
    def __init__(self):
        self.model_metadata = None
        self.pages = []

    def to_dict(self):
        return {
            "model_metadata": self.model_metadata.to_dict(),
            "pages": [x.to_dict() for x in self.pages],
        }


class PreprocessOptions:
    def __init__(self):
        self.deskew = True
        self.deskew_max_angle = 5
        self.deskew_initial_delta = 1
        self.despeckle = True
        self.despeckle_kernel_size = 3
        self.close = True
        self.close_kernel_size = 2


def save_analysis(analysis, filepath="output.yaml"):
    with open(filepath, "w") as outfile:
        yaml.safe_dump(
            analysis.to_dict(), outfile, sort_keys=False, default_flow_style=False
        )


def write_analysis_to_stream(analysis):
    stream = yaml.safe_dump(
        analysis.to_dict(), sort_keys=False, default_flow_style=False
    )

    return stream


def process_pdf(
    filepath,
    page_range,
    model,
    metadata,
    preprocess_options=PreprocessOptions(),
    split_lr=False,
):
    analysis = Analysis()
    analysis.model_metadata = metadata

    doc = pymupdf.open(filepath)

    page_index = 0

    for page_num in page_range:
        if page_num < 0 or page_num >= len(doc):
            print(f"Page {page_num} is out of range. Skipping.")
            continue
        page = doc.load_page(page_num)
        pix = page.get_pixmap(dpi=300)  # High DPI for quality

        # convert to numpy format so opencv can understand it
        image = np.frombuffer(pix.samples, dtype=np.uint8)
        image = image.reshape((pix.height, pix.width, pix.n))

        image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

        inner_pages = [image]
        page_areas = []

        if split_lr:
            width = image.shape[1]
            left = image[:, : width // 2]
            right = image[:, width // 2 :]
            inner_pages = [left, right]
            page_areas = ["left", "right"]

        for i, img in enumerate(inner_pages):
            page = prepare_image(img, preprocess_options)
            page.id = page_index
            page.original_page_num = page_num + 1

            if len(page_areas) > 0:
                page.page_area = page_areas[i]

            page_index = page_index + 1

            recognize_contours(page.matches, model, metadata.classes)

            analysis.pages.append(page)

    return analysis


def process_image(
    image, model, metadata, preprocess_options=PreprocessOptions(), split_lr=False
):
    analysis = Analysis()
    analysis.model_metadata = metadata

    inner_pages = [image]
    page_areas = []

    if split_lr:
        width = image.shape[1]
        left = image[:, : width // 2]
        right = image[:, width // 2 :]
        inner_pages = [left, right]
        page_areas = ["left", "right"]

    for i, img in enumerate(inner_pages):
        page = prepare_image(img, preprocess_options)
        page.id = i

        if len(page_areas) > 0:
            page.page_area = page_areas[i]

        recognize_contours(page.matches, model, metadata.classes)

        analysis.pages.append(page)

    return analysis


def preprocess_image(image, preprocess_options=PreprocessOptions()):
    resized = util.downsize(image)

    if preprocess_options.deskew:
        angle, resized = util.deskew(
            resized,
            limit=preprocess_options.deskew_max_angle,
            delta=preprocess_options.deskew_initial_delta,
        )

    binary = util.to_binary(resized)

    if preprocess_options.despeckle:
        binary = cv2.medianBlur(binary, preprocess_options.despeckle_kernel_size)

    if preprocess_options.close:
        kernel = np.ones(
            (
                preprocess_options.close_kernel_size,
                preprocess_options.close_kernel_size,
            ),
            np.uint8,
        )
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

    return binary


def prepare_image(image, preprocess_options):
    page = PageAnalysis()

    binary = preprocess_image(image, preprocess_options)

    page.segmentation = segment(binary)
    page.image_with_text_removed = remove_text(binary, page.segmentation)
    page.matches = prepare_matches_from_contours(
        page.image_with_text_removed,
        max_contour_width=page.segmentation.oligon_width * 1.5,
        max_contour_height=page.segmentation.oligon_width * 1.5,
    )
    assign_lines_to_matches(page.matches, page.segmentation.baselines)
    sort_matches(page.matches)

    for i, m in enumerate(page.matches):
        m.id = i

    return page


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
    for m in matches:
        if m.test_image is None or m.test_image.size == 0:
            continue

        img = cv2.cvtColor(m.test_image, cv2.COLOR_GRAY2RGB)

        img = transform(img)

        output = model.run(["output"], {"input": img.astype(np.float32)})

        probabilities = np.exp(output[0][0]) / np.sum(np.exp(output[0][0]))  # Softmax
        class_id = np.argmax(probabilities)
        confidence = probabilities[class_id].item()

        m.label = classes[class_id]
        m.confidence = confidence

        # For debugging
        # window_name = f"{m.label} ({m.confidence:0.2f})"
        # cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        # cv2.imshow(window_name, m.test_image)
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
