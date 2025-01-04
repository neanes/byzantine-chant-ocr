"""
Find Off Baseline

This script creates a dataset by searching a PDF or image for only neumes that do not touch the baseline.
"""

from show_off_baseline import filter
from create_dataset import setup

if __name__ == "__main__":
    setup(contour_filter=filter)
