#!/usr/bin/env python
import os

from setuptools import setup, find_packages


setup(
    name="django-cumulus",
    version=__import__("cumulus").get_version().replace(" ", "-"),
    packages=find_packages(),
    install_requires=[
        "pyrax>=1.9,<1.10",
    ],
    author="Ferrix Hovi, Thomas Schreiber",
    license="BSD",
    description="An interface to python-swiftclient and rackspace cloudfiles API from Django.",
    long_description=open("README.rst").read(),
    url="https://github.com/django-cumulus/django-cumulus/",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Framework :: Django",
    ]
)
