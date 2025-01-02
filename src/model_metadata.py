import json


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


def load_metadata(metadata_path):
    metadata = ModelMetadata()
    with open(metadata_path) as f:
        metadata.from_json(json.load(f))
    return metadata
