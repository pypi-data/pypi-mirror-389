from setuptools import setup, find_packages

setup(
    name="pygeist_client",
    version="0.0.1",
    packages=find_packages(include=["pygeist_client*"]),
    python_requires=">=3.10",
    install_requires=[],
    include_package_data=True,
    description="Pygeist client package",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
)
