from django.conf import settings

from cumulus.storage import SwiftclientStorage


def cdn_url(request):
    """
    A context processor to expose the full static cdn url in templates.
    """
    openstack_storage = SwiftclientStorage()
    content_url = openstack_storage.get_container_uri()
    static_url = settings.STATIC_URL
    return {
        "CDN_URL": content_url,  # deprecated
        "CONTENT_URL": content_url,
        "STATIC_URL": static_url,
    }
