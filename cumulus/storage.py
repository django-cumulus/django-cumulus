import mimetypes
import os
import re
import hashlib
from gzip import GzipFile
from StringIO import StringIO

import cloudfiles
from cloudfiles.errors import NoSuchObject, ResponseError

from django.core.files.base import File, ContentFile
from django.core.files.storage import Storage

from .settings import CUMULUS


HEADER_PATTERNS = tuple((re.compile(p), h) for p, h in CUMULUS.get('HEADERS', {}))


def sync_headers(cloud_obj, headers={}, header_patterns=HEADER_PATTERNS):
    """
    Overwrite the given cloud_obj's headers with the ones given as ``headers`
    and add additional headers as defined in the HEADERS setting depending on 
    the cloud_obj's file name.
    """
    # don't set headers on directories
    content_type = getattr(cloud_obj, 'content_type', None)
    if content_type == 'application/directory':
        return
    matched_headers = {}
    for pattern, pattern_headers in header_patterns:
        if pattern.match(cloud_obj.name):
            matched_headers.update(pattern_headers.copy())
    matched_headers.update(cloud_obj.headers)  # preserve headers already set
    matched_headers.update(headers)  # explicitly set headers overwrite matches and already set headers
    if matched_headers != cloud_obj.headers:
        cloud_obj.headers = matched_headers
        cloud_obj.sync_metadata()


def get_gzipped_contents(input_file):
    """
    Return a gzipped version of a previously opened file's buffer.
    """
    zbuf = StringIO()
    zfile = GzipFile(mode='wb', compresslevel=6, fileobj=zbuf)
    zfile.write(input_file.read())
    zfile.close()
    return ContentFile(zbuf.getvalue())


