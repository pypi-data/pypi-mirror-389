from setuptools import setup, find_packages
import codecs
import os

here = os.path.abspath(os.path.dirname(__file__))

with codecs.open(os.path.join(here, "README.md"), encoding="utf-8") as fh:
    long_description = "\n" + fh.read()

# Read requirements.txt
with open(os.path.join(here, "requirements.txt")) as f:
    requirements = f.read().splitlines()

with open(os.path.join(here, "luminanet", "__init__.py")) as f:
    for line in f.readlines():
        if line.startswith("__version__"):
            version = line.split("=")[1].strip().strip('"').strip("'")
            break

setup(
    name="luminanet",
    version=version,
    author="Your Name",
    author_email="your.email@example.com",
    description="LuminaNet: Pure Python Deep Learning Framework - Illuminate AI with Minimal Dependencies",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(include=['luminanet', 'luminanet.*']),
    install_requires=requirements,  # ✅ Gunakan requirements.txt
    keywords=[
        "deep learning", 
        "neural networks", 
        "machine learning",
        "pure python",
        "termux",
        "numpy",
        "educational",
        "luminanet"
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Education"
    ],
    python_requires=">=3.7",
    project_urls={
        "Source": "https://github.com/iyazkasep/luminanet",
        "Bug Reports": "https://github.com/iyazkasep/luminanet/issues",
    },
)
