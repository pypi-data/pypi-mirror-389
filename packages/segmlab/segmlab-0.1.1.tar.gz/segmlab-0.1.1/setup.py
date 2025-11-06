from setuptools import setup, find_packages

setup(
    name="segmlab",
    version="0.1.1",
    author="Divine Gupta, Kartikeya Mishra, Chaitnya Sharma",
    author_email="divine@example.com",
    description="A lightweight SAM-based image segmentation labeling library",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/seglab",
    packages=find_packages(),
    install_requires=[
        "ultralytics>=8.2.0",
        "torch>=2.0.0",
        "opencv-python",
        "matplotlib",
        "numpy"
    ],
    python_requires=">=3.8",
)
