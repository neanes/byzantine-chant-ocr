import os
import matplotlib.pyplot as plt
import re

import numpy as np

DATASET_FOLDER = "../data/dataset"

sources = {}
class_names = os.listdir(DATASET_FOLDER)

for class_name in class_names:
    class_path = os.path.join(DATASET_FOLDER, class_name)
    if os.path.isdir(class_path):  # Ensure it's a directory
        files_in_class_path = os.listdir(class_path)
        sources_found = [
            re.search(r"(.*)_p\d\d\d\d.*", f).group(1) for f in files_in_class_path
        ]

        for source in sources_found:
            if not sources.get(source):
                sources[source] = {}

            sources[source][class_name] = len(
                [f for f in files_in_class_path if f.startswith(source)]
            )

# Plot the horizontal bar graph
plt.figure(figsize=(10, len(class_names) * 0.5))

# Set bar width
bar_width = 0.8 / len(sources)

# Y positions for bars
y_positions = np.arange(len(class_names))

i = 0

for source in sources:
    for class_name in class_names:
        if not sources[source].get(class_name):
            sources[source][class_name] = 0

    sorted_classes = sorted(sources[source].items(), key=lambda x: x[1], reverse=True)
    class_names, image_counts = zip(*sorted_classes)
    offset = (i - (len(sources) - 1) / 2) * bar_width
    plt.barh(y_positions + offset, image_counts, height=bar_width, label=source)
    i = i + 1

plt.xlabel("Number of Images")
plt.ylabel("Class Names")
plt.yticks(y_positions, class_names)
plt.title("Number of Images per Class")
plt.gca().invert_yaxis()
plt.tight_layout()
plt.legend()
plt.show()
