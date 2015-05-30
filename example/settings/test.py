from common import *  # noqa

INSTALLED_APPS += (
    'cumulus.tests',
)

CUMULUS["PYRAX_IDENTITY_TYPE"] = 'rackspace'
