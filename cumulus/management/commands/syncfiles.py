import datetime
import fnmatch
import os
import re

from django.conf import settings
from django.core.management.base import CommandError, BaseCommand


from cumulus.authentication import Auth
from cumulus.settings import CUMULUS
from cumulus.storage import get_headers, get_content_type, get_gzipped_contents


class Command(BaseCommand):
    help = "Synchronizes project static *or* media files to cloud files."

    def add_arguments(self, parser):
        parser.add_argument("-i", "--include", action="append", default=[],
                             dest="includes", metavar="PATTERN",
                             help="Include file or directories matching this glob-style "
                                  "pattern. Use multiple times to include more."),
        parser.add_argument("-e", "--exclude", action="append", default=[],
                             dest="excludes", metavar="PATTERN",
                             help="Exclude files or directories matching this glob-style "
                                  "pattern. Use multiple times to exclude more."),
        parser.add_argument("-w", "--wipe",
                             action="store_true", dest="wipe", default=False,
                             help="Wipes out entire contents of container first."),
        parser.add_argument("-t", "--test-run",
                             action="store_true", dest="test_run", default=False,
                             help="Performs a test run of the sync."),
        parser.add_argument("-q", "--quiet",
                             action="store_true", dest="test_run", default=False,
                             help="Do not display any output."),
        parser.add_argument("-c", "--container",
                             dest="container", help="Override STATIC_CONTAINER."),
        parser.add_argument("-s", "--static",
                             action="store_true", dest="syncstatic", default=False,
                             help="Sync static files located at settings.STATIC_ROOT path."),
        parser.add_argument("-m", "--media",
                             action="store_true", dest="syncmedia", default=False,
                             help="Sync media files located at settings.MEDIA_ROOT path."),

    def set_options(self, options):
        """
        Sets instance variables based on an options dict
        """
        # COMMAND LINE OPTIONS
        self.wipe = options.get("wipe")
        self.test_run = options.get("test_run")
        self.quiet = options.get("test_run")
        self.container_name = options.get("container")
        self.verbosity = int(options.get("verbosity"))
        self.syncmedia = options.get("syncmedia")
        self.syncstatic = options.get("syncstatic")
        if self.test_run:
            self.verbosity = 2
        cli_includes = options.get("includes")
        cli_excludes = options.get("excludes")

        # CUMULUS CONNECTION AND SETTINGS FROM SETTINGS.PY
        if self.syncmedia and self.syncstatic:
            raise CommandError("options --media and --static are mutually exclusive")
        if not self.container_name:
            if self.syncmedia:
                self.container_name = CUMULUS["CONTAINER"]
            elif self.syncstatic:
                self.container_name = CUMULUS["STATIC_CONTAINER"]
            else:
                raise CommandError("must select one of the required options, either --media or --static")
        settings_includes = CUMULUS["INCLUDE_LIST"]
        settings_excludes = CUMULUS["EXCLUDE_LIST"]

        # PATH SETTINGS
        if self.syncmedia:
            self.file_root = os.path.abspath(settings.MEDIA_ROOT)
            self.file_url = settings.MEDIA_URL
        elif self.syncstatic:
            self.file_root = os.path.abspath(settings.STATIC_ROOT)
            self.file_url = settings.STATIC_URL
        if not self.file_root.endswith("/"):
            self.file_root = self.file_root + "/"
        if self.file_url.startswith("/"):
            self.file_url = self.file_url[1:]

        # SYNCSTATIC VARS
        # combine includes and excludes from the cli and django settings file
        self.includes = list(set(cli_includes + settings_includes))
        self.excludes = list(set(cli_excludes + settings_excludes))
        # transform glob patterns to regular expressions
        self.local_filenames = []
        self.create_count = 0
        self.upload_count = 0
        self.update_count = 0
        self.skip_count = 0
        self.delete_count = 0

    def handle_noargs(self, *args, **options):
        # setup
        self.set_options(options)
        self._connection = Auth()._get_connection()
        self.container = self._connection.get_container(self.container_name)

        # wipe first
        if self.wipe:
            self.wipe_container()

        # match local files
        abspaths = self.match_local(self.file_root, self.includes, self.excludes)
        relpaths = []
        for path in abspaths:
            filename = path.split(self.file_root)[1]
            if filename.startswith("/"):
                filename = filename[1:]
            relpaths.append(filename)

        if not relpaths:
            settings_root_prefix = "MEDIA" if self.syncmedia else "STATIC"
            raise CommandError("The {0}_ROOT directory is empty "
                               "or all files have been ignored.".format(settings_root_prefix))

        for path in abspaths:
            if not os.path.isfile(path):
                raise CommandError("Unsupported filetype: {0}.".format(path))

        # match cloud objects
        cloud_objs = self.match_cloud(self.includes, self.excludes)

        remote_objects = {
            obj.name: datetime.datetime.strptime(
                obj.last_modified,
                "%Y-%m-%dT%H:%M:%S.%f") for obj in self.container.get_objects()
        }

        # sync
        self.upload_files(abspaths, relpaths, remote_objects)
        self.delete_extra_files(relpaths, cloud_objs)

        if not self.quiet or self.verbosity > 1:
            self.print_tally()

    def match_cloud(self, includes, excludes):
        """
        Returns the cloud objects that match the include and exclude patterns.
        """
        cloud_objs = [cloud_obj.name for cloud_obj in self.container.get_objects()]
        includes_pattern = r"|".join([fnmatch.translate(x) for x in includes])
        excludes_pattern = r"|".join([fnmatch.translate(x) for x in excludes]) or r"$."
        excludes = [o for o in cloud_objs if re.match(excludes_pattern, o)]
        includes = [o for o in cloud_objs if re.match(includes_pattern, o)]
        return [o for o in includes if o not in excludes]

    def match_local(self, prefix, includes, excludes):
        """
        Filters os.walk() with include and exclude patterns.
        See: http://stackoverflow.com/a/5141829/93559
        """
        includes_pattern = r"|".join([fnmatch.translate(x) for x in includes])
        excludes_pattern = r"|".join([fnmatch.translate(x) for x in excludes]) or r"$."
        matches = []
        for root, dirs, files in os.walk(prefix, topdown=True):
            # exclude dirs
            dirs[:] = [os.path.join(root, d) for d in dirs]
            dirs[:] = [d for d in dirs if not re.match(excludes_pattern,
                                                       d.split(root)[1])]
            # exclude/include files
            files = [os.path.join(root, f) for f in files]
            files = [os.path.join(root, f) for f in files
                     if not re.match(excludes_pattern, f)]
            files = [os.path.join(root, f) for f in files
                     if re.match(includes_pattern, f.split(prefix)[1])]
            for fname in files:
                matches.append(fname)
        return matches

    def upload_files(self, abspaths, relpaths, remote_objects):
        """
        Determines files to be uploaded and call ``upload_file`` on each.
        """
        for relpath in relpaths:
            abspath = [p for p in abspaths if p[len(self.file_root):] == relpath][0]
            cloud_datetime = remote_objects[relpath] if relpath in remote_objects else None
            local_datetime = datetime.datetime.utcfromtimestamp(os.stat(abspath).st_mtime)

            if cloud_datetime and local_datetime < cloud_datetime:
                self.skip_count += 1
                if not self.quiet:
                    print("Skipped {0}: not modified.".format(relpath))
                continue
            if relpath in remote_objects:
                self.update_count += 1
            else:
                self.create_count += 1
            self.upload_file(abspath, relpath)

    def upload_file(self, abspath, cloud_filename):
        """
        Uploads a file to the container.
        """
        if not self.test_run:
            content = open(abspath, "rb")
            content_type = get_content_type(cloud_filename, content)
            headers = get_headers(cloud_filename, content_type)

            if headers.get("Content-Encoding") == "gzip":
                content = get_gzipped_contents(content)
                size = content.size
            else:
                size = os.stat(abspath).st_size
            self.container.create(
                obj_name=cloud_filename,
                data=content,
                content_type=content_type,
                content_length=size,
                content_encoding=headers.get("Content-Encoding", None),
                headers=headers,
                ttl=CUMULUS["FILE_TTL"],
                etag=None,
            )

        self.upload_count += 1
        if not self.quiet or self.verbosity > 1:
            print("Uploaded: {0}".format(cloud_filename))

    def delete_extra_files(self, relpaths, cloud_objs):
        """
        Deletes any objects from the container that do not exist locally.
        """
        for cloud_obj in cloud_objs:
            if cloud_obj not in relpaths:
                if not self.test_run:
                    self.delete_cloud_obj(cloud_obj)
                self.delete_count += 1
                if not self.quiet or self.verbosity > 1:
                    print("Deleted: {0}".format(cloud_obj))

    def delete_cloud_obj(self, cloud_obj):
        """
        Deletes an object from the container.
        """
        self._connection.delete_object(
            container=self.container_name,
            obj=cloud_obj,
        )

    def wipe_container(self):
        """
        Completely wipes out the contents of the container.
        """
        if self.test_run:
            print("Wipe would delete {0} objects.".format(len(self.container.object_count)))
        else:
            if not self.quiet or self.verbosity > 1:
                print("Deleting {0} objects...".format(len(self.container.object_count)))
            self._connection.delete_all_objects()

    def print_tally(self):
        """
        Prints the final tally to stdout.
        """
        self.update_count = self.upload_count - self.create_count
        if self.test_run:
            print("Test run complete with the following results:")
        print("Skipped {0}. Created {1}. Updated {2}. Deleted {3}.".format(
            self.skip_count, self.create_count, self.update_count, self.delete_count))
