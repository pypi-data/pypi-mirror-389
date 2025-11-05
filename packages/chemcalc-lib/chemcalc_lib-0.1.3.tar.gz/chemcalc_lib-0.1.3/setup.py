# setup.py
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="chemcalc_lib",
    version="0.1.3", 
    author="Théophile Gaudin",
    author_email="gaudin.theophile@gmail.com",
    description="A library for chemical mixture calculations and composition conversions",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/TheophileGaudin/chemcalc-lib",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License", 
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9", 
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Chemistry",
        "Topic :: Scientific/Engineering :: Mathematics",
    ],
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.19.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
        ],
        "examples": [],
    },
    keywords="chemistry mixture mole fraction composition chemical calculations",
    project_urls={
        "Bug Reports": "https://github.com/TheophileGaudin/chemcalc-lib/issues",
        "Source": "https://github.com/TheophileGaudin/chemcalc-lib",
        "Documentation": "https://github.com/TheophileGaudin/chemcalc-lib/blob/main/README.md",
    },
    include_package_data=True,
    zip_safe=False,
)