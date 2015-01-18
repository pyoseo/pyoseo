from django.test import TestCase
from django.contrib.auth.models import User

import models


class OseoUserTestCase(TestCase):

    def setUp(self):
        User.objects.create()

#import os
#from unittest import TestCase
#
#from django.core.urlresolvers import reverse
#from django.test import TestCase as TestCaseDjango
#from django.test.client import Client
#from django.conf import settings as django_settings
#import pyxb.bundles.opengis.oseo as oseo
#
#from oseoserver import models
#from oseoserver.operations import getstatus
#
#class GetstatusOperationTestCase(TestCaseDjango):
#    """
#    This class provides tests for the GetStatus operation class.
#    """
#
#    fixtures = ['test_get_status.json']
#
#    def setUp(self):
#        root_dir = os.path.dirname(django_settings.BASE_DIR)
#        self.encoding = 'utf8'
#        self.sample_directory = os.path.join(root_dir, 'samples',
#                                             'custom_samples')
#        self.operation = getstatus.GetStatus()
#        self.user = 'oseoserver'
#
#    def test_get_status_success(self):
#        sample_file = os.path.join(self.sample_directory, 'requests',
#                                   'GetStatus.xml')
#        request = open(sample_file).read()
#        schema_instance = oseo.CreateFromDocument(request)
#        response, status_code = self.operation(schema_instance, self.user)
#        self.assertEqual(status_code, 200)
#
#    def test_get_status_brief(self):
#        sample_file = os.path.join(self.sample_directory, 'requests',
#                                   'GetStatus.xml')
#        request = open(sample_file).read()
#        schema_instance = oseo.CreateFromDocument(request)
#        response, status_code = self.operation(schema_instance, self.user)
#        self.assertIsInstance(response, oseo.GetStatusResponseType)
#
#class GetStatusServerTestCase(TestCaseDjango):
#    """
#    This class provides tests for the Getstatus operation when ran through the
#    server.
#    """
#
#    fixtures = ['test_get_status.json']
#    urls = 'oseoserver.urls'
#
#    def setUp(self):
#        root_dir = os.path.dirname(django_settings.BASE_DIR)
#        self.encoding = 'utf8'
#        self.sample_directory = os.path.join(root_dir, 'samples',
#                                             'custom_samples')
#        self.operation = getstatus.GetStatus()
#        self.user = 'oseoserver'
#
#    def test_status_brief(self):
#        sample_file = os.path.join(self.sample_directory, 'requests',
#                                   'GetStatus.xml')
#        request_data = open(sample_file).read()
#        uri = reverse('oseo_endpoint')
#        response = self.client.post(uri, data=request_data,
#                                    content_type='text/xml')
#        truth = open(os.path.join(self.sample_directory, 'responses',
#                     'GetStatusResponse.xml')).read()
#        self.assertEqual(response.content, truth)
#