class CloudFilesStorage(Storage):
    """
    Custom storage for Rackspace Cloud Files.
    """
    default_quick_listdir = True
    api_key = CUMULUS['API_KEY']
    auth_url = CUMULUS['AUTH_URL']
    connection_kwargs = {}
    container_name = CUMULUS['CONTAINER']
    timeout = CUMULUS['TIMEOUT']
    use_servicenet = CUMULUS['SERVICENET']
    username = CUMULUS['USERNAME']
    ttl = CUMULUS['TTL']
    use_ssl = CUMULUS['USE_SSL']

    def __init__(self, username=None, api_key=None, container=None, timeout=None,
                 connection_kwargs=None, container_uri=None):
        """
        Initialize the settings for the connection and container.
        """
        if username is not None:
            self.username = username
        if api_key is not None:
            self.api_key = api_key
        if container is not None:
            self.container_name = container
        if timeout is not None:
            self.timeout = timeout
        if connection_kwargs is not None:
            self.connection_kwargs = connection_kwargs

        if container_uri is not None:
            self._container_public_uri = container_uri
        elif 'CONTAINER_URI' in CUMULUS:
            self._container_public_uri = CUMULUS['CONTAINER_URI']

    def __getstate__(self):
        """
        Return a picklable representation of the storage.
        """
        return dict(username=self.username,
                    api_key=self.api_key,
                    container_name=self.container_name,
                    timeout=self.timeout,
                    use_servicenet=self.use_servicenet,
                    connection_kwargs=self.connection_kwargs)

    def _get_connection(self):
        if not hasattr(self, '_connection'):
            self._connection = cloudfiles.get_connection(
                                  username=self.username,
                                  api_key=self.api_key,
                                  authurl = self.auth_url,
                                  timeout=self.timeout,
                                  servicenet=self.use_servicenet,
                                  **self.connection_kwargs)
        return self._connection

    def _set_connection(self, value):
        self._connection = value

    connection = property(_get_connection, _set_connection)

    def _get_container(self):
        if not hasattr(self, '_container'):
            self.container = self.connection.get_container(
                                                        self.container_name)
        return self._container

    def _set_container(self, container):
        """
        Set the container (and, if needed, the configured TTL on it), making
        the container publicly available.
        """
        if container.cdn_ttl != self.ttl or not container.is_public():
            container.make_public(ttl=self.ttl)
        if hasattr(self, '_container_public_uri'):
            delattr(self, '_container_public_uri')
        self._container = container

    container = property(_get_container, _set_container)

    def _get_container_url(self):
        if not hasattr(self, '_container_public_uri'):
            if self.use_ssl:
                self._container_public_uri = self.container.public_ssl_uri()
            else:
                self._container_public_uri = self.container.public_uri()
        if CUMULUS['CNAMES'] and self._container_public_uri in CUMULUS['CNAMES']:
            self._container_public_uri = CUMULUS['CNAMES'][self._container_public_uri]
        return self._container_public_uri

    container_url = property(_get_container_url)

    def _get_cloud_obj(self, name):
        """
        Helper function to get retrieve the requested Cloud Files Object.
        """
        return self.container.get_object(name)

    def _open(self, name, mode='rb'):
        """
        Return the CloudFilesStorageFile.
        """
        return CloudFilesStorageFile(storage=self, name=name)

    def _save(self, name, content):
        """
        Use the Cloud Files service to write ``content`` to a remote file
        (called ``name``).
        """
        (path, last) = os.path.split(name)
 
        # Avoid infinite loop if path is '/'
        if path and path != '/':
            try:
                self.container.get_object(path)
            except NoSuchObject:
                self._save(path, CloudStorageDirectory(path))

        content.open()
        cloud_obj = self.container.create_object(name)
        
        # If the objects has a hash, it already exists. The hash is md5 of
        # the content. If the hash has not changed, do not send the file over
        # again.
        upload = True
        if cloud_obj.etag:
            if cloud_obj.etag == cloud_obj.compute_md5sum(content.file):
                upload = False

        if upload:
            # If the content type is available, pass it in directly rather than
            # getting the cloud object to try to guess.
            if hasattr(content.file, 'content_type'):
                cloud_obj.content_type = content.file.content_type
            elif hasattr(content, 'content_type'):
                cloud_obj.content_type = content.content_type
            else:
                mime_type, encoding = mimetypes.guess_type(name)
                cloud_obj.content_type = mime_type
            # gzip the file if its of the right content type
            if cloud_obj.content_type in CUMULUS.get('GZIP_CONTENT_TYPES', []):
                content = get_gzipped_contents(content)
                cloud_obj.headers['Content-Encoding'] = 'gzip'
            # set file size
            if hasattr(content.file, 'size'):
                cloud_obj.size = content.file.size
            else:
                cloud_obj.size = content.size
            cloud_obj.send(content)

        content.close()
        sync_headers(cloud_obj)
        return name

    def delete(self, name):
        """
        Deletes the specified file from the storage system.
        """
        try:
            self.container.delete_object(name)
        except ResponseError, exc:
            if exc.status == 404:
                pass
            else:
                raise

    def exists(self, name):
        """
        Returns True if a file referenced by the given name already exists in
        the storage system, or False if the name is available for a new file.
        """
        try:
            self._get_cloud_obj(name)
            return True
        except NoSuchObject:
            return False

    def listdir(self, path):
        """
        Lists the contents of the specified path, returning a 2-tuple; the
        first being an empty list of directories (not available for quick-
        listing), the second being a list of filenames.

        If the list of directories is required, use the full_listdir method.
        """
        files = []
        if path and not path.endswith('/'):
            path = '%s/' % path
        path_len = len(path)
        for name in self.container.list_objects(path=path):
            files.append(name[path_len:])
        return ([], files)

    def full_listdir(self, path):
        """
        Lists the contents of the specified path, returning a 2-tuple of lists;
        the first item being directories, the second item being files.

        On large containers, this may be a slow operation for root containers
        because every single object must be returned (cloudfiles does not
        provide an explicit way of listing directories).
        """
        dirs = set()
        files = []
        if path and not path.endswith('/'):
            path = '%s/' % path
        path_len = len(path)
        for name in self.container.list_objects(prefix=path):
            name = name[path_len:]
            slash = name[1:-1].find('/') + 1
            if slash:
                dirs.add(name[:slash])
            elif name:
                files.append(name)
        dirs = list(dirs)
        dirs.sort()
        return (dirs, files)

    def size(self, name):
        """
        Returns the total size, in bytes, of the file specified by name.
        """
        return self._get_cloud_obj(name).size

    def url(self, name):
        """
        Returns an absolute URL where the file's contents can be accessed
        directly by a web browser.
        """
        return '%s/%s' % (self.container_url, name)

    def modified_time(self, name):
        # CloudFiles return modified date in different formats
        # depending on whether or not we pre-loaded objects.
        # When pre-loaded, timezone is not included but we
        # assume UTC. Since FileStorage returns localtime, and
        # collectstatic compares these dates, we need to depend 
        # on dateutil to help us convert timezones.
        try:
           from dateutil import parser, tz
        except ImportError:
            raise NotImplementedError("This functionality requires dateutil to be installed")

        obj = self.container.get_object(name)

        # convert to string to date
        date = parser.parse(obj.last_modified)

        # if the date has no timzone, assume UTC
        if date.tzinfo == None:
            date = date.replace(tzinfo=tz.tzutc())

        # convert date to local time w/o timezone
        date = date.astimezone(tz.tzlocal()).replace(tzinfo=None)
        return date


