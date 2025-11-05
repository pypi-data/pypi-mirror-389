"""
Setup script for Smart Clipboard Manager
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text() if readme_file.exists() else ""

# Read requirements
requirements = []
requirements_file = Path(__file__).parent / "requirements.txt"
if requirements_file.exists():
    with open(requirements_file) as f:
        requirements = f.read().strip().split('\n')
        requirements = [req.strip() for req in requirements if req.strip() and not req.startswith('#')]

setup(
    name="linux-clipboard-manager",
    version="1.1.1",
    author="Smart Clipboard Team",
    author_email="contact@smart-clipboard.com",
    description="A powerful clipboard manager with history, search, and smart categorization",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/krakujs/linux-clipboard-manager",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Utilities",
        "Topic :: Desktop Environment",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: POSIX :: Linux",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS :: MacOS X",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "flake8>=5.0.0",
            "black>=22.0.0",
            "isort>=5.10.0",
        ],
        "windows": [
            "pywin32>=305",
            "psutil>=5.9.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "smart-clipboard=src.__main__:main",
            "smart-clipboard-gui=src.__main__:show_ui_only",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="clipboard manager history copy paste productivity",
    project_urls={
        "Bug Reports": "https://github.com/krakujs/linux-clipboard-manager/issues",
        "Source": "https://github.com/krakujs/linux-clipboard-manager",
        "Documentation": "https://github.com/krakujs/linux-clipboard-manager/blob/main/README.md",
    },
)

