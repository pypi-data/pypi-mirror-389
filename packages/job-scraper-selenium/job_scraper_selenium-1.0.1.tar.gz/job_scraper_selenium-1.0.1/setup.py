"""
Setup script for job_scraper package
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="job-scraper-selenium",
    version="1.0.1",
    author="Adil C",
    author_email="adilc0070@gmail.com",
    description="A Python package for scraping job postings from Indeed and LinkedIn",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/adilc0070/job-scraper",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    keywords="job scraper indeed linkedin selenium web-scraping",
    project_urls={
        "Bug Reports": "https://github.com/adilc0070/job-scraper/issues",
        "Source": "https://github.com/adilc0070/job-scraper",
    },
)

