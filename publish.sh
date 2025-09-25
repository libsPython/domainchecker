#!/bin/bash

# DomainChecker PyPI Publishing Script

set -e

echo "🚀 Publishing DomainChecker to PyPI..."

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: pyproject.toml not found. Run this script from the domainchecker directory."
    exit 1
fi

# Check if twine is installed
if ! command -v twine &> /dev/null; then
    echo "📦 Installing twine..."
    pip install twine build
fi

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build/ dist/ *.egg-info/

# Build the package
echo "🔨 Building package..."
python -m build

# Check the build
echo "✅ Checking build..."
twine check dist/*

# Upload to PyPI
echo "📤 Uploading to PyPI..."
read -p "Enter your PyPI username: " username
read -s -p "Enter your PyPI password: " password
echo

twine upload dist/* --username "$username" --password "$password"

echo "🎉 DomainChecker successfully published to PyPI!"
echo "📦 Package: https://pypi.org/project/domainchecker/"
