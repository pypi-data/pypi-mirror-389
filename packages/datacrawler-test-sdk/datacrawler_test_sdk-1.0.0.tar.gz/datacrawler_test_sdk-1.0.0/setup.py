from codecs import open
from os import path

from setuptools import find_packages, setup

here = path.abspath(path.dirname(__file__))

setup(
    name="datacrawler-test-sdk",
    version="1.0.0",
    description="A Smart, Automatic, Fast and Lightweight Web Scraper for Python",
    long_description_content_type="text/markdown",
    url="https://github.com/siddharth-shah-17/Datacrawler-Experimental",
    author="Siddharth Shah",
    author_email="team@svector.co.in",
    license="MIT",
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
    ],
    keywords="scraping - scraper - crawler - web scraping",
    packages=find_packages(exclude=["contrib", "docs", "tests"]),
    python_requires=">=3.6",
    install_requires=["requests", "bs4", "lxml"],
)
