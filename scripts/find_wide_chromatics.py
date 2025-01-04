"""
Find Wide Chromatics

This script creates a dataset by searching a PDF or image for only neumes that resemble the wide fthores and martyria for chromatics.
"""

from show_wide_chromatics import filter
from create_dataset import setup

if __name__ == "__main__":
    setup(contour_filter=filter)
