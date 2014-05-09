django-cumulus
==============

``django-cumulus`` provides a set of tools to utilize the
`python-swiftclient`_ and `Rackspace Cloud Files API`_ from Django. It
includes a custom file storage class, SwiftclientFilesStorage.

More documentation about the usage and installation of ``django-cumulus``
can be found on `django-cumulus.readthedocs.org`_.

The source code for ``django-cumulus`` can be found and contributed to on
`github.com/django-cumulus/django-cumulus`_. There you can also `file issues`_.

To find out what's new in this version of ``django-cumulus``, please see
`the changelog`_


Core Team
=========

This library is maintained by:

* Ferrix Hovi (@ferrix)
* Thomas Schreiber (@rizumu)

They will be able to answer questions, give architectural guidance and merge
pull requests.


Quick Installation Guide
========================

Please visit `django-cumulus.readthedocs.org`_ for the full documentation.

* Install Django Cumulus with your favorite Python package manager::

    pip install django-cumulus

* To install the `in-development version`_ of Django Cumulus::

    pip install django-cumulus==dev


* Add ``'cumulus'`` to the ``INSTALLED_APPS`` setting in your
  project's ``settings.py``::

    INSTALLED_APPS = (
        ...
        'cumulus',
        ...
    )

* Add the following to your project's ``settings.py`` file::

    CUMULUS = {
        'USERNAME': 'YourUsername',
        'API_KEY': 'YourAPIKey',
        'CONTAINER': 'ContainerName',
        'PYRAX_IDENTITY_TYPE': 'rackspace',
    }
    DEFAULT_FILE_STORAGE = 'cumulus.storage.SwiftclientStorage'

The ``PYRAX_IDENTITY_TYPE`` parameter can either be ``rackspace`` or ``keystone``
depending on whether you use Rackspace or OpenStack respectively.


.. _github.com/django-cumulus/django-cumulus: https://github.com/django-cumulus/django-cumulus/
.. _django-cumulus.readthedocs.org: http://django-cumulus.readthedocs.org/
.. _python-swiftclient: https://pypi.python.org/pypi/python-swiftclient/
.. _Rackspace Cloud Files API: http://www.rackspace.com/cloud/files/api/
.. _file issues: https://github.com/django-cumulus/django-cumulus/issues/
.. _in-development version: https://github.com/django-cumulus/django-cumulus/tarball/master#egg=django-cumulus-dev
.. _the changelog: http://django-cumulus.readthedocs.org/en/latest/changelog.html
