"""Setup script for CSF package.

CSF - Cryptographic Security Framework
Inventor: Jeremy Noverraz (1988 - 2025) based on an idea by Ivàn Àvalos AND JCZD (engrenage.ch)
"""

from setuptools import setup, find_packages

# Read README for long description (prefer PyPI-specific version)
try:
    with open("README_PYPI.md", "r", encoding="utf-8") as fh:
        long_description = fh.read()
except FileNotFoundError:
    try:
        with open("README.md", "r", encoding="utf-8") as fh:
            long_description = fh.read()
    except FileNotFoundError:
        long_description = """CSF-Crypto: Post-Quantum Cryptographic Security Framework

Military-grade post-quantum cryptographic system integrating fractal geometry with semantic keys. 
Resistant to both classical and quantum attacks (Shor's and Grover's algorithms).

Features:
- NIST PQC standards (CRYSTALS-Kyber, Dilithium, SPHINCS+)
- Fractal-based message encoding
- Dual-layer key system (mathematical + semantic)
- Constant-time operations for side-channel protection
- Simple API like standard cryptographic libraries

Installation: pip install csf-crypto
Documentation: https://github.com/iyotee/csf
"""

setup(
    name="csf-crypto",
    version="1.0.16",
    author="Jeremy Noverraz (based on an idea by Ivàn Àvalos AND JCZD (engrenage.ch))",
    maintainer="Jeremy Noverraz",
    author_email="",
    description="Post-quantum cryptographic framework with fractal encoding and semantic keys - resistant to quantum attacks",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/iyotee/csf",
    packages=find_packages(exclude=["tests", "tests.*", "venv", "venv.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Security :: Cryptography",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
    python_requires=">=3.9",
    install_requires=[
        "numpy>=1.24.0",
        "scipy>=1.10.0",
        "matplotlib>=3.7.0",
        "msgpack>=1.0.0",
    ],
    extras_require={
        "pqc": [
            # Note: These packages may not be available on PyPI
            # CSF includes fallback implementations if these are not installed
            # "pykyber>=0.1.0",  # Optional: CRYSTALS-Kyber (may not exist on PyPI)
            # "python-pqc>=0.1.0",  # Optional: Additional PQC schemes (may not exist on PyPI)
            # "pysphincs>=0.1.0",  # Optional: SPHINCS+ (may not exist on PyPI)
        ],
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "mypy>=1.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "csf-keygen=csf.tools.keygen:main",
            "csf-benchmark=csf.tools.benchmark:main",
        ],
    },
    keywords="cryptography, post-quantum, fractal, encryption, security, NIST PQC",
    project_urls={
        "Documentation": "https://github.com/iyotee/csf",
        "Source": "https://github.com/iyotee/csf",
        "GitHub": "https://github.com/iyotee/csf",
    },
    include_package_data=True,
    zip_safe=False,
)

