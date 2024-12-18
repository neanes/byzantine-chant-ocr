import cv2

import util


def find_text_contours(image, segmentation, min_contour_height=5):
    contours = util.find_contours(image)

    text_contours = list()

    baseline_rects = list()

    # Find the bounding rectangles for each contour that overlaps a baseline
    for c in contours:
        rect = cv2.boundingRect(c)
        x, y, w, h = rect

        if any(y <= line and line <= y + h for line in segmentation.baselines):
            baseline_rects.append(rect)

    # Preserve contours that may be martyria, agogi,
    # or neumes that dip into the text line
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)

        textline = -1

        # Find contours that touch the textline +- avg_height / 2
        for line in segmentation.textlines_adj:
            top = max(y, line - segmentation.avg_text_height / 2)
            bottom = min(y + h, line + segmentation.avg_text_height / 2)

            if bottom - top > 0:
                textline = y
                break

            # if (
            #     line - segmentation.avg_text_height / 2 <= y
            #     and y <= line + segmentation.avg_text_height
            #     and w > h
            # ):
            #     textline = y
            #     break

        # If the contour doesn't touch the textline, skip it
        if textline == -1:
            continue

        # If the textline is before the first baseline, then this is a heading
        # and should be removed. That is, it's a title or mode key signature, etc.
        if textline < segmentation.baselines[0]:
            text_contours.append(c)
            continue

        # Check for neumes that are more than twice as wide as they are tall.
        # These may be neumes that happen to extend down to the textline.
        # But if the neume is thin, it may be a hyphen or a melisma, so
        # we remove it.
        if w / h > 2.2 and h > min_contour_height:
            continue

        # If the contour extends high enough above the textline,
        # it's probably a martyria, agogi or neume
        if y + h - textline > 1.5 * segmentation.avg_text_height:
            continue

        # If there is no contour on the baseline above the contour,
        # it might be a martyria

        # Find the baseline above the textline
        baseline = 0

        for line in segmentation.baselines:
            if line > textline:
                break

            baseline = y

        # Search for contours above the baseline
        found_contour_on_baseline = False

        for (
            baseline_rect_x,
            baseline_rect_y,
            baseline_rect_w,
            baseline_rect_h,
        ) in baseline_rects:
            # If the contour touches this baseline...
            if (
                baseline_rect_y <= baseline
                and baseline <= baseline_rect_y + baseline_rect_h
            ):
                # ...and the baseline contour is mostly above the textline contour.
                left = max(baseline_rect_x + baseline_rect_w / 4, x)
                right = min(baseline_rect_x + baseline_rect_w * 3 / 4, (x + w))

                if right - left > 0:
                    # ...then we found a contour above the baseline
                    found_contour_on_baseline = True
                    break

        # If there is no contour above on the baseline, then we may
        # still not want to remove this contour.
        if not found_contour_on_baseline:
            remove = True

            # Check to see whether there is a contour above this one
            # that satisfies certain criteria
            for inner_c in contours:
                other_rect_x, other_rect_y, other_rect_w, other_rect_h = (
                    cv2.boundingRect(inner_c)
                )

                # If the contour is above the other one...
                if other_rect_y < y:
                    # ...and it's overlapping...
                    left = max(x, other_rect_x)
                    right = min(x + w, other_rect_x + other_rect_w)
                    overlapped = right - left > 0

                    # ...and the other criteria are met, then this is probably a martyria
                    if (
                        overlapped
                        and other_rect_w < 0.75 * segmentation.oligon_width
                        and y - other_rect_y - other_rect_h
                        < 1.5 * segmentation.avg_text_height
                        and y + h - other_rect_y > 2 * segmentation.avg_text_height
                    ):
                        remove = False
                        break

            if not remove:
                continue

        # If we got this far, the contour is probably text and should be removed.
        # Mask the contour by drawing a filled rectangle over it
        text_contours.append(c)

    # Find melismas
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)

        for line in segmentation.textlines_adj:
            if (
                h <= min_contour_height
                and w > h
                and line <= y
                and y <= line + segmentation.avg_text_height
            ):
                text_contours.append(c)

    return text_contours


def remove_text(image, segmentation):
    contours = find_text_contours(image, segmentation)

    copy = image.copy()

    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        cv2.rectangle(copy, (x, y), (x + w, y + h), (0, 0, 0), cv2.FILLED)

    return copy
