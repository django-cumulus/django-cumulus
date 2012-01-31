import os
from setuptools import setup, find_packages

# Use the docstring of the __init__ file to be the description
short_description = " ".join(__import__('cumulus').__doc__.splitlines()).strip()

# Use part of the sphinx docs index for the long description
doc_dir = os.path.join(os.path.dirname(__file__), 'docs')
index_filename = os.path.join(doc_dir, 'index.rst')
long_description = open(index_filename).read().split('split here', 1)[1]

setup(
    name = "django-cumulus",
    version = __import__('cumulus').get_version().replace(' ', '-'),
    packages = find_packages(),
    install_requires = ['python-cloudfiles>=1.7.9.3'],

    author = "Rich Leland",
    author_email = "rich@richleland.com",
    license = 'BSD',
    description = short_description,
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
