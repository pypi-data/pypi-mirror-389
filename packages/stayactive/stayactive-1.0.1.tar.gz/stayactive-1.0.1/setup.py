from setuptools import setup, find_packages
import os

# Read README if it exists
long_description = "A simple activity simulator utility"
if os.path.exists("README.md"):
    with open("README.md", encoding="utf-8") as f:
        long_description = f.read()

setup(
    name="stayactive",
    version="1.0.1",
    packages=find_packages(),
    install_requires=[
        "pyautogui",
        "pynput",
    ],
    entry_points={
        "console_scripts": [
            "stayactive=stayactive.__main__:main",
        ],
    },
    author="Rajdeep Banik",
    author_email="banik.rajdeep1056@gmail.com",
    description="A simple activity simulator utility",
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)