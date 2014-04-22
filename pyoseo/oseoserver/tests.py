import os
from unittest import TestCase

from django.test import TestCase as TestCaseDjango
from django.conf import settings as django_settings
import pyxb.bundles.opengis.oseo as oseo

from oseoserver import models
from oseoserver import server
from oseoserver.oseooperations import getstatus

class GetStatusTestCase(TestCase):

    def setUp(self):
        server = server.OseoServer()
        self.operation = getstatus.GetStatus(server)
        self.user = 'oseoserver'
        root_dir = os.path.dirname(django_settings.BASE_DIR)
        self.sample_directory = os.path.join(root_dir, 'samples')
        creation_date = dt.datetime.utcnow()
        order = models.Order(
            created_on=creation_date,
            status_changed_on=creation_date,
            remark='testing remark',
            reference='testing reference',
        )

    def test_get_status_simple(self):
        sample = 'custom_samples/GetStatus.xml'
        request = open(os.path.join(self.sample_directory, sample)).read()
        schema_instance = oseo.CreateFromDocument(request)
        response, status_code = self.operation(schema_instance, self.user)
        self.assertEqual(status_code, 200)
