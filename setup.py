# ============================================================
# setup.py — Package setup for pip-installable mode (optional)
# ============================================================
from setuptools import setup, find_packages

setup(
    name="business-workflow-automation",
    version="1.0.0",
    description="A modular Python business workflow automation suite",
    author="Your Name",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "pandas>=2.0",
        "openpyxl>=3.1",
        "reportlab>=4.0",
        "schedule>=1.2",
        "python-dotenv>=1.0",
        "tqdm>=4.0",
        "colorama>=0.4",
        "ttkthemes>=3.2",
        "Pillow>=10.0",
    ],
    entry_points={
        "console_scripts": [
            "bizauto=main:main",
        ],
    },
)
