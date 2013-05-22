import swiftclient

from django.core.management.base import BaseCommand, CommandError

from cumulus.settings import CUMULUS


class Command(BaseCommand):
    help = ("List all the items in a container to stdout.\n\n"
            "We recommend you run it like this:\n"
            "    ./manage.py container_list <container> | pv --line-mode > <container>.list\n\n"
            "pv is Pipe Viewer: http://www.ivarch.com/programs/pv.shtml")
    args = "[container_name]"

    def connect(self):
        """
        Connects using the swiftclient api.
        """
        self.conn = swiftclient.Connection(authurl=CUMULUS["AUTH_URL"],
                                           user=CUMULUS["USERNAME"],
                                           key=CUMULUS["API_KEY"],
                                           snet=CUMULUS["SERVICENET"],
                                           auth_version=CUMULUS["AUTH_VERSION"],
                                           tenant_name=CUMULUS["AUTH_TENANT_NAME"])

    def handle(self, *args, **options):
        """
        Lists all the items in a container to stdout.
        """
        if len(args) == 0:
            self.connect()
            self.list_all_containers()
        elif len(args) == 1:
            self.connect()
            self.container = self.conn.get_container(args[0])
            for cloudfile in self.container[1]:
                print(cloudfile["name"])
        else:
            raise CommandError("Pass one and only one [container_name] as an argument")

    def list_all_containers(self):
        """
        Prints a list of all containers.
        """
        print("...Listing containers...")

        containers = self.conn.get_account()[1]
        if containers:
            print("Please specify one of the following containers:")
            for container in containers:
                print(container["name"])
        else:
            print("No containers were found for this account.")
