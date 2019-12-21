#!/usr/bin/env python

from os.path import exists, join
import re
from setuptools import setup

version = re.findall(
    r"__version__ = \"([.0-9]+)\"", open(join("unification", "__init__.py"), "r").read()
)[0]

setup(
    name="logical-unification",
    version=version,
    description="Logical unification in Python",
    url="http://github.com/brandonwillard/unification/",
    maintainer="Brandon T. Willard",
    maintainer_email="brandonwillard@gmail.com",
    license="BSD",
    keywords="unification logic-programming dispatch",
    packages=["unification"],
    install_requires=open("requirements.txt").read().split("\n"),
    long_description=(open("README.rst").read() if exists("README.rst") else ""),
    zip_safe=False,
)
