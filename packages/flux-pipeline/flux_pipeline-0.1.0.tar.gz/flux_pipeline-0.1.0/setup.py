from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="flux-pipeline",
    version="0.1.0",
    description="A simple framework for building composable, asynchronous workflows",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Flux Team",
    url="https://github.com/yourusername/flux-pipeline",
    packages=find_packages(exclude=["tests", "tests.*"]),
    py_modules=["flux"] if not find_packages() else [],
    python_requires=">=3.8",
    install_requires=[
        # No external dependencies - uses Python stdlib only
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)