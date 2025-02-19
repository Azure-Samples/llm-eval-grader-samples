# Create a package that will build and install the python codes from src directory.

from setuptools import setup, find_packages

package_name = "llmevalgrader"
version = "0.1.0"

setup(
    name=package_name,
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    version=version,
    description="A short description of the project.",
)
