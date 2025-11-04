from setuptools import setup, find_packages

from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="log_colors",
    version="0.1.0",
    packages=find_packages(),
    description="A colorful logging library for Python",
    long_description=long_description,
    long_description_content_type='text/markdown',
    author="avery-kb",
    install_requires=[],
    python_requires=">=3.7",
    url="https://github.com/avery-kb/log_colors",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
