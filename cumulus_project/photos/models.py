from django.db import models
from imagekit.models import ImageModel
from cumulus.storage import CloudFilesStorage

cfstorage = CloudFilesStorage()

class Photo(ImageModel):
    title = models.CharField(max_length=50)
    image = models.ImageField(upload_to='photos')
    ik_image = models.ImageField(storage=cfstorage, upload_to='photos')
    
    def __unicode__(self):
        return self.title
    
    class IKOptions:
        spec_module = 'photos.specs'
        cache_dir = 'photos'
        image_field = 'ik_image'
