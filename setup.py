import os, distribute_setup
distribute_setup.use_setuptools()
from setuptools import setup, find_packages

f = open(os.path.join(os.path.dirname(__file__), 'docs/index.rst'))
long_description = f.read().strip()
f.close()

setup(
    name = "django-cumulus",
    version = "0.2",
    packages = find_packages(),
    
    author = "Rich Leland",
    author_email = "rich@richleland.com",
    description = "An interface to Rackspace Cloud Files through Django.",
    long_description = long_description,
    url = "http://bitbucket.org/richleland/django-cumulus/",
    download_url = "http://bitbucket.org/richleland/django-cumulus/get/0.2.tar.gz",
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Framework :: Django',
    ]
)
