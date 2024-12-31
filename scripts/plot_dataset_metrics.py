import os
import matplotlib.pyplot as plt

DATASET_FOLDER = "../data/dataset"

class_counts = {}

for class_name in os.listdir(DATASET_FOLDER):
    class_path = os.path.join(DATASET_FOLDER, class_name)
    if os.path.isdir(class_path):  # Ensure it's a directory
        image_count = len(os.listdir(class_path))
        class_counts[class_name] = image_count

# Sort classes by the number of images
sorted_classes = sorted(class_counts.items(), key=lambda x: x[1], reverse=True)
class_names, image_counts = zip(*sorted_classes)

# Plot the horizontal bar graph
plt.figure(figsize=(10, len(class_names) * 0.5))
plt.barh(class_names, image_counts, color="skyblue")
plt.xlabel("Number of Images")
plt.ylabel("Class Names")
plt.title("Number of Images per Class")
plt.gca().invert_yaxis()
plt.tight_layout()
plt.show()
