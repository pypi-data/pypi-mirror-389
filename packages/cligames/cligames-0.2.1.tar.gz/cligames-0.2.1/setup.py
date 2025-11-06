import setuptools

with open("cligames/version.py") as version_file:
    version = version_file.read().split('"')[1]
    assert len(version.split(".")) == 3

with open("README.md") as readme_file:
    long_description = readme_file.read()

setuptools.setup(
    name="cligames",
    author="Thomas Brier",
    version=version,
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    entry_points={"console_scripts": "cligames = cligames.cli:main"},
    install_requires=[
        "typer",
        "rich",
    ],
)
