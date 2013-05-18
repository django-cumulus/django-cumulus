from urlparse import urlparse

from django.conf import settings

from cumulus.storage import CloudFilesStorage, CloudFilesStaticStorage

def _is_ssl_uri(uri):
    return urlparse(uri).scheme == 'https'

def _get_container_urls(cloudfiles_storage):
    cdn_url = cloudfiles_storage._get_container_url()
    ssl_url = cdn_url if _is_ssl_uri(cdn_url) else cloudfiles_storage.container.public_ssl_uri()
    
    return cdn_url, ssl_url

def cdn_url(request):
    """
    A context processor to expose the full CDN URL in templates.
    """
    cdn_url, ssl_url = _get_container_urls(CloudFilesStorage())
    static_url = settings.STATIC_URL

    return {'CDN_URL': cdn_url+static_url, 'CDN_SSL_URL': ssl_url+static_url}

def static_cdn_url(request):
    """
    A context processor to expose the full static CDN URL 
    as static URL in templates.
    """
    cdn_url, ssl_url = _get_container_urls(CloudFilesStaticStorage())
    static_url = settings.STATIC_URL

    return {'STATIC_URL': cdn_url+static_url, 'STATIC_SSL_URL': ssl_url+static_url, 'LOCAL_STATIC_URL': static_url}
