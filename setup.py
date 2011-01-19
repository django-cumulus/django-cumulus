import os, distribute_setup
distribute_setup.use_setuptools()
from setuptools import setup, find_packages

doc_dir = os.path.join(os.path.dirname(__file__), 'docs')
index_filename = os.path.join(doc_dir, 'index.rst')
long_description = open(index_filename).read().split('split here', 1)[1]

setup(
    name = "django-cumulus",
    version = "0.3.6",
    packages = find_packages(),

    author = "Rich Leland",
    author_email = "rich@richleland.com",
    license = 'BSD',
    description = "An interface to Rackspace Cloud Files through Django.",
    long_description = long_description,
    url = "https://github.com/richleland/django-cumulus/",
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Framework :: Django',
    ]
)
