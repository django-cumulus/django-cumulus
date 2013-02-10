import mimetypes
import pyrax

from django.conf import settings
from django.core.files import File
from django.core.files.storage import Storage

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
        api_key = api_key or CUMULUS["API_KEY"]
        username = username or CUMULUS["USERNAME"]
        pyrax.set_credentials(username, api_key)
        # self.auth_url = CUMULUS["AUTH_URL"]
        # self.connection_kwargs = connection_kwargs or {}
        self.container_name = container or CUMULUS["CONTAINER"]
        self.use_snet = CUMULUS["SERVICENET"]
        self.use_ssl = CUMULUS["USE_SSL"]

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
        Get or create the container.
        """
        if not hasattr(self, "_container"):
            self.container = pyrax.cloudfiles.create_container(self.container_name)
        return self._container

    def _set_container(self, container):
        """
        Set the container (and, if needed, the configured TTL on it), making
        the container publicly available.
        """
        if not container.cdn_enabled:
            container.make_public()
        # if container.cdn_ttl != self.ttl or not container.is_public():
        #     container.make_public(ttl=self.ttl)
        if hasattr(self, "_container_public_uri"):
            delattr(self, "_container_public_uri")
        self._container = container

    container = property(_get_container, _set_container)

    def _get_container_url(self):
        if self.use_ssl and CUMULUS["CONTAINER_SSL_URI"]:
            self._container_public_uri = CUMULUS["CONTAINER_SSL_URI"]
        elif self.use_ssl:
            self._container_public_uri = self.container.cdn_ssl_uri
        elif CUMULUS["CONTAINER_URI"]:
            self._container_public_uri = CUMULUS["CONTAINER_URI"]
            else:
            self._container_public_uri = self.container.cdn_uri
        if CUMULUS["CNAMES"] and self._container_public_uri in CUMULUS["CNAMES"]:
            self._container_public_uri = CUMULUS["CNAMES"][container_public_uri]
        return self._container_public_uri

    container_url = property(_get_container_url)

    def _get_object(self, name):
        """
        Helper function to retrieve the requested Cloud Files Object.
        """
        if name not in self.container.get_object_names():
            return False
        else:
        return self.container.get_object(name)

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
        # Checks if the content_type is already set.
        # Otherwise uses the mimetypes library to guess.
        if hasattr(content.file, "content_type"):
            content_type = content.file.content_type
        else:
            mime_type, encoding = mimetypes.guess_type(name)
            content_type = mime_type
        if name not in self.container.get_object_names():
            self.container.store_object(obj_name=name,
                                        data=content.read(),
                                        content_type=content_type,
                                        etag=None)
        return name

    def delete(self, name):
        """
        Deletes the specified file from the storage system.

        Deleting a model doesn't delete associated files:
        https://docs.djangoproject.com/en/1.3/releases/1.3/#deleting-a-model-doesn-t-delete-associated-files
        """
        try:
            self.container.delete_object(name)
        except pyrax.exceptions.ClientException, exc:
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
        return bool(self._get_object(name))

    def size(self, name):
        """
        Returns the total size, in bytes, of the file specified by name.
        """
        return self._get_object(name).total_bytes

    def url(self, name):
        """
        Returns an absolute URL where the content of each file can be
        accessed directly by a web browser.
        """
        return "{0}/{1}".format(self.container_url, name)

    def listdir(self, path):
        """
        Lists the contents of the specified path, returning a 2-tuple;
        the first being an empty list of directories (not available
        for quick-listing), the second being a list of filenames.

        If the list of directories is required, use the full_listdir method.
        """
        files = []
        if path and not path.endswith("/"):
            path = "{0}/".format(path)
        path_len = len(path)
        for name in self.container.get_object_names():
            if name.startswith(path):
            files.append(name[path_len:])
        return ([], files)

    def full_listdir(self, path):
        """
        Lists the contents of the specified path, returning a 2-tuple
        of lists; the first item being directories, the second item
        being files.
        """
        dirs = set()
        files = []
        if path and not path.endswith("/"):
            path = "{0}/".format(path)
        path_len = len(path)
        for name in self.container.get_object_names():
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
            self._file = self._storage._get_object(self.name)
            self._file.tell = self._get_pos
        return self._file

    def _set_file(self, value):
        if value is None:
            if hasattr(self, "_file"):
                del self._file
        else:
            self._file = value

    file = property(_get_file, _set_file)

    def read(self, chunk_size):
        if self._pos == self._get_size():
            return ""
        data = self.file.get(chunk_size=chunk_size).next()
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

    Uses one container per thread.
    """
    def __init__(self, *args, **kwargs):
        super(ThreadSafeSwiftclientStorage, self).__init__(*args, **kwargs)

        import threading
        self.local_cache = threading.local()

    def _get_container(self):
        if not hasattr(self.local_cache, "container"):
            container = pyrax.cloudfiles.create_container(self.container_name)
            self.local_cache.container = container

        return self.local_cache.container

    container = property(_get_container, SwiftclientStorage._set_container)
