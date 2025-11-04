"""Setup script for CQTech Metrics SDK"""
from setuptools import setup, find_packages

# Read the README file for long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements from requirements.txt if it exists
requirements = [
    "requests>=2.25.0",
    "pydantic>=1.8.0,<2.0.0",  # Using v1.x for broader compatibility
    "typing-extensions>=3.10.0"
]

setup(
    name="cqtech-metrics",
    version="0.1.0",
    author="CQTech",
    author_email="support@liudonghua123.com",  # Placeholder email
    description="A Python SDK for interacting with the CQTech Metrics OpenAPI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="http://github.com/liudonghua123/cqtech-metrics",
    project_urls={
        "Bug Reports": "http://github.com/liudonghua123/cqtech-metrics/issues",
        "Source": "http://github.com/liudonghua123/cqtech-metrics",
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
    packages=find_packages(include=['cqtech_metrics', 'cqtech_metrics.*']),
    install_requires=requirements,
    python_requires=">=3.7",
    keywords="cqtech, metrics, api, sdk",
    zip_safe=False,
)