from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from cumulus.storage import CloudFilesStorage
from cumulus.tests.models import Thing


cloudfiles_storage = CloudFilesStorage()

class CumulusTests(TestCase):
    def setUp(self):
        "Set up tiny files to test with."
        self.image = SimpleUploadedFile('1x1.jpg', '\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xfe\x00>CREATOR: gd-jpeg v1.0 (using IJG JPEG v62), default quality\n\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xdb\x00C\x01\t\t\t\x0c\x0b\x0c\x18\r\r\x182!\x1c!22222222222222222222222222222222222222222222222222\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x03\x01"\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05\x05\x04\x04\x00\x00\x01}\x01\x02\x03\x00\x04\x11\x05\x12!1A\x06\x13Qa\x07"q\x142\x81\x91\xa1\x08#B\xb1\xc1\x15R\xd1\xf0$3br\x82\t\n\x16\x17\x18\x19\x1a%&\'()*456789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xc4\x00\x1f\x01\x00\x03\x01\x01\x01\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x11\x00\x02\x01\x02\x04\x04\x03\x04\x07\x05\x04\x04\x00\x01\x02w\x00\x01\x02\x03\x11\x04\x05!1\x06\x12AQ\x07aq\x13"2\x81\x08\x14B\x91\xa1\xb1\xc1\t#3R\xf0\x15br\xd1\n\x16$4\xe1%\xf1\x17\x18\x19\x1a&\'()*56789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz\x82\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00?\x00\xf9\xfe\x8a(\xa0\x0f\xff\xd9', content_type='image/jpeg')
        self.document = SimpleUploadedFile('test.txt', "test content")
        self.custom = SimpleUploadedFile('custom.txt', "custom type", content_type="custom/type")
        self.thing = Thing.objects.create(image=self.image, document=self.document, custom=self.custom)

    def test_file_api(self):
        "Make sure we can access file attributes using the Django File API."
        self.assertEqual(self.thing.image.width, 1)
        self.assertEqual(self.thing.image.height, 1)
        self.assertEqual(self.thing.image.size, 695)
        self.assertTrue("rackcdn.com" in self.thing.image.url,
                     "URL is not a valid Cloud Files CDN URL.")

        self.assertEqual(self.thing.document.size, 12)
        self.assertTrue("rackcdn.com" in self.thing.document.url,
                     "URL is not a valid Cloud Files CDN URL.")
        delattr(self.thing.document.storage, '_container_public_uri')
        self.thing.document.storage.use_ssl = True
        self.assertTrue(self.thing.document.url.startswith("https"))

    def test_image_content_type(self):
        "Ensure content type is set properly for the uploaded image."
        cloud_image = cloudfiles_storage.container.get_object(self.thing.image.name)
        self.assertEqual(cloud_image.content_type, "image/jpeg")

    def test_text_content_type(self):
        "Ensure content type is set properly for the uploaded text."
        cloud_doc = cloudfiles_storage.container.get_object(self.thing.document.name)
        self.assertEqual(cloud_doc.content_type, "text/plain")

    def test_custom_content_type(self):
        "Ensure content type is set properly when custom content type is supplied."
        cloud_custom = cloudfiles_storage.container.get_object(self.thing.custom.name)
        self.assertEqual(cloud_custom.content_type, "custom/type")

    def tearDown(self):
        self.thing.delete()
