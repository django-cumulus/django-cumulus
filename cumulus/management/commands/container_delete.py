"""Delete a container.

Rackspace will only let us delete an empty container,
so first we have to list all the items in the container,
then delete them one by one. This can take a long time
for big containers.
"""

import multiprocessing
import optparse
import swiftclient
import sys
import time

from django.core.management.base import BaseCommand, CommandError

from cumulus.settings import CUMULUS
from Queue import Empty


class Command(BaseCommand):
    help = "Delete a container."
    args = "[container_name]"

    option_list = BaseCommand.option_list + (
        optparse.make_option("-y", "--yes", action="store_true", default=False,
                dest="is_yes", help="Assume Yes to confirmation question"),
        optparse.make_option("-w", "--workers", dest="workers", default=2,
            help="Number of workers to start. Default 50."),
        optparse.make_option("-b", "--batch-size", dest="batch_size", default=10,
            help="How many tasks to give to each worker. Default 10."))

    def set_options(self, options):
        self.marker = None
        self.is_fetch_done = False
        self.batch_size = 0
        self.is_yes = options.get("is_yes")
        self.num_workers = int(options.get("workers"))
        self.batch_size = int(options.get("batch_size"))

    def connect_container(self):
        """
        Connect using the swiftclient api.
        """
        self.conn = swiftclient.Connection(authurl=CUMULUS["AUTH_URL"],
                                           user=CUMULUS["USERNAME"],
                                           key=CUMULUS["API_KEY"],
                                           snet=CUMULUS["SERVICENET"])

    def handle(self, *args, **options):
        from datetime import datetime
        startTime = datetime.now()
        if len(args) != 1:
            raise CommandError("Pass one and only one [container_name] as an argument")
        container_name = args[0]
        if not self.is_yes:
            is_ok = raw_input("Permanently delete container {0}? [y|N]".format(container_name))
            if not is_ok == "y":
                raise CommandError("Aborted")

        self.set_options(options)
        self.connect_container()

        print("Connecting")
        container = self.conn.get_container(container_name)

        print("Deleting objects from container")
        cloud_objs = [cloud_file["name"] for cloud_file in container[1]]
        jobs = []
        print(len(cloud_objs))

        queue = multiprocessing.Queue
        processes = [multiprocessing.Process(target=delete,
                                             args=(container, cloud_obj))
                     for cloud_obj in cloud_objs]

            jobs.append(process)
            process.start()
        print(datetime.now()-startTime)
        # import ipdb; ipdb.set_trace()

        # queue = multiprocessing.Queue()
        # procs = [multiprocessing.Process(target=delete,
        #                                  args=(container,cloud_objs, queue))
        #         for _ in range(self.num_workers)]

        # for proc in procs:
        #     proc.start()
        # import ipdb; ipdb.set_trace()
        # while not queue.empty():
        #     sys.stdout.write("\rItems remaining: {0}                 ".format(
        #                         (queue.qsize() * self.batch_size)))
        #     sys.stdout.flush()
        #     time.sleep(1)

        #     if not self.is_fetch_done:
        #         self.fetch_more(container, queue)

        # print("Container empty. Waiting for final threads to finish.")
        # for proc in procs:
        #     proc.join()

        # print("Deleting container")
        # self.conn.delete_container(container)

    # def fetch_more(self, container, queue, limit=1000):
    #     """Fetch some more items from the container,
    #     and put them on the queue.
    #     """
    #     objs = None
    #     is_fetched = False
    #     while not is_fetched and limit > 5:
    #         try:
    #             objs = container.list_objects(limit=limit, marker=self.marker)
    #             is_fetched = True
    #         except IOError:
    #             is_fetched = False
    #             limit = limit / 2
    #             sys.stdout.write("\rBacking off. Limit: {0}    ".format(limit))
    #             sys.stdout.flush()
    #             time.sleep(1)

    #     if not objs:
    #         self.is_fetch_done = True
    #         return

    #     self.marker = objs[-1]

    #     # Batch them up onto queue
    #     while objs:
    #         batch = objs[:self.batch_size]
    #         objs = objs[self.batch_size:]

    #         queue.put(batch)

    # def delete_cloud_obj(self, cloud_obj):
    #     """
    #     Delete an object from the container.
    #     """
    #     self.conn.delete_object(container=self.container_name,
    #                             obj=cloud_obj)


def delete(container, cloud_obj):
    """Delete from cloudfiles. Runs in a separate process."""
    queue.get()
    # try:
    #     batch = queue.get_nowait()
    # except Empty:
    #     return
    # for name in batch:
    #     print("NAME: ")
    #     print(name)
    #     try:
    #         pass
    #     except Exception:
    #         pass
