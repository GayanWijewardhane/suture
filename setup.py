#!/usr/bin/env python3
"""
Suture Installation Script
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / 'README.md'
long_description = readme_file.read_text() if readme_file.exists() else ''

setup(
    name='suture',
    version='0.5.0',
    description='Linux Error Detection & Auto-Fix Tool',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Your Name',
    author_email='your.email@example.com',
    url='https://github.com/yourusername/suture',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'click>=8.1.0',
        'colorama>=0.4.6',
        'pyyaml>=6.0',
        'regex>=2023.0.0',
        'tabulate>=0.9.0',
    ],
    entry_points={
        'console_scripts': [
            'suture=src.cli:cli',
        ],
    },
    package_data={
        'suture': ['rules/*.yaml', 'config/*.conf'],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: System Administrators',
        'Topic :: System :: Systems Administration',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
    python_requires='>=3.8',
)
