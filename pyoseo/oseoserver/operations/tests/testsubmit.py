from django.test import TestCase

from oseoserver.operations.submit import Submit

class SubmitTestCase(TestCase):

    def test_create_submit(self):
        s = Submit()