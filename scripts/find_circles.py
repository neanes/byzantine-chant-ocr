"""
Find Circles

This script creates a dataset by searching a PDF or image for only neumes that are circular.
For example: the diatonic fthora for PA, GA, DI, KE, etc.

It is useful for quickly searching many pages for circular neumes and creating a dataset containing
only likely candidates.
"""

from create_dataset import setup
from show_circles import filter

if __name__ == "__main__":
    setup(contour_filter=filter)
