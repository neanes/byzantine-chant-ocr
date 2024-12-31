import os
import sys
import matplotlib.pyplot as plt

DATASET_FOLDER = "../data/dataset"


def plot_metrics(source):
    class_counts = {}

    for class_name in os.listdir(DATASET_FOLDER):
        class_path = os.path.join(DATASET_FOLDER, class_name)
        if os.path.isdir(class_path):  # Ensure it's a directory
            image_count = len(
                [f for f in os.listdir(class_path) if f.startswith(source)]
            )
            class_counts[class_name] = image_count

    # Sort classes by the number of images
    sorted_classes = sorted(class_counts.items(), key=lambda x: x[1], reverse=True)
    class_names, image_counts = zip(*sorted_classes)

    # Plot the horizontal bar graph
    plt.figure(figsize=(10, len(class_names) * 0.5))
    plt.barh(class_names, image_counts, color="skyblue")
    plt.xlabel("Number of Images")
    plt.ylabel("Class Names")
    plt.title(f"Number of Images per Class for {source}")
    plt.gca().invert_yaxis()
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please specify the source.")
        exit(1)

    source = sys.argv[1]

    plot_metrics(source)
