import StringIO
import swiftclient
import optparse

from django.core.management.base import BaseCommand, CommandError

from cumulus.cloudfiles_cdn import CloudfilesCDN
from cumulus.settings import CUMULUS


class Command(BaseCommand):
    help = "Display info for containers"
    args = "[container_name container_name ...]"

    option_list = BaseCommand.option_list + (
        optparse.make_option("-n", "--name", action="store_true", dest="name", default=False),
        optparse.make_option("-c", "--count", action="store_true", dest="count", default=False),
        optparse.make_option("-s", "--size", action="store_true", dest="size", default=False),
        optparse.make_option("-u", "--uri", action="store_true", dest="uri", default=False)
    )

    def connect(self):
        """
        Connect using the swiftclient api and the cloudfiles api.
        """
        self.conn = swiftclient.Connection(authurl=CUMULUS["AUTH_URL"],
                                           user=CUMULUS["USERNAME"],
                                           key=CUMULUS["API_KEY"],
                                           snet=CUMULUS["SERVICENET"])
        self.cloudfiles_cdn = CloudfilesCDN()

    def handle(self, *args, **options):
        self.connect()
        account = self.conn.get_account()
        if args:
            container_names = args
        else:
            container_names = [c["name"] for c in account[1]]
        containers = {}
        for container_name in container_names:
            containers[container_name] = self.conn.head_container(container_name)

        if not containers:
            print("No containers found.")
            return

        if not args:
            print("{0}, {1}, {2}\n".format(
                account[0]["x-account-container-count"],
                account[0]["x-account-object-count"],
                account[0]["x-account-bytes-used"],
            ))

        opts = ["name", "count", "size", "uri"]
        for container_name, values in containers.iteritems():
            uri = self.cloudfiles_cdn.public_uri(container_name)
            if not uri:
                uri = "NOT PUBLIC"
            info = {
                "name": container_name,
                "count": values["x-container-object-count"],
                "size": values["x-container-bytes-used"],
                "uri": uri,
            }
            output = [str(info[o]) for o in opts if options.get(o)]
            if not output:
                output = [str(info[o]) for o in opts]
            print(", ".join(output))
