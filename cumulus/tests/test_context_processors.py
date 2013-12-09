import mock

from django.conf import settings
from django.test import TestCase

from cumulus.context_processors import cdn_url, static_cdn_url


class ContextProcessorTests(TestCase):

    def setUp(self):
        patched = mock.patch('cumulus.context_processors.SwiftclientStorage')
        patched_static = mock.patch('cumulus.context_processors.SwiftclientStaticStorage')

        self.uri = 'http://test.uri'
        self.ssl_uri = 'https://test.uri'

        self.addCleanup(patched.stop)
        self.addCleanup(patched_static.stop)

        self.mocked = patched.start()
        self.mocked_static = patched_static.start()

        instance = self.mocked.return_value
        instance.container.cdn_uri = self.uri
        instance.container.cdn_ssl_uri = self.ssl_uri

        instance_static = self.mocked_static.return_value
        instance_static.container.cdn_uri = self.uri
        instance_static.container.cdn_ssl_uri = self.ssl_uri

    def test_cdn_url(self):
        expected = {
            "CDN_URL": self.uri + settings.STATIC_URL,
            "CDN_SSL_URL": self.ssl_uri + settings.STATIC_URL,
        }
        self.assertEqual(cdn_url(None), expected)

    def test_static_cdn_url(self):
        expected = {
            "STATIC_URL": self.uri + settings.STATIC_URL,
            "STATIC_SSL_URL": self.ssl_uri + settings.STATIC_URL,
            "LOCAL_STATIC_URL": settings.STATIC_URL,
        }
        self.assertEqual(static_cdn_url(None), expected)
