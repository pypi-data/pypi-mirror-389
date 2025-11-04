from setuptools import setup, find_packages
import os

# Read the contents of your README file
with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="terminal-media-player",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Play videos and images as ASCII art in your terminal",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/terminal-media-player",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.7",
    install_requires=[
        "opencv-python>=4.5.0",
        "Pillow>=8.0.0",
        "numpy>=1.19.0",
    ],
    entry_points={
        "console_scripts": [
            "tmp=terminal_media_player.cli:main",
            "terminal-media-player=terminal_media_player.cli:main",
            "ascii-video=terminal_media_player.cli:main",
        ],
    },
    keywords="terminal ascii video image media player",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/terminal-media-player/issues",
        "Source": "https://github.com/yourusername/terminal-media-player",
    },
)