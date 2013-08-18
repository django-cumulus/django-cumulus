import optparse
import pyrax
import swiftclient

from django.core.management.base import BaseCommand, CommandError

from cumulus.settings import CUMULUS


class Command(BaseCommand):
    help = "Create a container."
    args = "[container_name]"

    option_list = BaseCommand.option_list + (
        optparse.make_option("-p", "--private", action="store_true", default=False,
                             dest="private", help="Make a private container."),)

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
        if len(args) != 1:
            raise CommandError("Pass one and only one [container_name] as an argument")
        self.connect()
        container_name = args[0]
        print("Creating container: {0}".format(container_name))
        self.conn.put_container(container_name)
        if not options.get("private"):
            print("Publish container: {0}".format(container_name))
            if CUMULUS["USE_PYRAX"]:
                if CUMULUS["PYRAX_IDENTITY_TYPE"]:
                    pyrax.set_setting("identity_type", CUMULUS["PYRAX_IDENTITY_TYPE"])
                pyrax.set_credentials(CUMULUS["USERNAME"], CUMULUS["API_KEY"])
                public = not CUMULUS["SERVICENET"]
                connection = pyrax.connect_to_cloudfiles(region=CUMULUS["REGION"],
                                                         public=public)
                container = connection.get_container(container_name)
                if not container.cdn_enabled:
                    container.make_public(ttl=CUMULUS["TTL"])
            else:
                headers = {"X-Container-Read": ".r:*"}
                self.conn.post_container(container_name, headers=headers)
        print("Done")
