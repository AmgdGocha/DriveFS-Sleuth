"""
Author: Amged Wageh
Email: amged_wageh@outlook.com
LinkedIn: https://www.linkedin.com/in/amgedwageh/
"""

import re
import os

from setuptools import setup, find_packages

with open(
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "src", "drivefs_sleuth", "__init__.py"
    ),
    encoding="utf-8",
) as version_file:
    __version__ = re.search(
        r'__version__\s*=\s*["\']([^"\']+)["\']', version_file.read()
    ).group(1)

setup(
    name="drivefs_sleuth",
    version=__version__,
    description="The ultimate Google Drive File Stream Investigator!",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Amged Wageh",
    author_email="amged_wageh@outlook.com",
    url="https://github.com/AmgdGocha/DriveFS-Sleuth",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "Jinja2~=3.1.2",
        "bbpb",
    ],
    entry_points={
        "console_scripts": [
            "drivefs-sleuth=drivefs_sleuth.executor:execute",
        ],
    },
    license="Eclipse Public License 2.0",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Other Audience",
        "License :: OSI Approved :: Eclipse Public License 2.0 (EPL-2.0)",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Security",
        "Operating System :: OS Independent",
    ],
    include_package_data=True,
    package_data={
        "drivefs_sleuth": ["html_resources/*.html"],
    },
)

