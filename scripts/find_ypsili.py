"""
Find Ypsili

This script creates a dataset by searching a PDF or image for only neumes that are similar
to the shape of an ypsili.

It is useful for quickly searching many pages for ypsilis and creating a dataset containing
only likely candidates.
"""

from create_dataset import setup
from show_ypsili import transform

if __name__ == "__main__":
    setup(transform)
