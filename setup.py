#!/usr/bin/env python
import os
import versioneer

from setuptools import setup, find_packages

versioneer.VCS = 'git'
versioneer.versionfile_source = 'cumulus/_version.py'
versioneer.versionfile_build = None
versioneer.tag_prefix = ''
versioneer.parentdir_prefix = 'django-cumulus-'

setup(
    name = "django-cumulus",
    version = versioneer.get_version(),
    cmdclass = versioneer.get_cmdclass(),
    packages = find_packages(),
    install_requires = [
        "pyrax>=1.9,<1.10",
    ],
    author = "Ferrix Hovi, Thomas Schreiber",
    license = "BSD",
    description = "An interface to python-swiftclient and rackspace cloudfiles API from Django.",
    long_description = open("README.rst").read(),
    url = "https://github.com/django-cumulus/django-cumulus/",
    classifiers = [
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Framework :: Django",
    ]
)
