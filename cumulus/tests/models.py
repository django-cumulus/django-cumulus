from django.db import models

from cumulus.storage import SwiftclientStorage

openstack_storage = SwiftclientStorage()


class Thing(models.Model):
    "A dummy model to use for tests."
    image = models.ImageField(storage=openstack_storage,
                              upload_to="cumulus-tests",
                              blank=True)
    document = models.FileField(storage=openstack_storage, upload_to="cumulus-tests")
    custom = models.FileField(storage=openstack_storage, upload_to="cumulus-tests")
