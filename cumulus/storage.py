import mimetypes
import os

import swiftclient

from django.conf import settings
from django.core.files import File
from django.core.files.storage import Storage

from cumulus.cloudfiles_cdn import CloudfilesCDN
from cumulus.settings import CUMULUS


class SwiftclientStorage(Storage):
    """
    Custom storage for Swiftclient.
    """
    default_quick_listdir = True

    def __init__(self, username=None, api_key=None, container=None,
                 connection_kwargs=None):
        """
        Initialize the settings for the connection and container.
        """
        self.api_key = api_key or CUMULUS["API_KEY"]
        self.auth_url = CUMULUS["AUTH_URL"]
        self.connection_kwargs = connection_kwargs or {}
        self.container_name = container or CUMULUS["CONTAINER"]
        self.use_snet = CUMULUS["SERVICENET"]
        self.username = username or CUMULUS["USERNAME"]
        self.use_ssl = CUMULUS["USE_SSL"]
        self.swiftclient_connection = self.get_swiftclient_connection()
        self.cloudfiles_connection = self.get_cloudfiles_connection()
        self.container = self.get_container()
        self.container_public_uri = self.get_container_uri()
        self.full_listdir("img/")

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

    def get_swiftclient_connection(self):
        """
        Get a connection to the swiftclient api.
        """
        if hasattr(self, "swiftclient_connection"):
            return self.swiftclient_connection
        return swiftclient.Connection(authurl=self.auth_url,
                                      user=self.username,
                                      snet=self.use_snet,
                                      key=self.api_key,
                                      **self.connection_kwargs)

    def get_cloudfiles_connection(self):
        """
        Get a connection to the cloudfiles api.
        """
        if hasattr(self, "cloudfiles_connection"):
            return self.cloudfiles_connection
        return CloudfilesCDN()

    def get_cloud_objs_names(self):
        """
        Get a list containing the name of each cloud object.
        """
        if hasattr(self, "cloud_objs_names"):
            return self.cloud_objs_names
        return [cloud_obj["name"] for cloud_obj in self.container[1]]

    def get_container(self):
        """
        Get the container, making it publicly available if it is not already.
        """
        if hasattr(self, "container"):
            container = self.container
        container = self.swiftclient_connection.get_container(self.container_name)
        if not self.cloudfiles_connection.public_uri(self.container_name):
            self.cloudfiles_connection.make_public(self.container_name)
        return container

    def get_container_uri(self):
        if hasattr(self, "container_public_uri"):
            return self.container_public_uri
        elif self.use_ssl:
            container_public_uri = CUMULUS["CONTAINER_SSL_URI"]
        elif CUMULUS["CONTAINER_URI"]:
            container_public_uri = CUMULUS["CONTAINER_URI"]
        elif self.cloudfiles_connection.public_uri(self.container_name):
            container_public_uri = self.cloudfiles_connection.public_uri(self.container_name)
        if CUMULUS["CNAMES"] and container_public_uri in CUMULUS["CNAMES"]:
            container_public_uri = CUMULUS["CNAMES"][container_public_uri]
        return container_public_uri

    def _get_cloud_obj(self, name):
        """
        Helper function to retrieve the requested Cloud Files Object.
        """
        if not hasattr(self, "cloud_objs_names"):
            self.cloud_objs_names = self.get_cloud_objs_names()
        return bool(name in self.cloud_objs_names)

    def _open(self, name, mode="rb"):
        """
        Return the SwiftclientStorageFile.
        """
        return SwiftclientStorageFile(storage=self, name=name)

    def _save(self, name, content):
        """
        Use the Swiftclient service to write ``content`` to a remote
        file (called ``name``).
        """
        (path, last) = os.path.split(name)
        content.open()
        if hasattr(content.file, "size"):
            size = content.file.size
        else:
            size = content.size
        # Checks if the content_type is already set.
        # Otherwise uses the mimetypes library to guess.
        if hasattr(content.file, "content_type"):
            content_type = content.file.content_type
        elif hasattr(content, "content_type"):
            content_type = content.content_type
        else:
            mime_type, encoding = mimetypes.guess_type(name)
            content_type = mime_type
        if name not in self.cloud_objs_names:
            self.swiftclient_connection.put_object(container=self.container_name,
                                                   obj=name,
                                                   contents=content,
                                                   content_length=size,
                                                   etag=None,
                                                   content_type=content_type,
                                                   headers=None)
            self.cloud_objs_names.append(name)
        content.close()
        return name

    def delete(self, name):
        """
        Deletes the specified file from the storage system.

        Deleting a model doesn't delete associated files:
        https://docs.djangoproject.com/en/1.3/releases/1.3/#deleting-a-model-doesn-t-delete-associated-files
        """
        try:
            self.swiftclient_connection.delete_object(
                container=self.container_name,
                obj=name)
            self.cloud_objs_names.remove(name)
        except swiftclient.client.ClientException, exc:
            if exc.http_status == 404:
                pass
            else:
                raise

    def exists(self, name):
        """
        Returns True if a file referenced by the given name already
        exists in the storage system, or False if the name is
        available for a new file.
        """
        return bool(self._get_cloud_obj(name))

    def size(self, name):
        """
        Returns the total size, in bytes, of the file specified by name.
        """
        return self._get_cloud_obj(name).size

    def url(self, name):
        """
        Returns an absolute URL where the content of each file can be
        accessed directly by a web browser.
        """
        return "{0}/{1}".format(self.container_public_uri, name)

    def listdir(self, path):
        """
        Lists the contents of the specified path, returning a 2-tuple;
        the first being an empty list of directories (not available
        for quick-listing), the second being a list of filenames.

        If the list of directories is required, use the full_listdir method.
        """
        if not hasattr(self, "cloud_objs"):
            self.cloud_objs_names = self.get_cloud_objs_names()
        files = []
        if path and not path.endswith("/"):
            path = "{0}/".format(path)
        path_len = len(path)
        for name in self.cloud_objs_names:
            if name.startswith(path):
                files.append(name[path_len:])
        return ([], files)

    def full_listdir(self, path):
        """
        Lists the contents of the specified path, returning a 2-tuple
        of lists; the first item being directories, the second item
        being files.
        """
        if not hasattr(self, "cloud_objs"):
            self.cloud_objs_names = self.get_cloud_objs_names()
        dirs = set()
        files = []
        if path and not path.endswith("/"):
            path = "{0}/".format(path)
        path_len = len(path)
        for name in self.cloud_objs_names:
            if name.startswith(path):
                name = name[path_len:]
                slash = name[1:-1].find("/") + 1
                if slash:
                    dirs.add(name[:slash])
                    files.append(name[slash + 1:])
                else:
                    files.append(name)
        dirs = list(dirs)
        dirs.sort()
        return (dirs, files)


