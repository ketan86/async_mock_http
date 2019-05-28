# -*- coding: utf-8 -*-
#
# This file were created by Python Boilerplate. Use boilerplate to start simple
# usable and best-practices compliant Python projects.
#
# Learn more about it at: http://github.com/fabiommendes/python-boilerplate/
#

import codecs
import os

from setuptools import find_packages, setup

# Save version and author to __meta__.py
version = open("VERSION").read().strip()
dirname = os.path.dirname(__file__)
path = os.path.join(dirname, "py_mock_http", "__meta__.py")
meta = (
    """# Automatically created. Please do not edit.
__version__ = '%s'
__author__ = 'Ketan Patel'
"""
    % version
)
with open(path, "w") as F:
    F.write(meta)

setup(
    # Basic info
    name="py-mock-http",
    version=version,
    author="Ketan Patel",
    author_email="ketan86ecer@gmail.com",
    url="",
    description="Mock http/https api calls with async functionality.",
    long_description=codecs.open("README.rst", "rb", "utf8").read(),
    # Classifiers (see https://pypi.python.org/pypi?%3Aaction=list_classifiers)
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Software Development :: Libraries",
    ],
    # Packages and dependencies
    package_dir={"": "py_mock_http"},
    packages=find_packages("py_mock_http"),
    install_requires=['Click', 'Sanic'],
    extras_require={"dev": ["python-boilerplate[dev]", "manuel"]},
    # Other configurations
    zip_safe=False,
    platforms="any",
)
