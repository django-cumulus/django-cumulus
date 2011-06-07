from django.conf import settings

from cumulus.storage import CloudFilesStorage

def cdn_url(request):
    """
    A context processor to expose the full cdn url in templates.

    """
    cloudfiles_storage = CloudFilesStorage()
    static_url = settings.STATIC_URL
    container_url = cloudfiles_storage._get_container_url()
    cdn_url = container_url + static_url

    return {'CDN_URL': cdn_url}