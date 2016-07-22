"""Functional tests for the Getstatus operation"""

import pytest
from pyxb import BIND
from pyxb.bundles.opengis import oseo_1_0 as oseo
from pyxb.bundles.wssplat import soap12
from pyxb.bundles.wssplat import wsse
import requests

pytestmark = pytest.mark.functional


class TestGetStatus(object):

    def test_get_status(self, pyoseo_remote_server, pyoseo_server_user,
                        pyoseo_server_password, settings):
        pass
