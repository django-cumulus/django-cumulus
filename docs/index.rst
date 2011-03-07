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

To install the latest release (currently 1.0.1) from PyPI using pip::

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

    CUMULUS_USERNAME = 'YourUsername'
    CUMULUS_API_KEY = 'YourAPIKey'
    CUMULUS_CONTAINER = 'ContainerName'
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

Management command
******************

django-cumulus ships with a management command for synchronizing a local static media folder with a remote container. A few extra settings are required to make use of the command.

Add the following required settings::

     # the name of the container to sync with
    CUMULUS_STATIC_CONTAINER = 'MyStaticContainer'

    # whether to use rackspace's internal private network
    CUMULUS_USE_SERVICENET = False

    # a list of files to exclude from sync
    CUMULUS_FILTER_LIST = []

Invoke the management command::

    ./manage.py syncstatic

You can also perform a test run::

    ./manage.py syncstatic -t

For a full list of available options::

    ./manage.py help syncstatic

Requirements
************

* Django >= 1.1.4
* python-cloudfiles >= 1.7.8

Tests
*****

To run the tests, add ``cumulus`` to your ``INSTALLED_APPS`` and run::

    django-admin.py test cumulus

This will upload two very small files to your container and delete them when the tests have finished running.

Issues
******

To report issues, please use the issue tracker at https://github.com/richleland/django-cumulus/issues.
