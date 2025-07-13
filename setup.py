"""Setup configuration for Lamish Projection Engine."""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="lamish-projection-engine",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A high-dimensional embedding transformation system with visual feedback",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/lamish-projection-engine",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=[
        "numpy>=1.24.0",
        "scipy>=1.10.0",
        "scikit-learn>=1.3.0",
        "pandas>=2.0.0",
        "matplotlib>=3.7.0",
        "seaborn>=0.12.0",
        "click>=8.1.0",
        "rich>=13.0.0",
        "psycopg2-binary>=2.9.0",
        "sqlalchemy>=2.0.0",
        "pgvector>=0.2.0",
        "python-dotenv>=1.0.0",
        "pydantic>=2.0.0",
        "tqdm>=4.65.0",
    ],
    entry_points={
        "console_scripts": [
            "lpe=lamish_projection_engine.cli.main:cli",
        ],
    },
)