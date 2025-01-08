"""
Find On Baseline

This script creates a dataset by searching a PDF or image for only neumes that touch the baseline.
"""

from show_on_baseline import filter
from create_dataset import setup

if __name__ == "__main__":
    setup(contour_filter=filter)
