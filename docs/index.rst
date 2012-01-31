django-cumulus
==============

The aim of django-cumulus is to provide a set of tools to utilize Rackspace Cloud Files through Django. It currently includes a custom file storage class, CloudFilesStorage.

.. toctree::
   :maxdepth: 2
   :hidden:

   changelog

.. comment: split here

Installation
************

To install the latest release from PyPI using pip::

    pip install django-cumulus

To install the development version using pip::

    pip install -e git://github.com/richleland/django-cumulus.git#egg=django-cumulus

Add ``cumulus`` to ``INSTALLED_APPS``::

    INSTALLED_APPS = (
        ...
        'cumulus',
        ...
    )

Usage
*****

Add the following to your project's settings.py file::

    CUMULUS = {
        'USERNAME': 'YourUsername',
        'CUMULUS_API_KEY': 'YourAPIKey',
        'CUMULUS_CONTAINER': 'ContainerName'
    }
    DEFAULT_FILE_STORAGE = 'cumulus.storage.CloudFilesStorage'

Alternatively, if you don't want to set the DEFAULT_FILE_STORAGE, you can do the following in your models::

    from cumulus.storage import CloudFilesStorage

    cloudfiles_storage = CloudFilesStorage()

    class Photo(models.Model):
        image = models.ImageField(storage=cloudfiles_storage, upload_to='photos')
        alt_text = models.CharField(max_length=255)

Then access your files as you normally would through templates::

    <img src="{{ photo.image.url }}" alt="{{ photo.alt_text }}" />

Or through Django's default ImageField or FileField api::

    >>> photo = Photo.objects.get(pk=1)
    >>> photo.image.width
    300
    >>> photo.image.height
    150
    >>> photo.image.url
    http://c0000000.cdn.cloudfiles.rackspacecloud.com/photos/some-image.jpg

Static media
************

django-cumulus will work with Django's built-in ``collectstatic`` management command out of the box. You need to supply a few additional settings::

    CUMULUS = {
        'STATIC_CONTAINER': 'YourStaticContainer'
    }
    STATICFILES_STORAGE = 'cumulus.storage.CloudFilesStaticStorage'

Context Processor
*****************

django-cumulus includes an optional context_processor for accessing the full CDN_URL of any container files from your templates.

This is useful when you're using Cloud Files to serve you static media such as css and javascript and don't have access to the ``ImageField`` or ``FileField``'s url() convenience method.

Add ``cumulus.context_processors.cdn_url`` to your list of context processors in your project's settings.py file::


    TEMPLATE_CONTEXT_PROCESSORS = (
        ...
        'cumulus.context_processors.cdn_url',
        ...
    )

Now in your templates you can use {{ CDN_URL }} to output the full path to local media::

    <link rel="stylesheet" href="{{ CDN_URL }}css/style.css">

Management commands
*******************

syncstatic
----------

This management command synchronizes a local static media folder with a remote container. A few extra settings are required to make use of the command.

Add the following required settings::

    CUMULUS = {
        'STATIC_CONTAINER': 'MyStaticContainer', # the name of the container to sync with
        'USE_SERVICENET': False, # whether to use rackspace's internal private network
        'CUMULUS_FILTER_LIST': [] # a list of files to exclude from sync
    }

Invoke the management command::

    django-admin.py syncstatic

You can also perform a test run::

    django-admin.py syncstatic -t

For a full list of available options::

    django-admin.py help syncstatic

container_create
----------------

This management command creates a new container in Cloud Files.

Invoke the management command::

    django-admin.py container_create <container_name>

For a full list of available options::

    django-admin.py help container_create

container_delete
----------------

This management command deletes a container in Cloud Files.

Invoke the management command::

    django-admin.py container_delete <container_name>

For a full list of available options::

    django-admin.py help container_delete

container_info
--------------

This management command gathers information about containers in Cloud Files.

Invoke the management command::

    django-admin.py container_info [<container_one> <container two> ...]

For a full list of available options::

    django-admin.py help container_info

container_list
--------------

This management command lists all the items in a Cloud Files container to stdout.

Invoke the management command::

    django-admin.py container_list <container_name>

For a full list of available options::

    django-admin.py help container_list

Settings
********

Below are the default settings::

    CUMULUS = {
        'API_KEY': None,
        'AUTH_URL': 'us_authurl',
        'CNAMES': None,
        'CONTAINER': None,
        'SERVICENET': False,
        'TIMEOUT': 5,
        'TTL': 600,
        'USE_SSL': False,
        'USERNAME': None,
        'STATIC_CONTAINER': None,
        'FILTER_LIST': []
    }

API_KEY
-------

**Required.** This is your API access key. You can obtain it from the `Rackspace Management Console`_.

.. _Rackspace Management Console: https://manage.rackspacecloud.com/APIAccess.do

AUTH_URL
--------

Set this to the region your account is in. Valid values are ``us_authurl`` (default) and ``uk_authurl``.

CNAMES
------

A mapping of ugly Rackspace URLs to CNAMEd URLs. Example::

    CUMULUS = {
        'CNAMES': {
            'http://c3417812.r12.cf0.rackcdn.com': 'http://media.mysite.com'
        }
    }

CONTAINER
---------

**Required.** The name of the container you want files to be uploaded to.

FILTER_LIST
-----------

A list of items to exclude when using the ``syncstatic`` management command. Defaults to an empty list.

SERVICENET
----------

Specifies whether to use Rackspace's private network (True) or not (False). If you host your sites on Rackspace, you should set this to True in production as you will not incur data transfer fees between your server(s) and Cloud Files on the private network.

STATIC_CONTAINER
----------------

When using Django's ``collectstatic`` or django-cumulus's ``syncstatic`` command, this is the name of the container you want static files to be uploaded to.

TIMEOUT
-------

The timeout to use when attempting connections to Cloud Files. Defaults to 5 (seconds).

TTL
---

Currently unused.

USE_SSL
-------

Whether or not to retrieve the container URL as http (False) or https (True).

USERNAME
--------

**Required.** This is your API username. You can obtain it from the `Rackspace Management Console`_.

.. _Rackspace Management Console: https://manage.rackspacecloud.com/APIAccess.do

Requirements
************

* Django>=1.2
* python-cloudfiles >= 1.7.9

Tests
*****

To run the tests, clone `the github repo`_, `install tox`_ and invoke ``tox`` from the clone's root. This will upload two very small files to your container and delete them when the tests have finished running.

.. _the github repo: https://github.com/richleland/django-cumulus
.. _install tox: http://tox.readthedocs.org/en/latest/index.html

Issues
******

To report issues, please use the issue tracker at https://github.com/richleland/django-cumulus/issues.
