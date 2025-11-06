from setuptools import setup, find_packages
import pathlib

# The directory containing this file
here = pathlib.Path(__file__).parent.resolve()

# Read the README file for the long description
long_description = (here / "README.md").read_text(encoding="utf-8")

setup(
    name="BinaryTreePy",                # PyPI package name
    version="0.0.1",
    author="Pramod Dixit",
    author_email="your_email@example.com",
    description="A simple Python library for creating and working with binary trees",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/BinaryTreePy",  # optional
    packages=find_packages(),            # automatically finds 'binarytreepy' package
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    license="MIT",                       # Correct way to specify license
)
