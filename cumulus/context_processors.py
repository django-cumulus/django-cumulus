from urlparse import urlparse

from django.conf import settings

from cumulus.storage import CumulusStorage, CumulusStaticStorage


def _is_ssl_uri(uri):
    return urlparse(uri).scheme == "https"


def _get_container_urls(swiftclient_storage):
    cdn_url = swiftclient_storage.container.cdn_uri
    ssl_url = swiftclient_storage.container.cdn_ssl_uri

    return cdn_url, ssl_url


def cdn_url(request):
    """
    A context processor that exposes the full CDN URL in templates.
    """
    cdn_url, ssl_url = _get_container_urls(CumulusStorage())
    static_url = settings.STATIC_URL

    return {
        "CDN_URL": cdn_url + static_url,
        "CDN_SSL_URL": ssl_url + static_url,
    }


def static_cdn_url(request):
    """
    A context processor that exposes the full static CDN URL
    as static URL in templates.
    """
    cdn_url, ssl_url = _get_container_urls(CumulusStaticStorage())
    static_url = settings.STATIC_URL

    return {
        "STATIC_URL": cdn_url + static_url,
        "STATIC_SSL_URL": ssl_url + static_url,
        "LOCAL_STATIC_URL": static_url,
    }