class SwiftclientStaticStorage(SwiftclientStorage):
    """
    Subclasses SwiftclientStorage to automatically set the container
    to the one specified in CUMULUS["STATIC_CONTAINER"]. This provides
    the ability to specify a separate storage backend for Django's
    collectstatic command.

    To use, make sure CUMULUS["STATIC_CONTAINER"] is set to something other
    than CUMULUS["CONTAINER"]. Then, tell Django's staticfiles app by setting
    STATICFILES_STORAGE = "cumulus.storage.SwiftclientStaticStorage".
    """
    def __init__(self, *args, **kwargs):
        if not "container" in kwargs:
            kwargs["container"] = CUMULUS["STATIC_CONTAINER"]
        super(SwiftclientStaticStorage, self).__init__(*args, **kwargs)


class SwiftclientStorageFile(File):
    closed = False

    def __init__(self, storage, name, *args, **kwargs):
        self._storage = storage
        self._pos = 0
        super(SwiftclientStorageFile, self).__init__(file=None, name=name,
                                                    *args, **kwargs)

    def _get_pos(self):
        return self._pos

    def _get_size(self):
        if not hasattr(self, "_size"):
            self._size = self._storage.size(self.name)
        return self._size

    def _set_size(self, size):
        self._size = size

    size = property(_get_size, _set_size)

    def _get_file(self):
        if not hasattr(self, "_file"):
            self._file = self._storage.swiftclient_connection.get_object(
                self._storage.container_name, self.name)
            import ipdb; ipdb.set_trace()
            self._file.tell = self._get_pos
        return self._file

    def _set_file(self, value):
        if value is None:
            if hasattr(self, "_file"):
                del self._file
        else:
            self._file = value

    file = property(_get_file, _set_file)

    def read(self, num_bytes=None):
        if self._pos == self._get_size():
            return ""
        if num_bytes and self._pos + num_bytes > self._get_size():
            num_bytes = self._get_size() - self._pos
        data = self.file.read(size=num_bytes or -1, offset=self._pos)
        self._pos += len(data)
        return data

    def open(self, *args, **kwargs):
        """
        Open the cloud file object.
        """
        self._pos = 0

    def close(self, *args, **kwargs):
        self._pos = 0

    @property
    def closed(self):
        return not hasattr(self, "_file")

    def seek(self, pos):
        self._pos = pos


class ThreadSafeSwiftclientStorage(SwiftclientStorage):
    """
    Extends SwiftclientStorage to make it mostly thread safe.

    As long as you do not pass container or cloud objects between
    threads, you will be thread safe.

    Uses one cloudfiles connection per thread.
    """

    def __init__(self, *args, **kwargs):
        super(ThreadSafeSwiftclientStorage, self).__init__(*args, **kwargs)
        import threading
        self.local_cache = threading.local()
        self.local_cache.swiftclient_connection = self.get_swiftclient_connection()
        self.local_cache.cloudfiles_connection = self.get_cloudfiles_connection()
        self.local_cache.container = self.get_container()

    def get_swiftclient_connection(self):
        """
        Get a thread safe connection to the swiftclient api.
        """
        if hasattr(self.local_cache, "swiftclient_connection"):
            return self.local_cache.swiftclient_connection
        return swiftclient.Connection(authurl=self.auth_url,
                                      user=self.username,
                                      snet=self.use_snet,
                                      key=self.api_key,
                                      **self.connection_kwargs)

    def get_cloudfiles_connection(self):
        """
        Get a thread safe connection to the cloudfiles api.
        """
        if hasattr(self.local_cache, "cloudfiles_connection"):
            return self.local_cache.cloudfiles_connection
        return CloudfilesCDN()

    def get_container(self):
        """
        Get a thread safe connection to the container.
        """
        if hasattr(self.local_cache, "container"):
            container = self.local_cache.container
        container = self.swiftclient_connection.get_container(self.container_name)
        if not self.local_cache.cloudfiles_connection.public_uri(self.container_name):
            self.local_cache.cloudfiles_connection.make_public(self.container_name)
        return container
