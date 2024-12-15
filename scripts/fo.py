import fiftyone as fo

if __name__ == "__main__":
    # Ensures that the App processes are safely launched on Windows
    session = fo.launch_app(port=5151)
    session.wait()
