"""
Setup orch_serv
"""
import os
import pathlib
import re
from typing import Optional

from setuptools import setup

LIB_NAME = "my_utilities"
HERE = pathlib.Path(__file__)
DESCRIPTION = """
Library with helper functions and classes
"""


def get_version() -> Optional[str]:
    """
      Method for getting the version of the library from the init file
    :requirements: version must be specified separately
        :good: __version__ = '0.0.1'
        :bad: __version__, __any_variable__ = '0.0.1', 'any_value'
    :return: version lib
    """
    root_lib = pathlib.Path(__file__).parent / LIB_NAME
    txt = (root_lib / "__init__.py").read_text("utf-8")
    txt = txt.replace("'", '"')
    try:
        version = re.findall(r'^__version__ = "([^"]+)"\r?$', txt, re.M)[0]
        return version
    except IndexError:
        raise RuntimeError("Unable to determine version.") from Exception


def get_packages():
    """
    Method for getting packages used in the lib
    """
    ignore = ["__pycache__"]

    list_sub_folders_with_paths = [
        x[0].replace(os.sep, ".")
        for x in os.walk(LIB_NAME)
        if x[0].split(os.sep)[-1] not in ignore
    ]
    return list_sub_folders_with_paths


def get_long_description() -> str:
    """
    Get long description for setup function
    :return:  description
    """
    path_readme_pypi = pathlib.Path("README_PYPI.md")
    path_readme = pathlib.Path("README_PYPI.md")
    if path_readme_pypi.exists():
        with open(path_readme_pypi, "r", encoding="utf8") as file:
            return file.read()
    elif path_readme.exists():
        with open(path_readme, "r", encoding="utf8") as file:
            return file.read()
    else:
        return DESCRIPTION


setup(
    name=LIB_NAME,
    version=get_version(),
    description=DESCRIPTION,
    author="Denis Shchutkiy",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    author_email="denisshchutskyi@gmail.com",
    url="https://github.com/Shchusia/MyUtils",
    packages=get_packages(),
    keywords=["pip", LIB_NAME],
    python_requires=">=3.7",
    install_requires=["pydantic==1.9.0"],
)
