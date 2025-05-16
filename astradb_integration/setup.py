from setuptools import setup, find_packages

setup(
    name="astradb_integration",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "agno",
        "astrapy",
        "cassio",
    ],
)