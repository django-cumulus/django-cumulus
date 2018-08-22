django-cumulus |version|
========================


``django-cumulus`` provides a set of tools to utilize the
`python-swiftclient`_ and `Rackspace Cloud Files API`_ from Django. It
includes a custom file storage class, CumulusFilesStorage.

More documentation about the usage and installation of ``django-cumulus``
can be found on `django-cumulus.readthedocs.org`_.

The source code for ``django-cumulus`` can be found and contributed to on
`github.com/django-cumulus/django-cumulus`_. There you can also `file issues`_.

This documentation applies to the version |version| of django-cumulus.
To find out what's new in this version, please see `the changelog`_

.. toctree::
   :maxdepth: 2
   :hidden:

   changelog


Installation
************

To install the latest release from PyPI using pip::

    pip install django-cumulus

To install the development version using pip::

    pip install -e git://github.com/django-cumulus/django-cumulus.git#egg=django-cumulus

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
        'API_KEY': 'YourAPIKey',
        'CONTAINER': 'ContainerName',
        'PYRAX_IDENTITY_TYPE': 'rackspace',
    }
    DEFAULT_FILE_STORAGE = 'cumulus.storage.CumulusStorage'

The ``PYRAX_IDENTITY_TYPE`` parameter can either be ``rackspace`` or ``keystone``
depending on whether you use Rackspace or OpenStack respectively.

Alternatively, if you don't want to set the DEFAULT_FILE_STORAGE, you
can do the following in your models::

    from cumulus.storage import CumulusStorage

    swiftclient_storage = CumulusStorage()

    class Photo(models.Model):
        image = models.ImageField(storage=swiftclient_storage, upload_to='photos')
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


Static files
************

``django-cumulus`` will work with Django's built-in ``collectstatic``
management command out of the box. You need to supply a few additional
settings::

    CUMULUS = {
        'STATIC_CONTAINER': 'YourStaticContainer'
    }
    STATICFILES_STORAGE = 'cumulus.storage.CumulusStaticStorage'


Context Processor
*****************

``django-cumulus`` includes an optional context_processor for accessing
the full CDN_URL of any container files from your templates.

This is useful when you're using Cumulus to serve you static media
such as css and javascript and don't have access to the ``ImageField``
or ``FileField``'s url() convenience method.

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


syncfiles
----------


This management command synchronizes a local static or media folder with
respective remote containers. A few extra settings are required to
make use of the command.

Add the following required settings::

    CUMULUS = {
        'CONTAINER': 'MyMediaContainer', # the name of the media container to sync with
        'STATIC_CONTAINER': 'MyStaticContainer',  # the name of the static container to sync with
        'SERVICENET': False,  # whether to use rackspace's internal private network
    }

Invoke the management command::

    django-admin.py syncfiles --static

    django-admin.py syncfiles --media

You can also perform a test run::

    django-admin.py syncfiles --test-run

For a full list of available options::

    django-admin.py help syncfiles


container_create
----------------

This management command creates a new container.

Invoke the management command::

    django-admin.py container_create <container_name>

For a full list of available options::

    django-admin.py help container_create


container_delete
----------------

This management command deletes a container.

Invoke the management command::

    django-admin.py container_delete <container_name>

For a full list of available options::

    django-admin.py help container_delete


container_info
--------------

This management command gathers information about containers:

Invoke the management command::

    django-admin.py container_info [<container_one> <container two> ...]

For a full list of available options::

    django-admin.py help container_info


container_list
--------------

This management command lists all the items in a container to stdout.

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
        'AUTH_VERSION': '1.0',
        'AUTH_TENANT_NAME': None,
        'AUTH_TENANT_ID': None,
        'REGION': 'DFW',
        'CNAMES': None,
        'CONTAINER': None,
        'CONTAINER_URI': None,
        'CONTAINER_SSL_URI': None,
        'SERVICENET': False,
        'TIMEOUT': 5,
        'TTL': 86400,
        'USE_SSL': False,
        'USERNAME': None,
        'STATIC_CONTAINER': None,
        'INCLUDE_LIST': [],
        'EXCLUDE_LIST': [],
        'HEADERS': {},
        'GZIP_CONTENT_TYPES': [],
        'USE_PYRAX': True,
        'PYRAX_IDENTITY_TYPE': None,
    }


API_KEY
-------

**Required.** This is your API access key. You can obtain it from the `Rackspace Management Console`_.

.. _Rackspace Management Console: https://manage.rackspacecloud.com/APIAccess.do


AUTH_URL
--------

