import cv2
import sys
import yaml

sys.path.append("../src")
from model import load_classes, load_model
from ocr import process_image, process_pdf

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please specify the file path")
        exit(1)

    filepath = sys.argv[1]

    classes = load_classes("../models/classes.json")
    model = load_model("../models/current_model.pth", classes)
    model.eval()

    if filepath.endswith(".pdf"):
        results = process_pdf(filepath, [14, 14], model, classes)
    else:
        image = cv2.imread(filepath, cv2.IMREAD_GRAYSCALE)
        results = process_image(image, model, classes)

    with open("output.yaml", "w") as outfile:
        yaml.safe_dump(
            results.to_dict(), outfile, sort_keys=False, default_flow_style=False
        )