import os
from distutils.core import setup

f = open(os.path.join(os.path.dirname(__file__), 'README'))
long_description = f.read().strip()
f.close()

setup(
    name='django-cumulus',
    version='0.1',
    description='A Django app for working with Rackspace Cloud APIs.',
    long_description=long_description,
    author='Rich Leland',
    author_email='rich@richleland.com',
    url='https://bitbucket.org/richleland/django-cumulus/',
    download_url='https://bitbucket.org/richleland/django-cumulus/downloads/',
    packages=['cumulus'],
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