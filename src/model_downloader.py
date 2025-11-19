import requests
from pathlib import Path


def download_latest_model(out_dir: Path):
    """
    Downloads the latest model assets based on dist/model/latest.json in the repo.
    Saves current_model.onnx and metadata.json into out_dir.

    Returns:
        str: The tag of the latest release.
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    owner = "neanes"
    repo = "byzantine-chant-ocr"
    branch = "master"

    # URL of the JSON file in the repo
    latest_json_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/dist/model/latest.json"

    # Fetch latest.json
    response = requests.get(latest_json_url)
    response.raise_for_status()
    latest_info = response.json()

    # Extract URLs for model assets
    model_url = latest_info["assets"]["model"]
    metadata_url = latest_info["assets"]["metadata"]

    # Prepare paths
    model_out = out_dir / "current_model.onnx"
    metadata_out = out_dir / "metadata.json"

    # Download model file
    r = requests.get(model_url)
    r.raise_for_status()
    model_out.write_bytes(r.content)

    # Download metadata
    r = requests.get(metadata_url)
    r.raise_for_status()
    metadata_out.write_bytes(r.content)

    return latest_info["latest_release"]
