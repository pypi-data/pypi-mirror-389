from setuptools import setup, find_packages
import os

# Read README
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
try:
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]
except FileNotFoundError:
    requirements = []

setup(
    name="versalaw2",
    version="0.1.5",  # Increment version
    author="Your Name",
    author_email="your.email@example.com",
    description="Comprehensive Indonesian Law Library with International Law Modules",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    package_data={
        'versalaw2': ['*.py', 'indonesian_law/*', 'international_law/*'],
    },
    include_package_data=True,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Legal Professionals",
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
    install_requires=requirements,
    keywords="law, legal, indonesia, international, criminal, civil",
)
