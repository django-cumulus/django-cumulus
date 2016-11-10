from pyrax.object_storage import DEFAULT_CDN_TTL

from django.conf import settings


CUMULUS = {
    "API_KEY": None,
    "AUTH_URL": "us_authurl",
    "AUTH_VERSION": "2.0",
    "AUTH_TENANT_NAME": None,
    "AUTH_TENANT_ID": None,
    "REGION": "DFW",
    "CNAMES": None,
    "CONTAINER": None,
    "CONTAINER_URI": None,
    "CONTAINER_SSL_URI": None,
    "SERVICENET": False,
    "TIMEOUT": 5,
    "TTL": DEFAULT_CDN_TTL,  # 86400s (24h), pyrax default
    "USE_SSL": False,
    "USERNAME": None,
    "STATIC_CONTAINER": None,
    "STATIC_CONTAINER_URI": None,
    "STATIC_CONTAINER_SSL_URI": None,
    "INCLUDE_LIST": [],
    "EXCLUDE_LIST": [],
    "HEADERS": {},
    "GZIP_CONTENT_TYPES": [],
    "USE_PYRAX": True,
    "PYRAX_IDENTITY_TYPE": 'rackspace',
    "FILE_TTL": None,
    "FAIL_SILENTLY": True,
}

if hasattr(settings, "CUMULUS"):
    CUMULUS.update(settings.CUMULUS)

# set the full rackspace auth_url
if CUMULUS["AUTH_URL"] == "us_authurl":
    CUMULUS["AUTH_URL"] = "https://identity.api.rackspacecloud.com/v2.0"
elif CUMULUS["AUTH_URL"] == "uk_authurl":
    CUMULUS["AUTH_URL"] = "https://lon.identity.api.rackspacecloud.com/v2.0"
