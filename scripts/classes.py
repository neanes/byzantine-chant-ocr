import os
import json
from torchvision import datasets

data_dir = "../data"

# Get class names
class_names = datasets.ImageFolder(
    os.path.join(data_dir, "train"),
).classes

with open("../models/classes.json", "w") as f:
    json.dump(class_names, f, indent=4)
