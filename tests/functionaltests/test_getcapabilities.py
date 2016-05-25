import pytest
from pyxb import BIND
from pyxb.bundles.opengis import oseo_1_0 as oseo
from pyxb.bundles.wssplat import soap12
from pyxb.bundles.wssplat import wsse
import requests

@pytest.mark.functional
class TestGetCapabilities(object):

    @pytest.mark.skip()
    def test_get_capabilities_no_auth_no_soap(self):
        # will fail because presently our auth scheme requires SOAP
        pass

    def test_default_get_capabilities(self, pyoseo_server_url,
                                      pyoseo_server_user,
                                      pyoseo_server_password):
        get_caps = oseo.GetCapabilities(service="OS")
        security = wsse.Security(
            wsse.UsernameToken(
                pyoseo_server_user,
                wsse.Password(pyoseo_server_password, Type="BBBB#VITO")
            ))
        soap_request_env = soap12.Envelope(
            Header=BIND(security),
            Body=BIND(get_caps)
        )
        request_data = soap_request_env.toxml(encoding="utf-8")
        url = "{}/oseo/".format(pyoseo_server_url)
        response = requests.post(url, data=request_data)
        response_data = response.text
        print("response_data: {}".format(response_data))
        soap_response_env = soap12.CreateFromDocument(response_data)
        caps = soap_response_env.Body.wildcardElements()[0]
        print("caps type: {}".format(type(caps)))

    @pytest.mark.skip()
    def test_get_capabilities_no_auth_soap11(self):
        pass

    @pytest.mark.skip()
    def test_get_capabilities_bad_auth_soap12(self):
        pass

    @pytest.mark.skip()
    def test_get_capabilities_good_auth_soap12(self):
        pass
