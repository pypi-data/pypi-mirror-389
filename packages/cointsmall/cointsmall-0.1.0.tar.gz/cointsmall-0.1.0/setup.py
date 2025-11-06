"""
Setup script for cointsmall Python package
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="cointsmall",
    version="0.1.0",
    author="Jérôme Trinh (methodology), Dr. Merwan Roudane (R package), Python port",
    author_email="merwanroudane920@gmail.com",
    maintainer="Dr. Merwan Roudane",
    maintainer_email="merwanroudane920@gmail.com",
    description="Cointegration testing with structural breaks in very small samples (Python port of R package by Dr. Merwan Roudane, Independent Researcher)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/cointsmall-python",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Mathematics",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.7",
    install_requires=[
        "numpy>=1.19.0",
        "scipy>=1.5.0",
        "statsmodels>=0.12.0",
        "pandas>=1.1.0",
    ],
    extras_require={
        "dev": ["pytest>=6.0", "pytest-cov>=2.10"],
    },
)
