import os
import numpy as np
import sys
import pandas as pd
import matplotlib.pyplot as plt


def plot_metrics(file_path):
    # Check if the file exists
    if not os.path.exists(file_path):
        print(f"No data to plot. File '{file_path}' not found.")
        return

    # Load metrics from the CSV file
    metrics_df = pd.read_csv(file_path)

    epochs = metrics_df["epoch"]
    train_loss = metrics_df["train_loss"]
    val_loss = metrics_df["val_loss"]
    train_acc = metrics_df["train_acc"]
    val_acc = metrics_df["val_acc"]

    # Plot loss and accuracy
    plt.figure(figsize=(12, 6))

    # Loss plot
    plt.subplot(1, 2, 1)
    plt.plot(epochs, train_loss, label="Train Loss", color="blue", marker="o")
    plt.plot(epochs, val_loss, label="Val Loss", color="orange", marker="o")
    plt.xlabel("Epoch")
    plt.ylabel("Loss")
    plt.title("Training Loss")
    plt.xticks(ticks=np.arange(min(epochs), max(epochs) + 1, step=1))
    plt.legend()

    # Accuracy plot
    plt.subplot(1, 2, 2)
    plt.plot(epochs, train_acc, label="Train Accuracy", color="blue", marker="o")
    plt.plot(epochs, val_acc, label="Val Accuracy", color="orange", marker="o")
    plt.xlabel("Epoch")
    plt.ylabel("Accuracy")
    plt.title("Training Accuracy")
    plt.xticks(ticks=np.arange(min(epochs), max(epochs) + 1, step=1))
    plt.legend()

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please specify the file path to the metrics.")
        exit(1)

    filepath = sys.argv[1]

    plot_metrics(filepath)
