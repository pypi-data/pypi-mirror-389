from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    # Use a package name matching the importable package to avoid confusion
    name="eastwood_games_downloader",
    # Bump version for a fixed upload
    version="0.1.1",
    author="Eastwood Games",
    author_email="your.email@example.com",
    description="A simple game downloader GUI prototype",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/eastwood-games-downloader",
    # Explicitly include the package to prevent accidental packaging of a
    # directory named `src` (which previously ended up as a top-level package
    # in the built wheel).
    packages=["eastwood_games_downloader"],
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