import json
import sys
from pathlib import Path


def generate_latest_model_file(tag: str):
    """
    Generate a latest.json file that points to the GitHub release for the given tag,
    including direct links to the model assets.
    """
    owner = "neanes"
    repo = "byzantine-chant-ocr"

    base_release_url = f"https://github.com/{owner}/{repo}/releases/tag/{tag}"
    base_asset_url = f"https://github.com/{owner}/{repo}/releases/download/{tag}"

    data = {
        "latest_release": tag,
        "release_url": base_release_url,
        "assets": {
            "model": f"{base_asset_url}/current_model.onnx",
            "metadata": f"{base_asset_url}/metadata.json",
        },
    }

    print(json.dumps(data, indent=2))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python generate_latest_json.py <tag>")
        sys.exit(1)

    tag = sys.argv[1]

    generate_latest_model_file(tag)
