import optparse
import pyrax
import swiftclient

from django.core.management.base import BaseCommand

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
                                           snet=CUMULUS["SERVICENET"],
                                           auth_version=CUMULUS["AUTH_VERSION"],
                                           tenant_name=CUMULUS["AUTH_TENANT_NAME"])

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
            if CUMULUS["USE_PYRAX"]:
                if CUMULUS["PYRAX_IDENTITY_TYPE"]:
                    pyrax.set_setting("identity_type", CUMULUS["PYRAX_IDENTITY_TYPE"])
                pyrax.set_credentials(CUMULUS["USERNAME"], CUMULUS["API_KEY"])
                public = not CUMULUS["SERVICENET"]
                connection = pyrax.connect_to_cloudfiles(region=CUMULUS["REGION"],
                                                         public=public)
                metadata = connection.get_container_cdn_metadata(container_name)
                if "x-cdn-enabled" not in metadata or metadata["x-cdn-enabled"] == "False":
                    uri = "NOT PUBLIC"
                else:
                    uri = metadata["x-cdn-uri"]
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
            else:
                headers, data = self.conn.get_container(container_name)
                print(headers)
                print(data)
