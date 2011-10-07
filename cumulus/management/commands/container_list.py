"""List all the items in a rackspace cloudfiles container to stdout.

Usage: django-admin.py container_list <container_name>
We recommend you run it like this:

 django-admin.py container_list <container> | pv --line-mode > <container>.list

pv is Pipe Viewer: http://www.ivarch.com/programs/pv.shtml
"""

import pprint
import time

import cloudfiles
from django.core.management.base import BaseCommand
from cumulus import settings

MAX_LIMIT = 1000    # The most rackspace will give us in one request
MIN_LIMIT = 200     # The least we'll tolerate


class Command(BaseCommand):
    """Django management command"""

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.connection = None

    def handle(self, *args, **options):
        """Main"""

        self.connection = cloudfiles.Connection(
                settings.CUMULUS['USERNAME'],
                settings.CUMULUS['API_KEY'])

        if len(args) == 1:
            lister = ContainerLister(self.connection, args[0])
            lister.run()

        else:
            self.list_all_containers()

    def list_all_containers(self):
        """Print a list of all containers"""

        print('...Listing containers...')

        containers = self.connection.list_containers()

        print('Please specify one of the following containers:')
        pprint.pprint(containers)


class ContainerLister(object):
    """List objects in a container.

    Rackspace only returns up to 1000 at a time,
    so we keep requesting the next set until we get
    an empty one.
    """

    def __init__(self, connection, container_name):

        self.connection = connection
        self.container = connection.get_container(container_name)

        self.limit = MAX_LIMIT
        self.marker = None
        self.is_done = False

    def run(self):
        """Prints names of items in container to stdout"""

        while not self.is_done:
            self.list_more()

    def list_more(self):
        """List more items"""

        try:
            objs = self.container.list_objects(
                    limit=self.limit,
                    marker=self.marker)

            if objs:
                self.marker = objs[-1]

                for item in objs:
                    print(item)

            else:
                self.is_done = True

            if self.limit <= MIN_LIMIT:
                # Maybe rackspace is better now
                self.limit = MAX_LIMIT

        except IOError:
            # Rackspace is timing out, fetch less and pause.
            self.limit = self.limit / 2
            time.sleep(1)