Set this to the region your account is in. Valid values are ``us_authurl`` (default) and ``uk_authurl``,
or if you are not using rackspace, your swift auth url.


AUTH_VERSION
------------

OpenStack auth version to use with the ``swiftclient``. Does not apply to ``pyrax`` based connections.


AUTH_TENANT_NAME and AUTH_TENANT_ID
-----------------------------------

Required if you are using your own Openstack Swift rather than rackspaces.


REGION
------

Set this to the regional datacenter to connect to. Valid values are ``DFW`` (default) ``ORD`` and ``LON``.


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


CONTAINER_URI and CONTAINER_SSL_URI
-----------------------------------

Specified URLs for the container will be used instead of looking up
the URL directly from the container.


INCLUDE_LIST
------------

A list of glob-style regular expresions to match files or directories
to include when using the ``syncfiles`` management command. Defaults
to an empty list.


EXCLUDE_LIST
------------

A list of glob-style regular expresions to match files or directories
to exclude when using the ``syncfiles`` management command. Defaults
to an empty list.


SERVICENET
----------

Specifies whether to use Rackspace's private network (True) or not
(False). If you host your sites on Rackspace, you should set this to
True in production as you will not incur data transfer fees between
your server(s) and the cdn on the private network.


STATIC_CONTAINER
----------------

When using Django's ``collectstatic`` or ``django-cumulus``'s
``syncfiles --static`` command, this is the name of the container you
want static files to be uploaded to.

TIMEOUT
-------

The timeout to use when attempting connections over swiftclient. Defaults to 5 (seconds).


TTL
---

The maximum time (in seconds) until a copy of one of your files distributed into the CDN is re-fetched from your container. Defaults to 86400 (seconds) (24h), the default set by pyrax.

Note: After changing TTL, caching servers may not recognize the new TTL for this container until the previous TTL expires.


USE_SSL
-------

Whether or not to retrieve the container URL as http (False) or https (True).


USERNAME
--------


**Required.** This is your API username. You can obtain it from the `Rackspace Management Console`_.


HEADERS
-------

Set headers based on a regular expression in the file name. This can be used to allow Firefox to
access webfonts across domains::

   CUMULUS = {
       'HEADERS': (
           (r'.*\.(eot|otf|woff|ttf)$', {
               'Access-Control-Allow-Origin': '*'
           }),
       )
   }


GZIP_CONTENT_TYPES
------------------

Set which content types must be gzipped before sent to the cloud::

    CUMULUS = {
        'GZIP_CONTENT_TYPES': ['image/jpeg', 'text/css'],
    }

The files matching these content types would be gzipped and will have *gzip*
content-encoding.


USE_PYRAX
---------

If True, will use the Official Rackspace's Python SDK for OpenStack/Rackspace
APIs. Defaults to True.

Note: Currently this is required even to use your own OpenStack Swift setup.


PYRAX_IDENTITY_TYPE
-------------------

Pyrax supports different identity types. For now (version 1.4.5 of Pyrax),
there are two types available: *rackspace* and *keystone*.

You **can** specify it through cumulus settings and if you don't, you **must**
do it through other means (like environment variables or configuration files,
see Pyrax documentation for more details).


Requirements
************

* Django>=1.4
* pyrax>=1.9,<1.10


Tests
*****

To run the tests, clone `the github repo`_, `install tox`_ and invoke ``tox`` from the clone's root. This will upload two very small files to your container and delete them when the tests have finished running.


Issues
******

The source code for ``django-cumulus`` can be found and contributed to on
`github.com/django-cumulus/django-cumulus`_. There you can also `file issues`_.


Changelog
*********

To find out what's new in this version of django-cumulus, please see
`the changelog`_


.. _github.com/django-cumulus/django-cumulus: https://github.com/django-cumulus/django-cumulus/
.. _python-swiftclient: https://pypi.python.org/pypi/python-swiftclient/
.. _Rackspace Cloud Files API: http://www.rackspace.com/cloud/files/api/
.. _file issues: https://github.com/django-cumulus/django-cumulus/issues/
.. _in-development version: https://github.com/django-cumulus/django-cumulus/tarball/master#egg=django-cumulus-dev
.. _the changelog: http://django-cumulus.readthedocs.org/en/latest/changelog.html
.. _the github repo: https://github.com/django-cumulus/django-cumulus
.. _install tox: http://tox.readthedocs.org/en/latest/index.html
.. _Rackspace Management Console: https://manage.rackspacecloud.com/APIAccess.do
.. _django-cumulus.readthedocs.org: http://django-cumulus.readthedocs.org/
