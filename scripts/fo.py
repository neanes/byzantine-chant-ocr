import fiftyone as fo

# Load your FiftyOne dataset
dataset = fo.Dataset.from_dir(
    dataset_type=fo.types.ImageClassificationDirectoryTree,
    dataset_dir="../data",
)

if __name__ == "__main__":
    # Ensures that the App processes are safely launched on Windows
    session = fo.launch_app(dataset)
    session.wait()
