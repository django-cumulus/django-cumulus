import datetime
import fnmatch
import mimetypes
import optparse
import os
import pyrax
import re
import swiftclient

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError, NoArgsCommand


from cumulus.settings import CUMULUS
from cumulus.storage import sync_headers, get_gzipped_contents


class Command(NoArgsCommand):
    help = "Synchronizes static media to cloud files."
    option_list = NoArgsCommand.option_list + (
        optparse.make_option("-i", "--include", action="append", default=[],
                             dest="includes", metavar="PATTERN",
                             help="Include file or directories matching this glob-style "
                                  "pattern. Use multiple times to include more."),
        optparse.make_option("-e", "--exclude", action="append", default=[],
                             dest="excludes", metavar="PATTERN",
                             help="Exclude files or directories matching this glob-style "
                                  "pattern. Use multiple times to exclude more."),
        optparse.make_option("-w", "--wipe",
                             action="store_true", dest="wipe", default=False,
                             help="Wipes out entire contents of container first."),
        optparse.make_option("-t", "--test-run",
                             action="store_true", dest="test_run", default=False,
                             help="Performs a test run of the sync."),
        optparse.make_option("-q", "--quiet",
                             action="store_true", dest="test_run", default=False,
                             help="Do not display any output."),
        optparse.make_option("-c", "--container",
                             dest="container", help="Override STATIC_CONTAINER."),
    )

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
        if self.test_run:
            self.verbosity = 2
        cli_includes = options.get("includes")
        cli_excludes = options.get("excludes")

        # CUMULUS CONNECTION AND SETTINGS FROM SETTINGS.PY
        if not self.container_name:
            self.container_name = CUMULUS["STATIC_CONTAINER"]
        settings_includes = CUMULUS["INCLUDE_LIST"]
        settings_excludes = CUMULUS["EXCLUDE_LIST"]

        # PATH SETTINGS
        self.static_root = os.path.abspath(settings.STATIC_ROOT)
        self.static_url = settings.STATIC_URL
        if not self.static_root.endswith("/"):
            self.static_root = self.static_root + "/"
        if self.static_url.startswith("/"):
            self.static_url = self.static_url[1:]

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

    def connect_container(self):
        """
        Connects to a container using the swiftclient api.

        The container will be created and/or made public using the
        pyrax api if not already so.
        """
        self.conn = swiftclient.Connection(authurl=CUMULUS["AUTH_URL"],
                                           user=CUMULUS["USERNAME"],
                                           key=CUMULUS["API_KEY"],
                                           snet=CUMULUS["SERVICENET"],
                                           auth_version=CUMULUS["AUTH_VERSION"],
                                           tenant_name=CUMULUS["AUTH_TENANT_NAME"])
        try:
            self.conn.head_container(self.container_name)
        except swiftclient.client.ClientException as exception:
            if exception.msg == "Container HEAD failed":
                call_command("container_create", self.container_name)
            else:
                raise

        if CUMULUS["USE_PYRAX"]:
            if CUMULUS["PYRAX_IDENTITY_TYPE"]:
                pyrax.set_setting("identity_type", CUMULUS["PYRAX_IDENTITY_TYPE"])
            public = not CUMULUS["SERVICENET"]
            pyrax.set_credentials(CUMULUS["USERNAME"], CUMULUS["API_KEY"])
            connection = pyrax.connect_to_cloudfiles(region=CUMULUS["REGION"],
                                                     public=public)
            container = connection.get_container(self.container_name)
            if not container.cdn_enabled:
                container.make_public(ttl=CUMULUS["TTL"])
        else:
            headers = {"X-Container-Read": ".r:*"}
            self.conn.post_container(self.container_name, headers=headers)

        self.container = self.conn.get_container(self.container_name)

    def handle_noargs(self, *args, **options):
        # setup
        self.set_options(options)
        self.connect_container()

        # wipe first
        if self.wipe:
            self.wipe_container()

        # match local files
        abspaths = self.match_local(self.static_root, self.includes, self.excludes)
        relpaths = []
        for path in abspaths:
            filename = path.split(self.static_root)[1]
            if filename.startswith("/"):
                filename = filename[1:]
            relpaths.append(filename)
        if not relpaths:
            raise CommandError("The STATIC_ROOT directory is empty "
                               "or all files have been ignored.")
        for path in abspaths:
            if not os.path.isfile(path):
                raise CommandError("Unsupported filetype: {0}.".format(path))

        # match cloud objects
        cloud_objs = self.match_cloud(self.includes, self.excludes)

        # sync
        self.upload_files(abspaths, relpaths)
        self.delete_extra_files(relpaths, cloud_objs)

        if not self.quiet or self.verbosity > 1:
            self.print_tally()

    def match_cloud(self, includes, excludes):
        """
        Returns the cloud objects that match the include and exclude patterns.
        """
        cloud_objs = [cloud_obj["name"] for cloud_obj in self.container[1]]
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

    def upload_files(self, abspaths, relpaths):
        """
        Determines files to be uploaded and call ``upload_file`` on each.
        """
        for relpath in relpaths:
            abspath = [p for p in abspaths if p.endswith(relpath)][0]
            try:
                head = self.conn.head_object(self.container_name, relpath)
            except swiftclient.client.ClientException as exception:
                if exception.msg != "Object HEAD failed":
                    raise exception
                self.upload_file(abspath, relpath)
                continue
            cloud_datetime = (head["last-modified"] and
                              datetime.datetime.strptime(
                                  head["last-modified"],
                                  "%a, %d %b %Y %H:%M:%S %Z")
                              or None)
            local_datetime = datetime.datetime.utcfromtimestamp(os.stat(abspath).st_mtime)

            if cloud_datetime and local_datetime < cloud_datetime:
                self.skip_count += 1
                if not self.quiet:
                    print("Skipped {0}: not modified.".format(relpath))
                continue
            self.upload_file(abspath, relpath)

    def upload_file(self, abspath, cloud_filename):
        """
        Uploads a file to the container.
        """
        if not self.test_run:
            headers = None
            contents = open(abspath, "rb")
            size = os.stat(abspath).st_size

            mime_type, encoding = mimetypes.guess_type(abspath)
            if mime_type in CUMULUS.get("GZIP_CONTENT_TYPES", []):
                headers = {'Content-Encoding': 'gzip'}
                contents = get_gzipped_contents(contents)
                size = contents.size

            self.conn.put_object(container=self.container_name,
                                 obj=cloud_filename,
                                 contents=contents,
                                 content_length=size,
                                 etag=None,
                                 content_type=mime_type,
                                 headers=headers)
            # TODO syncheaders
            #sync_headers(cloud_obj)
        self.create_count += 1
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
        self.conn.delete_object(container=self.container_name,
                                obj=cloud_obj)

    def wipe_container(self):
        """
        Completely wipes out the contents of the container.
        """
        if self.test_run:
            print("Wipe would delete {0} objects.".format(len(self.container[1])))
        else:
            if not self.quiet or self.verbosity > 1:
                print("Deleting {0} objects...".format(len(self.container[1])))
            for cloud_obj in self.container[1]:
                self.conn.delete_object(self.container_name, cloud_obj["name"])

    def print_tally(self):
        """
        Prints the final tally to stdout.
        """
        self.update_count = self.upload_count - self.create_count
        if self.test_run:
            print("Test run complete with the following results:")
        print("Skipped {0}. Created {1}. Updated {2}. Deleted {3}.".format(
            self.skip_count, self.create_count, self.update_count, self.delete_count))
