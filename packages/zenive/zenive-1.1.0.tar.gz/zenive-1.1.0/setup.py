#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import os
import re

def get_version():
    """Get version from zen/__init__.py without importing the module."""
    version_file = os.path.join(os.path.dirname(__file__), 'zen', '__init__.py')
    with open(version_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", content, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string in zen/__init__.py")

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

def get_requirements():
    """Read requirements from requirements.txt."""
    try:
        with open("requirements.txt", "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip() and not line.startswith("#")]
    except FileNotFoundError:
        return []

setup(
    name="zenive",
    version=get_version(),
    author="TheRaj71",
    author_email="theraj71@example.com",
    description="Python component registry system inspired by shadcn/ui - install components from GitHub",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/TheRaj71/Zenive",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Code Generators",
        "Topic :: System :: Software Distribution",
    ],
    python_requires=">=3.8",
    install_requires=get_requirements(),
    entry_points={
        "console_scripts": [
            "zen=zen.cli.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "zen": ["templates/*", "schemas/*"],
    },
    keywords="components, registry, shadcn, python, cli, zen",
    project_urls={
        "Bug Tracker": "https://github.com/TheRaj71/Zenive/issues",
        "Source Code": "https://github.com/TheRaj71/Zenive",
    },
)
