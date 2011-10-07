import cloudfiles
import optparse

from cumulus import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    args = "[container_name container_name ...]"
    help = "Display info for cloud files containers"

    option_list = BaseCommand.option_list + (
        optparse.make_option('-n', '--name', action='store_true', dest='name', default=False),
        optparse.make_option('-c', '--count', action='store_true', dest='count', default=False),
        optparse.make_option('-s', '--size', action='store_true', dest='size', default=False),
        optparse.make_option('-u', '--uri', action='store_true', dest='uri', default=False)
    )

    def handle(self, *args, **options):
        USERNAME = settings.CUMULUS['USERNAME']
        API_KEY = settings.CUMULUS['API_KEY']

        conn = cloudfiles.get_connection(USERNAME, API_KEY)
        if args:
            containers = []
            for container_name in args:
                try:
                    container = conn.get_container(container_name)
                except cloudfiles.errors.NoSuchContainer:
                    raise CommandError("Container does not exist: %s" % container_name)
                containers.append(container)
        else:
            containers = conn.get_all_containers()

        opts = ['name', 'count', 'size', 'uri']

        for container in containers:
            info = {
                'name': container.name,
                'count': container.object_count,
                'size': container.size_used,
                'uri': container.public_uri() if container.is_public() else "NOT PUBLIC",
            }
            output = [str(info[o]) for o in opts if options.get(o)]
            if not output:
                output = [str(info[o]) for o in opts]
            print ', '.join(output)

        if not containers:
            print 'No containers found.'
