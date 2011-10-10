"""Create a public (CDN) rackspace container.
"""

import sys

from django.core.management.base import BaseCommand, CommandError
import cloudfiles

from cumulus import settings

USAGE = 'django-admin.py container_create <container_name>'


class Command(BaseCommand):
    """Create a public container"""

    def handle(self, *args, **options):
        """Main"""

        if len(sys.argv) != 3:
            raise CommandError('Usage: %s' % USAGE)

        container_name = sys.argv[2]
        print('Creating container: %s' % container_name)

        conn = cloudfiles.get_connection(
                        username=settings.CUMULUS['USERNAME'],
                        api_key=settings.CUMULUS['API_KEY'])

        container = conn.create_container(container_name)
        container.make_public()

        print('Done')
