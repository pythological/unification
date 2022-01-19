#!/usr/bin/env python
from os.path import exists

from setuptools import setup

import versioneer

setup(
    name="logical-unification",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description="Logical unification in Python",
    url="http://github.com/pythological/unification/",
    maintainer="Brandon T. Willard",
    maintainer_email="brandonwillard+unification@gmail.com",
    license="BSD",
    keywords="unification logic-programming dispatch",
    packages=["unification"],
    install_requires=[
        "toolz",
        "multipledispatch",
    ],
    long_description=(open("README.md").read() if exists("README.md") else ""),
    long_description_content_type="text/markdown",
    zip_safe=False,
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: Software Development :: Libraries",
    ],
)
