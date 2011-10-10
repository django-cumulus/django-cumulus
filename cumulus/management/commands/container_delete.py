"""Delete a Rackspace CloudFiles container.

Rackspace will only let us delete an empty container,
so first we have to list all the items in the container,
then delete them one by one. This can take a long time
for big containers.
"""

import sys
import time
from optparse import make_option
from Queue import Empty
import multiprocessing

from django.core.management.base import BaseCommand, CommandError
import cloudfiles

from cumulus import settings

USAGE = 'django-admin.py container_delete <container_name>'


class Command(BaseCommand):
    """Delete a container"""

    option_list = BaseCommand.option_list + (
            make_option(
                '--yes',
                action='store_true',
                dest='is_yes',
                default=False,
                help='Assume Yes to confirmation question'),
            make_option(
                '--workers',
                dest='workers',
                default=50,
                help='Number of workers to start. Default 50.'),
            make_option(
                '--batch-size',
                dest='batch_size',
                default=10,
                help='How many tasks to give to each worker. Default 10.')
        )

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.marker = None
        self.is_fetch_done = False
        self.batch_size = 0

    def handle(self, *args, **options):
        """Main"""

        if len(args) != 1:
            raise CommandError('Usage: %s' % USAGE)

        container_name = args[0]

        is_yes = options.get('is_yes')
        num_workers = int(options.get('workers'))
        self.batch_size = int(options.get('batch_size'))

        print('Connecting')
        conn = cloudfiles.get_connection(
                username=settings.CUMULUS['USERNAME'],
                api_key=settings.CUMULUS['API_KEY'])
        container = conn.get_container(container_name)

        if not is_yes:
            is_ok = raw_input('Permanently delete container %s? [y|N]' %
                                container)
            if not is_ok == 'y':
                raise CommandError('Aborted')

        queue = multiprocessing.Queue()

        print('Listing objects in container')
        while not self.is_fetch_done and queue.qsize() < (num_workers * 2):
            sys.stdout.write('\rQueued batches: %d. Need: %d ' %
                    (queue.qsize(), (num_workers * 2)))
            sys.stdout.flush()
            self.fetch_more(container, queue)

        print('Deleting objects from container')

        procs = [multiprocessing.Process(target=delete,
                                         args=(container, queue))
                for _ in range(num_workers)]

        for proc in procs:
            proc.start()

        print('')
        while not queue.empty():
            sys.stdout.write('\rItems remaining: %d                 ' %
                                (queue.qsize() * self.batch_size))
            sys.stdout.flush()
            time.sleep(1)

            if not self.is_fetch_done:
                self.fetch_more(container, queue)

        print('Container empty. Waiting for final threads to finish.')
        for proc in procs:
            proc.join()

        print('Deleting container')
        conn.delete_container(container)

    def fetch_more(self, container, queue, limit=1000):
        """Fetch some more items from the container,
        and put them on the queue.
        """

        objs = None
        is_fetched = False
        while not is_fetched and limit > 5:
            try:
                objs = container.list_objects(limit=limit, marker=self.marker)
                is_fetched = True
            except IOError:
                is_fetched = False
                limit = limit / 2
                sys.stdout.write('\rBacking off. Limit: %d    ' % limit)
                sys.stdout.flush()
                time.sleep(1)

        if not objs:
            self.is_fetch_done = True
            return

        self.marker = objs[-1]

        # Batch them up onto queue
        while objs:
            batch = objs[:self.batch_size]
            objs = objs[self.batch_size:]

            queue.put(batch)


def delete(container, queue):
    """Delete from cloudfiles. Runs in a separate process."""

    while 1:

        try:
            batch = queue.get_nowait()
        except Empty:
            return

        for name in batch:
            try:
                container.delete_object(name)
            except Exception:
                pass

