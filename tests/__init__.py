"""
Author: Amged Wageh
Email: amged_wageh@outlook.com
LinkedIn: https://www.linkedin.com/in/amgedwageh/
Description: bootstrap for the test suite; makes the src/ package importable before test discovery.
"""

import os
import sys

_TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
_SRC_DIR = os.path.abspath(os.path.join(_TESTS_DIR, os.pardir, "src"))
for directory in (_SRC_DIR, _TESTS_DIR):
    if directory not in sys.path:
        sys.path.insert(0, directory)
