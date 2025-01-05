"""
Find Yporroe

This script creates a dataset by searching a PDF or image for only neumes that are similar to the yporroe.

It is useful for quickly searching many pages for yprorre neumes and creating a dataset containing
only likely candidates.
"""

from show_yporroe import filter
from create_dataset import setup

if __name__ == "__main__":
    setup(contour_filter=filter)
