from django.core.management.base import BaseCommand, CommandError

from cumulus.authentication import Auth


class Command(BaseCommand):
    help = "Delete a container."
    args = "[container_name]"

    def add_arguments(self, parser):
        parser.add_argument('-y', '--yes', action='store_true', default=False,
                            dest='is_yes', help='Assume Yes to confiramtion question')

    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError("Pass one and only one [container_name] as an argument")
        container_name = args[0]
        if not options.get("is_yes"):
            is_ok = raw_input("Permanently delete container {0}? [y|N] ".format(
                container_name))
            if not is_ok == "y":
                raise CommandError("Aborted")

        print("Connecting")
        self._connection = Auth()._get_connection()
        container = self._connection.get_container(container_name)
        print("Deleting objects from container {0}".format(container_name))
        container.delete_all_objects()
        container.delete()
        print("Deletion complete")
