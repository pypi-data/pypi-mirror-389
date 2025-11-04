from setuptools import setup, find_packages

setup(
    name="ismycomputeronfire",
    version="0.1",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "ismycomputeronfire = ismycomputeronfire.cli:main",
        ],
    },
)
