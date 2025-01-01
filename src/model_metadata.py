class ModelMetadata:
    def __init__(self):
        self.model_version = None
        self.classes = None

    def to_dict(self):
        return {
            "model_version": self.model_version,
            "classes": self.classes,
        }

    def from_json(self, json):
        self.model_version = json["model_version"]
        self.classes = json["classes"]
