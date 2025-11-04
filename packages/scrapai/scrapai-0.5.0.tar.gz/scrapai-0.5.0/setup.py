"""
Setup script for ScrapAI SDK
"""

from setuptools import setup, find_packages

# Use PyPI-specific README for package description
# Keep GitHub README.md for detailed technical documentation
try:
    with open("README_PYPI.md", "r", encoding="utf-8") as fh:
        long_description = fh.read()
except FileNotFoundError:
    # Fallback to main README if PyPI README doesn't exist
    with open("README.md", "r", encoding="utf-8") as fh:
        long_description = fh.read()

setup(
    name="scrapai",
    version="0.5.0",
    author="Zohaib Yousaf",
    author_email="chzohaib136@gmail.com",
    description="AI-powered web scraping SDK with intelligent configuration generation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/zohaib3249/scrapai",
    project_urls={
        "Bug Reports": "https://github.com/zohaib3249/scrapai/issues",
        "Source": "https://github.com/zohaib3249/scrapai",
        "Documentation": "https://github.com/zohaib3249/scrapai#readme",
    },
    packages=find_packages(exclude=["tests", "tests.*", "examples", "examples.*"]),
    keywords="web-scraping, ai, scraping, automation, data-extraction, scraping-sdk, ai-agent, web-crawler",
    license="MIT",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: Indexing/Search",
    ],
    python_requires=">=3.8",
    install_requires=[
        # HTTP requests
        "requests>=2.32.5",
        "urllib3>=2.5.0",  # Directly imported in http_client.py
        # HTML parsing
        "beautifulsoup4>=4.14.2",
        "lxml>=6.0.2",
        # User agent rotation
        "fake-useragent>=2.2.0",
        # AI service client (OpenAI-compatible API)
        "openai>=2.6.1",
        "playwright>=1.55.0",
        "playwright-stealth>=2.0.0",
    ],
    extras_require={
        # Browser rendering (Playwright)
        "playwright": [
            "playwright>=1.55.0",
            "playwright-stealth>=2.0.0",
        ],
        # All optional dependencies
        "all": [
            "playwright>=1.55.0",
            "playwright-stealth>=2.0.0",
        ],
    },
)

