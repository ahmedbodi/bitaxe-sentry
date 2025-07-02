from setuptools import setup, find_packages
import os
import sys

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import version from version.py
from bitaxe_sentry.sentry.version import __version__

setup(
    name="bitaxe_sentry",
    version=__version__,
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "requests",
        "apscheduler",
        "sqlmodel",
        "fastapi",
        "uvicorn",
        "python-dotenv",
        "jinja2",
    ],
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "bitaxe-sentry=sentry.__main__:main",
        ],
    },
) 