from django.core.management.base import BaseCommand

from cumulus.authentication import Auth


class Command(BaseCommand):
    help = "Display info for containers"
    args = "[container_name container_name ...]"

    def add_arguments(self, parser):
        parser.add_argument("-n", "--name", action="store_true", dest="name", default=False),
        parser.add_argument("-c", "--count", action="store_true", dest="count", default=False),
        parser.add_argument("-s", "--size", action="store_true", dest="size", default=False),
        parser.add_argument("-u", "--uri", action="store_true", dest="uri", default=False)

    def handle(self, *args, **options):
        self._connection = Auth()._get_connection()

        container_names = self._connection.list_container_names()

        if args:
            matches = []
            for container_name in container_names:
                if container_name in args:
                    matches.append(container_name)
            container_names = matches

        if not container_names:
            print("No containers found.")
            return

        if not args:
            account_details = self._connection.get_account_details()
            print("container_count | object_count | bytes_used")
            print("{0}, {1}, {2}\n".format(
                account_details["container_count"],
                account_details["object_count"],
                account_details["bytes_used"],
            ))

        opts = ["name", "count", "size", "uri"]
        output = [o for o in opts if options.get(o)]

        if output:
            print(" | ".join(output))
        else:
            print(" | ".join(opts))

        for container_name in container_names:
            container = self._connection.get_container(container_name)
            info = {
                "name": container.name,
                "count": container.object_count,
                "size": container.total_bytes,
                "cdn_enabled": container.cdn_enabled,
                "uri": container.cdn_uri if container.cdn_enabled else None,
            }
            output = [str(info[o]) for o in opts if options.get(o)]
            if not output:
                output = [str(info[o]) for o in opts]
            print(", ".join(output))
