"""
Job Scraper - A Python package for scraping job postings from Indeed and LinkedIn

This package provides easy-to-use functions for extracting job details from popular
job posting websites using Selenium for browser automation.

Author: Adil C
License: MIT
"""

__version__ = "1.0.2"
__author__ = "Adil C"
__email__ = "adilc0070@gmail.com"

from .scraper import scrape_job, scrape_indeed_job, scrape_linkedin_job

__all__ = ['scrape_job', 'scrape_indeed_job', 'scrape_linkedin_job']

