"""
Setup configuration for google-search-scraper package
"""

from setuptools import setup, find_packages
from setuptools.command.install import install
import subprocess
import sys

class PostInstallCommand(install):
    """Post-installation for installing Playwright browsers"""
    def run(self):
        install.run(self)
        # Only attempt to install Playwright browsers during actual pip install,
        # not during build process (when playwright may not be installed yet)
        try:
            import playwright
            try:
                print("\n" + "="*60)
                print("Installing Playwright browsers...")
                print("="*60)
                subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
                print("\n" + "Playwright chromium browser installed successfully!")
                print("="*60 + "\n")
            except subprocess.CalledProcessError:
                print("\nWarning: Failed to install Playwright browsers automatically.")
                print("Please run manually: playwright install chromium\n")
        except ImportError:
            # Playwright not yet installed (happens during build)
            pass

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="google-search-aj",
    version="1.0.4",
    author="Aditya Jangam",
    author_email="adityajangam25@gmail.com",
    description="Fast, lightweight Google search scraper with stealth mode",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Aaditya17032002/google-search",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: Indexing/Search",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "playwright>=1.40.0",
        "beautifulsoup4>=4.12.0",
    ],
    cmdclass={
        'install': PostInstallCommand,
    },
    entry_points={
        'console_scripts': [
            'google-search=google_search_scraper.cli:main',
        ],
    },
    keywords='google search scraper web-scraping playwright automation',
    project_urls={
        'Homepage': 'https://github.com/Aaditya17032002/google-search',
        'Bug Reports': 'https://github.com/Aaditya17032002/google-search/issues',
        'Source': 'https://github.com/Aaditya17032002/google-search',
        'Documentation': 'https://github.com/Aaditya17032002/google-search#readme',
    },
)