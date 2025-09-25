#!/usr/bin/env python3
"""
Setup script for DomainChecker package.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

# Read version from __init__.py
def get_version():
    with open("src/domainchecker/__init__.py", "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("__version__"):
                return line.split("=")[1].strip().strip('"').strip("'")
    return "1.0.0"

setup(
    name="domainchecker-taxlien",
    version=get_version(),
    author="TaxLien Team",
    author_email="team@taxlien.online",
    description="Comprehensive domain checking, WHOIS lookup, and DNS resolution library",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/taxlien-online/domainchecker",
    project_urls={
        "Bug Tracker": "https://github.com/taxlien-online/domainchecker/issues",
        "Documentation": "https://domainchecker.readthedocs.io",
        "Source Code": "https://github.com/taxlien-online/domainchecker",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Networking",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.31.0",
        "python-whois>=0.8.0",
        "dnspython>=2.4.0",
        "python-dateutil>=2.9.0",
        "colorama>=0.4.6",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.11.0",
            "isort>=5.12.0",
            "flake8>=6.1.0",
            "mypy>=1.7.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "domainchecker=domainchecker.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
