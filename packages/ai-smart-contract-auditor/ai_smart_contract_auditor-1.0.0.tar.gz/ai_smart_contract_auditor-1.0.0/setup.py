"""Setup configuration for AI Smart Contract Auditor"""
from setuptools import setup, find_packages
import os

# Read long description from README
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
try:
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]
except FileNotFoundError:
    # Fallback to hardcoded requirements if file not found during build
    requirements = [
        "anthropic>=0.39.0",
        "chromadb>=0.5.23",
        "pytest>=8.3.4",
        "pytest-cov>=6.0.0",
        "pytest-xdist>=3.6.1",
        "black>=24.10.0",
        "isort>=5.13.2",
        "flake8>=7.1.1",
        "pylint>=3.3.2",
        "bandit>=1.8.0",
        "safety>=3.2.11",
        "cosmic-ray>=8.3.9",
    ]

setup(
    name="ai-smart-contract-auditor",
    version="1.0.0",
    author="AI Smart Contract Auditor Team",
    author_email="contact@example.com",
    description="AI-powered smart contract security auditor with parallel processing",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jw3b-dev/AI-Smart-Contract-Auditor",
    project_urls={
        "Bug Tracker": "https://github.com/jw3b-dev/AI-Smart-Contract-Auditor/issues",
        "Documentation": "https://github.com/jw3b-dev/AI-Smart-Contract-Auditor#readme",
        "Source Code": "https://github.com/jw3b-dev/AI-Smart-Contract-Auditor",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Security",
        "Topic :: Software Development :: Quality Assurance",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "ai-auditor=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.json", "*.yaml", "*.yml"],
    },
    keywords="smart-contract security audit blockchain ethereum solidity",
    zip_safe=False,
)
