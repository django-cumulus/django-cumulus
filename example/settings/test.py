import os

import django

from common import *  # noqa

INSTALLED_APPS += (
    'cumulus.tests',
)

CUMULUS['PYRAX_IDENTITY_TYPE'] = 'rackspace'
# Avoiding conflits with container names across tests.
CUMULUS['CONTAINER'] = CUMULUS['CONTAINER'] + os.environ.get('CONTAINER_TAG', '')
CUMULUS['STATIC_CONTAINER'] = CUMULUS['STATIC_CONTAINER'] + os.environ.get('CONTAINER_TAG', '')

# Test < 1.6 can't use this runner. Test >= 1.6 need this runner.
if django.get_version() >= '1.6':
    TEST_RUNNER = 'django.test.runner.DiscoverRunner'
