from pyrax.cf_wrapper.client import CFClient

from django.conf import settings


CUMULUS = {
    "API_KEY": None,
    "AUTH_URL": "us_authurl",
    "AUTH_VERSION": "1.0",
    "AUTH_TENANT_NAME": None,
    "REGION": "DFW",
    "CNAMES": None,
    "CONTAINER": None,
    "CONTAINER_URI": None,
    "CONTAINER_SSL_URI": None,
    "SERVICENET": False,
    "TIMEOUT": 5,
    "TTL": CFClient.default_cdn_ttl,  # 86400s (24h), pyrax default
    "USE_SSL": False,
    "USERNAME": None,
    "STATIC_CONTAINER": None,
    "INCLUDE_LIST": [],
    "EXCLUDE_LIST": [],
    "HEADERS": {},
    "GZIP_CONTENT_TYPES": [],
    "USE_PYRAX": True,
    "PYRAX_IDENTITY_TYPE": None,
}

if hasattr(settings, "CUMULUS"):
    CUMULUS.update(settings.CUMULUS)

if "FILTER_LIST" in settings.CUMULUS.keys():
    CUMULUS["EXCLUDE_LIST"] = CUMULUS

# set the full rackspace auth_url
if CUMULUS["AUTH_URL"] == "us_authurl":
    CUMULUS["AUTH_URL"] = "https://auth.api.rackspacecloud.com/v1.0"
elif CUMULUS["AUTH_URL"] == "uk_authurl":
    CUMULUS["AUTH_URL"] = "https://lon.auth.api.rackspacecloud.com/v1.0"

# backwards compatibility for old-style cumulus settings
if not hasattr(settings, "CUMULUS") and hasattr(settings, "CUMULUS_API_KEY"):
    import warnings
    warnings.warn(
        "settings.CUMULUS_* is deprecated; use settings.CUMULUS instead.",
        PendingDeprecationWarning
    )

    CUMULUS.update({
        "API_KEY": getattr(settings, "CUMULUS_API_KEY"),
        "AUTH_URL": getattr(settings, "AUTH_URL", "us_authurl"),
        "REGION": getattr(settings, "REGION", "DFW"),
        "CNAMES": getattr(settings, "CUMULUS_CNAMES", None),
        "CONTAINER": getattr(settings, "CUMULUS_CONTAINER"),
        "SERVICENET": getattr(settings, "CUMULUS_USE_SERVICENET", False),
        "TIMEOUT": getattr(settings, "CUMULUS_TIMEOUT", 5),
        "TTL": getattr(settings, "CUMULUS_TTL", CFClient.default_cdn_ttl),
        "USERNAME": getattr(settings, "CUMULUS_USERNAME"),
    })
