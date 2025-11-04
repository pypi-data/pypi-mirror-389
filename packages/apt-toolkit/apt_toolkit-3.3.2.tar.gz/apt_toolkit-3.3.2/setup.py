"""
Setup configuration for APT Toolkit
"""

from pathlib import Path

from setuptools import setup, find_packages

BASE_DIR = Path(__file__).parent
README = (BASE_DIR / "README.md").read_text(encoding="utf-8")

setup(
    name="apt-toolkit",
    version="3.3.2",
    description="Advanced Persistent Threat offensive toolkit for authorized penetration testing",
    author="Security Research Team",
    long_description=README,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "rich>=13.7,<14",
        "click>=8.0.0",
        "pytest>=7.0.0",
        "pytest-cov>=4.0.0",
        "dnspython>=2.0.0",
        "openai>=1.0.0",
        "requests>=2.25.0",
        "cryptography>=3.4.0",
        "pycryptodome>=3.10.0",
        "colorama>=0.4.0",
        "psutil>=5.8.0",
    ],
    entry_points={
        'console_scripts': [
            'apt-toolkit=apt_toolkit.interactive_shell:main',
            'apt=apt_toolkit.interactive_shell:main',
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Security",
        "Topic :: Education",
    ],
)
