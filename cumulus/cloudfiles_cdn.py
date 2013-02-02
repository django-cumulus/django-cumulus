import cloudfiles

from cumulus.settings import CUMULUS


class CloudfilesCDN(object):
    """
    The majority of django-cumulus now uses the Openstack api via the
    python-swifclient library, however there are a few features
    specific to the Rackspace Cloud Files CDN that are not available
    with python-swifclient.

    python-cloudfiles is necessary to convert a private container to a
    public one.
    """

    def __init__(self):
        """
        Connect using the python-cloudfiles api.
        """
        self.conn = cloudfiles.get_connection(username=CUMULUS["USERNAME"],
                                              api_key=CUMULUS["API_KEY"],
                                              servicenet=CUMULUS["SERVICENET"],
                                              authurl=CUMULUS["CLOUDFILES_AUTH_URL"])

    def public_uri(self, container_name):
        """
        Get the public uri of a public container.
        Returns ``None`` if private.
        """
        container = self.conn.get_container(container_name)
        if container.is_public():
            return container.public_uri()
        else:
            return None

    def make_public(self, container_name):
        container = self.conn.get_container(container_name)
        if not container.is_public():
            return container.make_public()
