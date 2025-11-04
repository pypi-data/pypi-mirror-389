from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="smart-code-analyzer",
    version="0.5.0",
    author="Julio",
    description="Deep source code analysis and documentation tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/thinmanj/code-analyzer",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Quality Assurance",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "click>=8.0.0",
        "pyyaml>=6.0",
        "radon>=6.0.0",
        "rich>=13.0.0",
        "tqdm>=4.65.0",
    ],
    extras_require={
        "full": [
            "bandit>=1.7.0",
            "pylint>=2.17.0",
            "jedi>=0.19.0",
        ],
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "code-analyzer=code_analyzer.cli:main",
        ],
    },
)
