import os
import json
import torch
from torchvision import models
from torchvision import transforms
from torch.utils.data import DataLoader
from torch.utils.data import Dataset
from torchvision import datasets
import torch.nn as nn
import torch.optim as optim

from test import test_model


class EarlyStopper:
    def __init__(self, patience=1, min_delta=0):
        self.patience = patience
        self.min_delta = min_delta
        self.counter = 0
        self.min_validation_loss = float("inf")

    def early_stop(self, validation_loss):
        if validation_loss < self.min_validation_loss:
            self.min_validation_loss = validation_loss
            self.counter = 0
        elif validation_loss > (self.min_validation_loss + self.min_delta):
            self.counter += 1
            if self.counter >= self.patience:
                return True
        return False


class AugmentedDataset(Dataset):
    def __init__(self, root_dir, transform=None, num_augments=100):
        self.dataset = datasets.ImageFolder(root=root_dir)
        self.transform = transform
        self.num_augments = num_augments  # How many augmentations to apply per image

        self.classes = self.dataset.classes
        self.class_to_idx = self.dataset.class_to_idx

    def __len__(self):
        return (
            len(self.dataset) * self.num_augments
        )  # Multiply the size by the number of augmentations

    def __getitem__(self, idx):
        # Determine which image and class to use
        img_idx = idx // self.num_augments
        img, label = self.dataset[img_idx]

        # Apply the transform (augmentation)
        augmented_img = img
        if self.transform:
            augmented_img = self.transform(augmented_img)

        return augmented_img, label


data_dir = "../data/dataset"

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

# Define augmentations for training data
data_transforms = {
    "train": transforms.Compose(
        [
            # transforms.Resize((224, 224)),
            # transforms.RandomResizedCrop(128),  # Random crop and resize
            # transforms.RandomHorizontalFlip(),  # Flip images horizontally
            # transforms.RandomRotation(20),  # Random rotation up to 20 degrees
            # transforms.ColorJitter(
            #    brightness=0.2, contrast=0.2, saturation=0.2
            # ),  # Adjust brightness, contrast, etc.
            transforms.ToTensor(),  # Convert to tensor. Scales to [0, 1]
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ]
    ),
    "val": transforms.Compose(
        [
            # transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ]
    ),
}

# remove emtpy folders
# for folder in os.listdir(os.path.join(data_dir, "train")):
#     folder_path = os.path.join(os.path.join(data_dir, "train"), folder)
#     if os.path.isdir(folder_path) and not os.listdir(folder_path):
#         print(f"Removing empty folder: {folder_path}")
#         os.rmdir(folder_path)  # Remove empty folder

# for folder in os.listdir(os.path.join(data_dir, "val")):
#     folder_path = os.path.join(os.path.join(data_dir, "val"), folder)
#     if os.path.isdir(folder_path) and not os.listdir(folder_path):
#         print(f"Removing empty folder: {folder_path}")
#         os.rmdir(folder_path)  # Remove empty folder

# Load datasets with augmentations
# image_datasets = {
#     "train": AugmentedDataset(
#         root_dir=os.path.join(data_dir, "train"),
#         transform=data_transforms["train"],
#         num_augments=1,
#     ),
#     "val": datasets.ImageFolder(
#         os.path.join(data_dir, "val"),
#         transform=data_transforms["val"],
#     ),
# }

full_dataset = datasets.ImageFolder(data_dir, transform=data_transforms["train"])


class_names = full_dataset.classes

with open("../models/classes.json", "w") as f:
    json.dump(class_names, f, indent=4)

train_dataset, val_dataset, test_dataset = torch.utils.data.random_split(
    full_dataset, [0.7, 0.15, 0.15]
)

image_datasets = {
    "train": train_dataset,
    "val": val_dataset,
    "test": test_dataset,
}

# Create DataLoaders
batch_size = 32
dataloaders = {
    "train": DataLoader(train_dataset, batch_size=batch_size, shuffle=True),
    "val": DataLoader(val_dataset, batch_size=batch_size, shuffle=False),
    "test": DataLoader(test_dataset, batch_size=batch_size, shuffle=False),
}

# print("train classes\n")
# for n in class_names:
#     print(n)

# print("val classes\n")
# for n in image_datasets["val"].classes:
#     print(n)

# Load the pre-trained MobileNetV2 model
model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.DEFAULT)

# Modify the last layer to match the number of classes
num_features = model.last_channel  # Get the size of the last layer
model.classifier[1] = nn.Linear(num_features, len(class_names))  # Replace classifier

# Move model to device
model = model.to(device)

# Freeze all layers except the classifier
for param in model.features.parameters():
    param.requires_grad = False

optimizer = optim.Adam(
    model.classifier.parameters(), lr=0.001
)  # Only update classifier layers
criterion = nn.CrossEntropyLoss()

# Training loop (same as before)
# patience=5, min_delta=1e-4
early_stopper = EarlyStopper(patience=3, min_delta=1e-3)

num_epochs = 50
try:
    for epoch in range(num_epochs):
        print(f"Epoch {epoch+1}/{num_epochs}")
        for phase in ["train", "val"]:
            if phase == "train":
                model.train()
            else:
                model.eval()

            running_loss = 0.0
            running_corrects = 0

            for inputs, labels in dataloaders[phase]:
                inputs, labels = inputs.to(device), labels.to(device)

                optimizer.zero_grad()
                with torch.set_grad_enabled(phase == "train"):
                    outputs = model(inputs)
                    _, preds = torch.max(outputs, 1)
                    loss = criterion(outputs, labels)

                    if phase == "train":
                        loss.backward()
                        optimizer.step()

                running_loss += loss.item() * inputs.size(0)
                running_corrects += torch.sum(preds == labels.data)

            epoch_loss = running_loss / len(image_datasets[phase])
            epoch_acc = running_corrects.double() / len(image_datasets[phase])

            print(f"{phase} Loss: {epoch_loss:.4f} Acc: {epoch_acc:.4f}")

            if phase == "val" and early_stopper.early_stop(epoch_loss):
                print("Stopping early.")
                break
    torch.save(model.state_dict(), "current_model.pth")
except KeyboardInterrupt:
    print("Training interrupted! Saving the current model...")
    torch.save(model.state_dict(), "interrupted_model.pth")
    print("Model saved. You can resume training later or use the saved model as is.")

print("\n\nTesting Model\n\n")
test_model(model, dataloaders["test"], device)
