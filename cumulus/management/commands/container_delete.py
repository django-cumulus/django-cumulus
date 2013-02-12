import datetime
import multiprocessing
import optparse
import swiftclient

from django.core.management.base import BaseCommand, CommandError

from cumulus.settings import CUMULUS


class Command(BaseCommand):
    help = "Delete a container."
    args = "[container_name]"

    option_list = BaseCommand.option_list + (
        optparse.make_option("-y", "--yes", action="store_true", default=False,
                             dest="is_yes", help="Assume Yes to confirmation question"),)

    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError("Pass one and only one [container_name] as an argument")
        container_name = args[0]
        if not options.get("is_yes"):
            is_ok = input("Permanently delete container {0}? [y|N]".format(container_name))
            if not is_ok == "y":
                raise CommandError("Aborted")

        conn = swiftclient.Connection(authurl=CUMULUS["AUTH_URL"],
                                      user=CUMULUS["USERNAME"],
                                      key=CUMULUS["API_KEY"],
                                      snet=CUMULUS["SERVICENET"],
                                      auth_version=CUMULUS["AUTH_VERSION"],
                                      tenant_name=CUMULUS["AUTH_TENANT_NAME"])

        print("Connecting")
        container = conn.get_container(container_name)

        print("Deleting objects from container {0}".format(container_name))
        # divide the objects to delete equally into one list per processor
        cloud_objs = [cloud_obj["name"] for cloud_obj in container[1]]
        nbr_chunks = multiprocessing.cpu_count()
        chunk_size = len(cloud_objs) / nbr_chunks
        if len(cloud_objs) % nbr_chunks != 0:
            chunk_size += 1
        chunks = [[container_name, cloud_objs[x * chunk_size:(x + 1) * chunk_size]]
                  for x in range(nbr_chunks)]
        # create a Pool which will create Python processes
        p = multiprocessing.Pool()
        start_time = datetime.datetime.now()
        # send out the work chunks to the Pool
        po = p.map_async(delete_cloud_objects, chunks)
        # we get a list of lists back, one per chunk, so we have to
        # flatten them back together
        # po.get() will block until results are ready and then
        # return a list of lists of results: [[cloud_obj], [cloud_obj]]
        results = po.get()
        output = []
        for res in results:
            output += res
        if output != cloud_objs:
            print("Deletion failure")
        conn.delete_container(container_name)
        print(datetime.datetime.now() - start_time)
        print("Deletion complete")


def delete_cloud_objects(chunk):
    """Deletes cloud objects. Runs in a separate process."""
    container_name, cloud_objs = chunk
    conn = swiftclient.Connection(authurl=CUMULUS["AUTH_URL"],
                                  user=CUMULUS["USERNAME"],
                                  key=CUMULUS["API_KEY"],
                                  snet=CUMULUS["SERVICENET"],
                                  auth_version=CUMULUS["AUTH_VERSION"],
                                  tenant_name=CUMULUS["AUTH_TENANT_NAME"])
    filter(None, cloud_objs)
    deleted = []
    for cloud_obj in cloud_objs:
        conn.delete_object(container=container_name,
                           obj=cloud_obj)
        deleted.append(cloud_obj)
    return deleted
