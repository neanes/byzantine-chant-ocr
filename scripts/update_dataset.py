"""
Update Dataset

This script looks through a FiftyOne dataset and copies all tagged samples into the model's dataset
located at data/dataset.

Usage: python update_dataset.py dataset_name
"""

import os
import shutil
import sys


def update_dataset(dataset, dataset_folder):
    count = 0
    for sample in dataset:
        if sample.tags:
            label = sample.tags[0]
            class_folder = os.path.join(dataset_folder, label)
            os.makedirs(class_folder, exist_ok=True)

            new_path = os.path.join(class_folder, os.path.basename(sample.filepath))

            if not os.path.exists(new_path):
                shutil.copy(sample.filepath, new_path)
                count = count + 1

    print(f"Added {count} files to {dataset_folder}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please specify the name of the dataset.")
        exit(1)

    dataset_name = sys.argv[1]

    print("Loading FiftyOne...")
    import fiftyone as fo

    print("Loading dataset...")
    dataset = fo.load_dataset(dataset_name)
    print("Adding files...")
    update_dataset(dataset, "../data/dataset")
