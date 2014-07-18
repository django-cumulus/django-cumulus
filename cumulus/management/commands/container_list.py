from django.core.management.base import BaseCommand, CommandError

from cumulus.authentication import Auth


class Command(BaseCommand):
    help = ("List all the items in a container to stdout.\n\n"
            "We recommend you run it like this:\n"
            "    ./manage.py container_list <container> | pv --line-mode > <container>.list\n\n"
            "pv is Pipe Viewer: http://www.ivarch.com/programs/pv.shtml")
    args = "[container_name]"

    def handle(self, *args, **options):
        """
        Lists all the items in a container to stdout.
        """
        self._connection = Auth()._get_connection()

        if len(args) == 0:
            containers = self._connection.list_containers()
            if not containers:
                print("No containers were found for this account.")
        elif len(args) == 1:
            containers = self._connection.list_container_object_names(args[0])
            if not containers:
                print("No matching container found.")
        else:
            raise CommandError("Pass one and only one [container_name] as an argument")

        for container in containers:
            print(container)
