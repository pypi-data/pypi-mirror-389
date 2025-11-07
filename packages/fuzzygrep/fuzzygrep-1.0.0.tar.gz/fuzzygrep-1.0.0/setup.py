"""Setup script for fuzzygrep package."""

from pathlib import Path

from setuptools import find_packages, setup

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Core requirements
core_requirements = [
    "prompt_toolkit>=3.0.0",
    "rapidfuzz>=3.0.0",
    "rich>=13.0.0",
    "typer>=0.9.0",
    "cachetools>=5.0.0",
]

# Optional requirements
optional_requirements = {
    "enhanced": [
        "ijson>=3.2.0",
        "pandas>=2.0.0",
    ],
    "dev": [
        "pytest>=7.4.0",
        "pytest-cov>=4.1.0",
        "pytest-mock>=3.11.0",
        "black>=23.0.0",
        "flake8>=6.0.0",
        "mypy>=1.5.0",
        "isort>=5.12.0",
    ],
}

# All optional requirements
optional_requirements["all"] = sum(optional_requirements.values(), [])

setup(
    name="fuzzygrep",
    version="1.0.0",
    author="Anggi Ananda",
    description="Interactive fuzzy search for JSON and CSV files",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/anggiAnand/fuzzygrep",
    packages=find_packages(exclude=["tests", "tests.*"]),
    install_requires=core_requirements,
    extras_require=optional_requirements,
    entry_points={
        "console_scripts": [
            "fuzzygrep=fuzzygrep.cli:app",
        ],
    },
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Filters",
        "Topic :: Utilities",
    ],
    keywords="fuzzy search json csv cli interactive",
)
