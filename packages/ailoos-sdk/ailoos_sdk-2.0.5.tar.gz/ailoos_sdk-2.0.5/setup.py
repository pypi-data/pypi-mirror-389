"""
Setup script for Ailoos Python SDK
"""

from setuptools import setup, find_packages
import os

# Read README
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="ailoos-sdk",
    version="2.0.5",
    author="Ailoos Team",
    author_email="team@ailoos.ai",
    description="Python SDK for Ailoos distributed AI platform",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ailoos/ailoos-python-sdk",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: Other/Proprietary License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="ailoos ai distributed machine-learning sdk api",
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "isort>=5.10.0",
            "flake8>=4.0.0",
            "mypy>=0.950",
            "sphinx>=5.0.0",
            "sphinx-rtd-theme>=1.0.0",
        ],
        "gpu": [
            "torch>=2.0.0",
            "torchvision>=0.15.0",
            "torchaudio>=2.0.0",
        ],
        "quantum": [
            "qiskit>=0.44.0",
            # qiskit-aer removed due to compilation issues on macOS ARM64
            # Use cloud simulators (IBM Quantum, Amazon Braket) instead
        ],
        "quantum-full": [
            "qiskit>=0.44.0",
            "qiskit-aer>=0.12.0; sys_platform != 'darwin' or platform_machine != 'arm64'",
            # Only install qiskit-aer on platforms that support it
        ],
        "blockchain": [
            "web3>=6.0.0",
            "eth-account>=0.8.0",
        ],
        "p2p": [
            "libp2p>=0.0.1",
            "ipfshttpclient>=0.8.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "ailoos=ailoos_sdk.cli:main",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/ailoos/ailoos-python-sdk/issues",
        "Source": "https://github.com/ailoos/ailoos-python-sdk",
        "Documentation": "https://docs.ailoos.ai/python-sdk/",
        "Discord": "https://discord.gg/ailoos",
    },
)