from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="eastwood-games-downloader",
    version="0.1.0",
    author="Eastwood Games",
    author_email="your.email@example.com",
    description="A simple game downloader GUI prototype",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/eastwood-games-downloader",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "eastwood-games=eastwood_games_downloader.main:main",
        ],
    },)