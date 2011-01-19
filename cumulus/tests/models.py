from django.db import models

from cumulus.storage import CloudFilesStorage

cloudfiles_storage = CloudFilesStorage()

class Thing(models.Model):
    "A dummy model to use for tests."
    image = models.ImageField(storage=cloudfiles_storage, upload_to='cumulus-tests')
    document = models.FileField(storage=cloudfiles_storage, upload_to='cumulus-tests')
    custom = models.FileField(storage=cloudfiles_storage, upload_to='cumulus-tests')


