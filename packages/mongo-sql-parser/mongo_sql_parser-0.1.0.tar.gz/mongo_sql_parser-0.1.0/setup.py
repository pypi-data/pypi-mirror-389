"""
Setup configuration for mongo-sql-parser package
"""
from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8') if (this_directory / "README.md").exists() else ""

# Read version from package
version = {}
with open('mongo_sql_parser/__init__.py', 'r') as f:
    for line in f:
        if line.startswith('__version__'):
            exec(line, version)
            break

setup(
    name="mongo-sql-parser",
    version=version.get('__version__', '0.1.0'),
    author="Sachin H M",
    author_email="sachinhm22197@gmail.com",
    description="A library for converting SQL queries to MongoDB aggregation pipelines",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://pypi.org/project/mongo-sql-parser/",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Database",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.7",
    install_requires=[
        "sqlglot>=10.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    keywords="mongodb sql parser query converter aggregation pipeline",
    project_urls={
        "PyPI": "https://pypi.org/project/mongo-sql-parser/",
        "Documentation": "https://pypi.org/project/mongo-sql-parser/",
    },
)

