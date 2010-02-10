import os
from django.test import TestCase
from django.db import models
from django.core.files import File
from django.core.files.images import ImageFile

from cumulus.storage import CloudFilesStorage
cloudfiles_storage = CloudFilesStorage()

class Thing(models.Model):
    "A dummy model to use for tests."
    image = models.ImageField(storage=cloudfiles_storage, upload_to='cumulus-tests')
    document = models.FileField(storage=cloudfiles_storage, upload_to='cumulus-tests')


class CumulusTests(TestCase):
    def setUp(self):
        "Set up tiny files to test with."
        image_path = os.path.join(os.path.dirname(__file__), 'image_300x200.gif')
        document_path = os.path.join(os.path.dirname(__file__), 'text_file.txt')
        self.image = ImageFile(open(image_path, 'rb'))
        self.document = File(open(document_path, 'r'))
    
    def test_file_api(self):
        """
        Make sure we can perform the following using the Django File API:
        - Upload the test files
        - Access common file attributes
        - Delete the test files
        """
        self.thing = Thing.objects.create(image=self.image, document=self.document)
        
        self.assertEqual(self.thing.image.width, 300)
        self.assertEqual(self.thing.image.height, 200)
        self.assertEqual(self.thing.image.size, 976)
        self.assert_("cdn.cloudfiles.rackspacecloud.com" in self.thing.image.url,
                     "URL is not a valid Cloud Files CDN URL.")
        
        self.assertEqual(self.thing.document.size, 31)
        self.assert_("cdn.cloudfiles.rackspacecloud.com" in self.thing.document.url,
                     "URL is not a valid Cloud Files CDN URL.")
        
        self.thing.delete()
    
    def tearDown(self):
        self.document.close()
        self.image.close()