class CloudStorageDirectory(File):
    """
    A File-like object that creates a directory at cloudfiles
    """

    def __init__(self, name):
        super(CloudStorageDirectory, self).__init__(StringIO(), name=name)
        self.file.content_type = 'application/directory'
        self.size = 0

    def __str__(self):
        return 'directory'

    def __nonzero__(self):
        return True

    def open(self, mode=None):
        self.seek(0)

    def close(self):
        pass


class CloudFilesStaticStorage(CloudFilesStorage):
    """
    Subclasses CloudFilesStorage to automatically set the container to the one
    specified in CUMULUS['STATIC_CONTAINER']. This provides the ability to
    specify a separate storage backend for Django's collectstatic command.

    To use, make sure CUMULUS['STATIC_CONTAINER'] is set to something other
    than CUMULUS['CONTAINER']. Then, tell Django's staticfiles app by setting
    STATICFILES_STORAGE = 'cumulus.storage.CloudFilesStaticStorage'.
    """
    container_name = CUMULUS['STATIC_CONTAINER']


class CloudFilesStorageFile(File):
    closed = False

    def __init__(self, storage, name, *args, **kwargs):
        self._storage = storage
        self._pos = 0
        super(CloudFilesStorageFile, self).__init__(file=None, name=name,
                                                    *args, **kwargs)

    def _get_pos(self):
        return self._pos

    def _get_size(self):
        if not hasattr(self, '_size'):
            self._size = self._storage.size(self.name)
        return self._size

    def _set_size(self, size):
        self._size = size

    size = property(_get_size, _set_size)

    def _get_file(self):
        if not hasattr(self, '_file'):
            self._file = self._storage._get_cloud_obj(self.name)
            self._file.tell = self._get_pos
        return self._file

    def _set_file(self, value):
        if value is None:
            if hasattr(self, '_file'):
                del self._file
        else:
            self._file = value

    file = property(_get_file, _set_file)

    def read(self, num_bytes=0):
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
        return not hasattr(self, '_file')

    def seek(self, pos):
        self._pos = pos

class ThreadSafeCloudFilesStorage(CloudFilesStorage):
    """
    Extends CloudFilesStorage to make it mostly thread safe.

    As long as you don't pass container or cloud objects
    between threads, you'll be thread safe.

    Uses one cloudfiles connection per thread.
    """

    def __init__(self, *args, **kwargs):
        super(ThreadSafeCloudFilesStorage, self).__init__(*args, **kwargs)

        import threading
        self.local_cache = threading.local()

    def _get_connection(self):
        if not hasattr(self.local_cache, 'connection'):
            connection = cloudfiles.get_connection(self.username,
                                    self.api_key, **self.connection_kwargs)
            self.local_cache.connection = connection

        return self.local_cache.connection

    connection = property(_get_connection, CloudFilesStorage._set_connection)

    def _get_container(self):
        if not hasattr(self.local_cache, 'container'):
            container = self.connection.get_container(self.container_name)
            self.local_cache.container = container

        return self.local_cache.container

    container = property(_get_container, CloudFilesStorage._set_container)
