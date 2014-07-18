import optparse

from django.core.management.base import BaseCommand, CommandError

from cumulus.authentication import Auth
from cumulus.settings import CUMULUS


class Command(BaseCommand):
    help = "Create a container."
    args = "[container_name]"

    option_list = BaseCommand.option_list + (
        optparse.make_option("-p", "--private", action="store_true", default=False,
                             dest="private", help="Make a private container."),)

    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError("Pass one and only one [container_name] as an argument")

        self._connection = Auth()._get_connection()

        container_name = args[0]
        print("Creating container: {0}".format(container_name))
        container = self._connection.create_container(container_name)
        if options.get("private"):
            print("Private container: {0}".format(container_name))
            container.make_private()
        else:
            print("Public container: {0}".format(container_name))
            container.make_public(ttl=CUMULUS["TTL"])
