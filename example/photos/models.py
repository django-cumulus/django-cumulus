from django.db import models


class Photo(models.Model):
    title = models.CharField(max_length=50)
    image = models.ImageField(upload_to='photos')

    def __unicode__(self):
        return self.title
