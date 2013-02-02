import swiftclient
import sys

from django.core.management.base import BaseCommand, CommandError

from cumulus.settings import CUMULUS


class Command(BaseCommand):
    help = "Create a container."
    args = "[container_name]"

    def connect(self):
        """
        Connect using the swiftclient api.
        """
        self.conn = swiftclient.Connection(authurl=CUMULUS["AUTH_URL"],
                                           user=CUMULUS["USERNAME"],
                                           key=CUMULUS["API_KEY"],
                                           snet=CUMULUS["SERVICENET"])

    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError("Pass one and only one [container_name] as an argument")
        self.connect()
        container_name = args[0]
        print("Creating container: {0}".format(container_name))
        self.conn.put_container(container_name)
        print("Done")
