import django
# For compatibility with < 1.6 django testing.
if django.get_version() < '1.6':
    from .test_storage import *  # noqa
