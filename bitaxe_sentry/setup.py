from setuptools import setup, find_packages

setup(
    name="bitaxe_sentry",
    version="0.1.0",
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