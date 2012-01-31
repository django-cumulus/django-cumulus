changelog
=========

Version 1.0.5, 30 January 2012
******************************

* Added CloudFilesStaticStorage subclass for collectstatic compatability
* Added thread-safe CloudFilesStorage subclass
* Added four new management commands
* Added creation of pseudo-directories
* Numerous bug fixes and code cleanups
* Created new example project based on Django 1.3
* Updated tox configuration
* Bumped python-cloudfiles requirement to 1.7.9.3

Version 1.0.4, 02 September 2011
********************************

* Added USE_SSL setting, which outputs SSL URLs. Thanks to @whafro for the nudge.

Version 1.0.3, 07 June 2011
***************************

* Added context processor for using container URLs in templates for statically synced media

Version 1.0.2, 05 May 2011
**************************

* Added ``CUMULUS_CNAMES`` setting to map cloudfiles URIs to CNAMEs

Version 1.0, 03 March 2011
**************************

* OK, srsly. Time for 1.0.
* Fixed content_type bug
* Bumped python-cloudfiles requirement to 1.7.8

Version 0.3.6, 19 January 2011
******************************

* Added containerinfo management command
* Properly integrated ``CUMULUS_USE_SERVICENET`` into storage backend
* Resolved `issue 5`_, adding ``CUMULUS_TIMEOUT`` setting to specify default connection timeout
* Restructured tests to work properly with django-nose

.. _issue 5: https://github.com/richleland/django-cumulus/issues/issue/5

Version 0.3.5, 07 January 2011
******************************

* Fixed glaring issue affecting Django > 1.1.x (see http://bit.ly/e8YhcR)
* Removed reliance on physical files for tests
* Added tox config to test multiple versions of Python and Django

Version 0.3.4, 13 September 2010
********************************

* Reverted exception handling to pre-2.6 style
* Added example project to repo

Version 0.3.3, 12 July 2010
***************************

* Removed reliance on bitbucket tag download files

Version 0.3.2, 12 July 2010
***************************

* Pulled in Ian Schenck's delete_object fix

Version 0.3.1, 18 May 2010
**************************

* Fixed syncstatic deletion bug
* Require verbosity > 1 for syncstatic output

Version 0.3, 17 May 2010
**************************

* Added syncstatic management command

Version 0.2.3, 03 May 2010
**************************

* Fix bug when accessing imagekit attributes
* Fix setup.py distribute installation issue

Version 0.2.2, 11 February 2010
*******************************

* Fixed bug when using django-imagekit

Version 0.2, 10 February 2010
*****************************

* Changed focus and aim of project
* Removed all previous custom admin work
* Incorporated CloudFilesStorage custom storage backend
* Added sphinx docs
* Converted setup to use distribute

Version 0.1, 28 July 2009
*************************

* Initial release
