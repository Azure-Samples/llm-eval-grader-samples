# Create a package that will build and install the python codes from src directory.

from setuptools import setup, find_packages

setup(
    name='llminspect',
    version='0.1',
    packages=find_packages(where='llminspect'),
    package_dir={"": "llminspect"},
)
