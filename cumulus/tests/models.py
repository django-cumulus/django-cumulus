from django.db import models

from cumulus.settings import CUMULUS
from cumulus.storage import CumulusStorage

# Different container names for model.
openstack_storage = CumulusStorage()
openstack_storage.container_name = CUMULUS['CONTAINER']


class Thing(models.Model):
    """
    A dummy model to use for tests.
    """
    document = models.FileField(storage=openstack_storage, upload_to='cumulus-tests')
    custom = models.FileField(storage=openstack_storage, upload_to='cumulus-tests')

    def delete(self, using=None):
        """
        Delete by removing the files from its storage first,
        then proceeding with super's delete.
        """
        self.document.delete()
        self.custom.delete()

        super(Thing, self).delete()

# Different container names for model.
openstack_storage_static = CumulusStorage()
openstack_storage_static.container_name = CUMULUS['STATIC_CONTAINER']


class StaticThing(models.Model):
    """
    A dummy model to use for tests.
    """
    image = models.ImageField(storage=openstack_storage_static, upload_to='cumulus-tests')
    document = models.FileField(storage=openstack_storage_static, upload_to='cumulus-tests')
    custom = models.FileField(storage=openstack_storage_static, upload_to='cumulus-tests')

    def delete(self, using=None):
        """
        Delete by removing the files from its storage first,
        then proceeding with super's delete.
        """
        self.image.delete()
        self.document.delete()
        self.custom.delete()

        super(StaticThing, self).delete()
