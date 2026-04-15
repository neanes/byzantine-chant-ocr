"""
Find Quality

This script creates a dataset by searching a PDF or image for only neumes that are wide quality characters such as the omalon, heteron, psifiston, etc.

It is useful for quickly searching many pages for such neumes and creating a dataset containing
only likely candidates.
"""

from create_dataset import setup
from show_quality import transform

if __name__ == "__main__":
    setup(transform)
