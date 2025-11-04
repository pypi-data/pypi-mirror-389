"""
Setup configuration for rail-score Python SDK
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="rail-score",
    version="1.0.1",
    author="Responsible AI Labs",
    author_email="support@responsibleailabs.ai",
    description="Official Python SDK for RAIL Score API - Responsible AI evaluation and generation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Responsible-AI-Labs/rail-score",
    project_urls={
        "Documentation": "https://responsibleailabs.ai/docs",
        "Source": "https://github.com/Responsible-AI-Labs/rail-score",
        "Bug Reports": "https://github.com/Responsible-AI-Labs/rail-score/issues",
    },
    packages=find_packages(exclude=["tests", "examples"]),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.28.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=22.0.0",
            "mypy>=0.990",
            "flake8>=5.0.0",
        ],
    },
    keywords="rail responsible-ai ai-safety content-evaluation ai-ethics compliance",
    package_data={
        "rail_score": ["py.typed"],
    },
)
