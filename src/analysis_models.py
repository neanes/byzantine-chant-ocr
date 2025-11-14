class ContourMatch:
    def __init__(self):
        self.id: int = -1
        self.bounding_circle: Circle | None = None
        self.bounding_rect: Rect | None = None
        self.test_image = None
        self.label: str | None = None
        self.confidence: float = 0
        self.line: int = -1
        self.grouped: bool = False

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


class PageAnalysis:
    def __init__(self):
        self.id = 0
        self.original_page_num = None
        self.page_area = None
        self.interpreted_groups = []
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
        result["interpreted_groups"] = [x.to_dict() for x in self.interpreted_groups]

        return result


class Analysis:
    def __init__(self):
        self.schema_version = 1
        self.model_metadata = None
        self.pages = []

    def to_dict(self):
        return {
            "schema_version": self.schema_version,
            "model_metadata": self.model_metadata.to_dict(),
            "pages": [x.to_dict() for x in self.pages],
        }


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
