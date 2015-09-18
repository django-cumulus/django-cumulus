import mimetypes
import pyrax
import re
import warnings
from gzip import GzipFile

try:
    from cStringIO import StringIO
except ImportError:
    try:
        from StringIO import StringIO
    except ImportError:
        from io import StringIO

from django.core.files.storage import Storage
from django.core.files.base import File, ContentFile

try:
    from django.utils.deconstruct import deconstructible
except ImportError:
    # Make a no-op decorator to avoid errors
    def deconstructible(*args, **kwargs):
        def decorator(klass):
            return klass

        if not args:
            return decorator
        return decorator(*args, **kwargs)

from cumulus.authentication import Auth
from cumulus.settings import CUMULUS


HEADER_PATTERNS = tuple((re.compile(p), h) for p, h in CUMULUS.get("HEADERS", {}))


def get_content_type(name, content):
    """
    Checks if the content_type is already set.
    Otherwise uses the mimetypes library to guess.
    """
    if hasattr(content, "content_type"):
        content_type = content.content_type
    else:
        mime_type, encoding = mimetypes.guess_type(name)
        content_type = mime_type
    return content_type


def get_headers(name, content_type):
    headers = {"Content-Type": content_type}
    # gzip the file if its of the right content type
    if content_type in CUMULUS.get("GZIP_CONTENT_TYPES", []):
        headers["Content-Encoding"] = "gzip"
    if CUMULUS["HEADERS"]:
        for pattern, pattern_headers in HEADER_PATTERNS:
            if pattern.match(name):
                headers.update(pattern_headers.copy())
    return headers


def sync_headers(cloud_obj, headers=None, header_patterns=HEADER_PATTERNS):
    """
    Overwrites the given cloud_obj's headers with the ones given as ``headers`
    and adds additional headers as defined in the HEADERS setting depending on
    the cloud_obj's file name.
    """
    if headers is None:
        headers = {}

    # don't set headers on directories
    content_type = getattr(cloud_obj, "content_type", None)
    if content_type == "application/directory":
        return
    matched_headers = {}
    for pattern, pattern_headers in header_patterns:
        if pattern.match(cloud_obj.name):
            matched_headers.update(pattern_headers.copy())
    # preserve headers already set
    matched_headers.update(cloud_obj.headers)
    # explicitly set headers overwrite matches and already set headers
    matched_headers.update(headers)
    if matched_headers != cloud_obj.headers:
        cloud_obj.headers = matched_headers
        cloud_obj.sync_metadata()


def get_gzipped_contents(input_file):
    """
    Returns a gzipped version of a previously opened file's buffer.
    """
    zbuf = StringIO()
    zfile = GzipFile(mode="wb", compresslevel=6, fileobj=zbuf)
    zfile.write(input_file.read())
    zfile.close()
    return ContentFile(zbuf.getvalue())


