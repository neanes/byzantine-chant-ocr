"""
FiftyOne

This script starts an instance of FiftyOne. This is a tool that can be used to quickly
view and tag contours.

After tagging contours, use the update_dataset.py script to copy the tagged images into the model's dataset.
"""

import fiftyone as fo

if __name__ == "__main__":
    # Ensures that the App processes are safely launched on Windows
    session = fo.launch_app(port=5151)
    session.wait()
