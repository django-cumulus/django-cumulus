from django.conf import settings


CUMULUS = {
    "API_KEY": None,
    "AUTH_URL": "us_authurl",
    "CNAMES": None,
    "CONTAINER": None,
    "CONTAINER_URI": None,
    "SERVICENET": False,
    "TIMEOUT": 5,
    "TTL": 600,
    "USE_SSL": False,
    "USERNAME": None,
    "STATIC_CONTAINER": None,
    "INCLUDE_LIST": [],
    "EXCLUDE_LIST": [],
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
if not hasattr(settings, "CUMULUS"):
    import warnings
    warnings.warn(
        "settings.CUMULUS_* is deprecated; use settings.CUMULUS instead.",
        PendingDeprecationWarning
    )

    CUMULUS.update({
        "API_KEY": getattr(settings, "CUMULUS_API_KEY"),
        "AUTH_URL": getattr(settings, "AUTH_URL", "us_authurl"),
        "CNAMES": getattr(settings, "CUMULUS_CNAMES", None),
        "CONTAINER": getattr(settings, "CUMULUS_CONTAINER"),
        "SERVICENET": getattr(settings, "CUMULUS_USE_SERVICENET", False),
        "TIMEOUT": getattr(settings, "CUMULUS_TIMEOUT", 5),
        "TTL": getattr(settings, "CUMULUS_TTL", 600),
        "USERNAME": getattr(settings, "CUMULUS_USERNAME"),
    })