@deconstructible
class CumulusStorage(Auth, Storage):
    """
    Custom storage for Cumulus.
    """
    default_quick_listdir = True
    container_name = CUMULUS["CONTAINER"]
    container_uri = CUMULUS["CONTAINER_URI"]
    container_ssl_uri = CUMULUS["CONTAINER_SSL_URI"]
    ttl = CUMULUS["TTL"]
    file_ttl = CUMULUS["FILE_TTL"]
    use_ssl = CUMULUS["USE_SSL"]

    def _open(self, name, mode="rb"):
        """
        Returns the CumulusStorageFile.
        """
        return ContentFile(self._get_object(name).get())

    def _save(self, name, content):
        """
        Uses the Cumulus service to write ``content`` to a remote
        file (called ``name``).
        """
        content_type = get_content_type(name, content.file)
        headers = get_headers(name, content_type)

        if self.use_pyrax:
            if headers.get("Content-Encoding") == "gzip":
                content = get_gzipped_contents(content)
            self.connection.store_object(container=self.container_name,
                                         obj_name=name,
                                         data=content.read(),
                                         content_type=content_type,
                                         content_encoding=headers.get("Content-Encoding", None),
                                         ttl=self.file_ttl,
                                         etag=None)
            # set headers/object metadata
            self.connection.set_object_metadata(container=self.container_name,
                                                obj=name,
                                                metadata=headers,
                                                prefix='',
                                                clear=True)
        else:
            # TODO gzipped content when using swift client
            self.connection.put_object(self.container_name, name,
                                       content, headers=headers)

        return name

    def delete(self, name):
        """
        Deletes the specified file from the storage system.

        Deleting a model doesn't delete associated files: bit.ly/12s6Oox
        """
        try:
            self.connection.delete_object(self.container_name, name)
        except pyrax.exceptions.ClientException as exc:
            if exc.http_status == 404:
                pass
            else:
                raise
        except pyrax.exceptions.NoSuchObject:
            pass

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
        file_object = self._get_object(name)
        if file_object:
            return file_object.total_bytes
        else:
            return 0

    def url(self, name):
        """
        Returns an absolute URL where the content of each file can be
        accessed directly by a web browser.
        """
        return u"{0}/{1}".format(self.container_url, name)

    def listdir(self, path):
        """
        Lists the contents of the specified path, returning a 2-tuple;
        the first being an empty list of directories (not available
        for quick-listing), the second being a list of filenames.

        If the list of directories is required, use the full_listdir method.
        """
        files = []
        if path and not path.endswith("/"):
            path = u"{0}/".format(path)
        path_len = len(path)
        for name in [x["name"] for x in
                     self.connection.get_container(self.container_name, full_listing=True)[1]]:
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
            path = u"{0}/".format(path)
        path_len = len(path)
        for name in [x["name"] for x in
                     self.connection.get_container(self.container_name, full_listing=True)[1]]:
            name = name[path_len:]
            slash = name[1:-1].find("/") + 1
            if slash:
                dirs.add(name[:slash])
            elif name:
                files.append(name)
        dirs = list(dirs)
        dirs.sort()
        return (dirs, files)


class CumulusStaticStorage(CumulusStorage):
    """
    Subclasses CumulusStorage to automatically set the container
    to the one specified in CUMULUS["STATIC_CONTAINER"]. This provides
    the ability to specify a separate storage backend for Django's
    collectstatic command.

    To use, make sure CUMULUS["STATIC_CONTAINER"] is set to something other
    than CUMULUS["CONTAINER"]. Then, tell Django's staticfiles app by setting
    STATICFILES_STORAGE = "cumulus.storage.CumulusStaticStorage".
    """
    container_name = CUMULUS["STATIC_CONTAINER"]
    container_uri = CUMULUS["STATIC_CONTAINER_URI"]
    container_ssl_uri = CUMULUS["STATIC_CONTAINER_SSL_URI"]


class ThreadSafeCumulusStorage(CumulusStorage):
    """
    Extends CumulusStorage to make it mostly thread safe.

    As long as you do not pass container or cloud objects between
    threads, you will be thread safe.

    Uses one connection/container per thread.
    """
    def __init__(self, *args, **kwargs):
        super(ThreadSafeCumulusStorage, self).__init__(*args, **kwargs)

        import threading
        self.local_cache = threading.local()

    def _get_connection(self):
        if not hasattr(self.local_cache, "connection"):
            super(ThreadSafeSwiftclientStorage, self)._get_connection()
            self.local_cache.connection = connection

        return self.local_cache.connection

    connection = property(_get_connection, CumulusStorage._set_connection)

    def _get_container(self):
        if not hasattr(self.local_cache, "container"):
            container = self.connection.create_container(self.container_name)
            self.local_cache.container = container

        return self.local_cache.container

    container = property(_get_container, CumulusStorage._set_container)


class SwiftclientStorage(CumulusStorage):
    def __init__(self, *args, **kwargs):
        warnings.warn("SwiftclientStorage is deprecated and will be removed in django-cumulus==1.3: \
                       Use CumulusStorage instead.", DeprecationWarning)
        super(SwiftclientStorage, self).__init__()


class SwiftclientStaticStorage(CumulusStaticStorage):
    def __init__(self, *args, **kwargs):
        warnings.warn("SwiftclientStaticStorage is deprecated and will be removed in django-cumulus==1.3: \
                       Use CumulusStaticStorage instead.", DeprecationWarning)
        super(SwiftclientStaticStorage, self).__init__()


class ThreadSafeSwiftclientStorage(ThreadSafeCumulusStorage):
    def __init__(self, *args, **kwargs):
        warnings.warn("ThreadSafeSwiftclientStorage is deprecated and will be removed in django-cumulus==1.3: \
                       Use ThreadSafeCumulusStorage instead.", DeprecationWarning)
        super(ThreadSafeSwiftclientStorage, self).__init__()
