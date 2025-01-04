"""
Find Circles 3

This script creates a dataset by searching a PDF or image for only neumes that are circular.
Unlike find_circles, it looks for circles that specifically have lines protuding directly east and west,
althought it will still detect slanted lines, too.

It is useful for quickly searching many pages for circular neumes and creating a dataset containing
only likely candidates.
"""

from show_circles3 import filter
from create_dataset import setup

if __name__ == "__main__":
    setup(contour_filter=filter)
