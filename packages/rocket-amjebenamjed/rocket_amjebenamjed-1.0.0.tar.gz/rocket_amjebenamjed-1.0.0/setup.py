from setuptools import setup, find_packages

setup(
    name="rocket_amjebenamjed",  # The package name (what you'll install with pip)
    version="1.0.0",  # Your version number
    author="Ben Amjed",
    author_email="your_email@example.com",  # optional but recommended
    description="A Python package modeling Rockets, Shuttles, and Circular Rockets with distance, area, and circumference calculations.",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/rocket",  # optional if you have GitHub
    packages=find_packages(),  # Automatically finds all subpackages (like rocket/)
    install_requires=[],  # dependencies (usually standard libs not included)
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
