import logging
import pyrax
try:
    import swiftclient
except ImportError:
    pass

from cumulus.settings import CUMULUS


class Auth(object):
    connection_kwargs = {}
    use_pyrax = CUMULUS["USE_PYRAX"]
    use_snet = CUMULUS["SERVICENET"]
    region = CUMULUS["REGION"]
    username = CUMULUS["USERNAME"]
    api_key = CUMULUS["API_KEY"]
    auth_url = CUMULUS["AUTH_URL"]
    auth_tenant_id = CUMULUS["AUTH_TENANT_ID"]
    auth_tenant_name = CUMULUS["AUTH_TENANT_NAME"]
    auth_version = CUMULUS["AUTH_VERSION"]
    pyrax_identity_type = CUMULUS["PYRAX_IDENTITY_TYPE"]

    def __init__(self, username=None, api_key=None, container=None,
                 connection_kwargs=None, container_uri=None):
        """
        Initializes the settings for the connection and container.
        """
        if username is not None:
            self.username = username
        if api_key is not None:
            self.api_key = api_key
        if container is not None:
            self.container_name = container
        if connection_kwargs is not None:
            self.connection_kwargs = connection_kwargs

        # connect
        if self.use_pyrax:
            self.pyrax = pyrax
            if self.pyrax_identity_type:
                self.pyrax.set_setting("identity_type", self.pyrax_identity_type)
            if self.auth_url:
                self.pyrax.set_setting("auth_endpoint", self.auth_url)
            if self.auth_tenant_id:
                self.pyrax.set_setting("tenant_id", self.auth_tenant_id)
            self.pyrax.set_setting("region", self.region)
            try:
                self.pyrax.set_credentials(self.username, self.api_key)
            except:
                logging.exception(
                    """Pyrax Connect Error in `django_cumulus.cumulus.authentication.Auth`::
                           self.pyrax.set_credentials(self.username, self.api_key)
                    """)
        # else:
        #     headers = {"X-Container-Read": ".r:*"}
        #     self._connection.post_container(self.container_name, headers=headers)

    def _get_connection(self):
        if not hasattr(self, "_connection"):
            if self.use_pyrax:
                self._connection = pyrax.connect_to_cloudfiles(public=True)
            else:
                self._connection = swiftclient.Connection(
                    authurl=self.auth_url,
                    user=self.username,
                    key=self.api_key,
                    snet=self.servicenet,
                    auth_version=self.auth_version,
                    tenant_name=self.auth_tenant_name,
                )
        return self._connection

    def _set_connection(self, value):
        self._connection = value

    connection = property(_get_connection, _set_connection)

    def __getstate__(self):
        """
        Return a picklable representation of the storage.
        """
        return {
            "username": self.username,
            "api_key": self.api_key,
            "container_name": self.container_name,
            "use_snet": self.use_snet,
            "connection_kwargs": self.connection_kwargs
        }

    def _get_container(self):
        """
        Gets or creates the container.
        """
        if not hasattr(self, "_container"):
            if self.use_pyrax:
                self._container = self.connection.create_container(self.container_name)
            else:
                self._container = None
        return self._container

    def _set_container(self, container):
        """
        Sets the container (and, if needed, the configured TTL on it), making
        the container publicly available.
        """
        if self.use_pyrax:
            if container.cdn_ttl != self.ttl or not container.cdn_enabled:
                container.make_public(ttl=self.ttl)
            if hasattr(self, "_container_public_uri"):
                delattr(self, "_container_public_uri")
        self._container = container

    container = property(_get_container, _set_container)

    def _get_container_url(self):
        if self.use_ssl and self.container_ssl_uri:
            self._container_public_uri = self.container_ssl_uri
        elif self.use_ssl:
            self._container_public_uri = self.container.cdn_ssl_uri
        elif self.container_uri:
            self._container_public_uri = self.container_uri
        else:
            self._container_public_uri = self.container.cdn_uri
        if CUMULUS["CNAMES"] and self._container_public_uri in CUMULUS["CNAMES"]:
            self._container_public_uri = CUMULUS["CNAMES"][self._container_public_uri]
        return self._container_public_uri

    container_url = property(_get_container_url)

    def _get_object(self, name):
        """
        Helper function to retrieve the requested Object.
        """
        try:
            return self.container.get_object(name)
        except pyrax.exceptions.NoSuchObject:
            return None
        except swiftclient.exceptions.ClientException:
            return None
