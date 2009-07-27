from django.db import models
from django.core.urlresolvers import reverse

class Account(models.Model):
    """
    Represents Rackspace Cloud account information.
    """
    username = models.CharField(max_length=255)
    api_key = models.CharField(max_length=32)
    
    def __unicode__(self):
        return self.username
    
    class Meta:
        ordering = ('username',)
    
    def manage_cloudfiles(self):
        return '<a href="%s">Cloud Files</a>' % reverse('admin:cumulus-edit-cloudfiles', args=(self.id,))
    manage_cloudfiles.allow_tags = True
