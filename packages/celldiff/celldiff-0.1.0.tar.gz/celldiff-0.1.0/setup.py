"""Setup script for CellDiffusion package."""

from setuptools import setup, find_packages
import os

# Read the contents of README file
this_directory = os.path.abspath(os.path.dirname(__file__))

# Get package version
version = {}
with open(os.path.join(this_directory, "CellDiffusion", "_version.py")) as f:
    exec(f.read(), version)

# Read requirements (be robust if file is absent in some build contexts)
requirements = []
try:
    with open(os.path.join(this_directory, "requirements.txt")) as f:
        requirements = f.read().splitlines()
except FileNotFoundError:
    requirements = []

# Long description from README.md
with open(os.path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_readme = f.read()

setup(
    name="celldiff",
    version=version["__version__"],
    author=version["__author__"],
    author_email=version["__email__"],
    description="A Python package for generating pseudo-cells using diffusion models",
    long_description=long_readme,
    long_description_content_type="text/markdown",
    url="https://github.com/ShiltonZhang/CellDiffusion",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    license="AGPL-3.0",
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov",
            "black",
            "flake8",
            "mypy",
            "jupyter",
            "matplotlib",
            "seaborn",
        ],
        "docs": [
            "sphinx",
            "sphinx-rtd-theme",
            "sphinxcontrib-napoleon",
        ]
    },
    include_package_data=True,
    zip_safe=False,
    keywords="single-cell, diffusion-models, pseudo-cells, bioinformatics, machine-learning",
    project_urls={
        "Bug Reports": "https://github.com/ShiltonZhang/CellDiffusion/issues",
        "Source": "https://github.com/ShiltonZhang/CellDiffusion",
    },
)





