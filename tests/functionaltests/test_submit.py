import pytest
from pyxb import BIND
from pyxb.bundles.opengis import oseo_1_0 as oseo
from pyxb.bundles.wssplat import soap12
from pyxb.bundles.wssplat import wsse
import requests

pytestmark = pytest.mark.functional


class TestSubmit(object):

    # write a test product ordering disabled at the general level

    # write a test product ordering disabled at the collection level

    def test_submit_product_order_http_access(self, pyoseo_remote_server,
                                              pyoseo_server_user,
                                              pyoseo_server_password,
                                              settings):
        print("debug: {}".format(settings.DEBUG))
        col_id = settings.OSEOSERVER_COLLECTIONS[0]["collection_identifier"]
        submit = oseo.Submit(
            service="OS",
            version="1.0.0",
            orderSpecification=oseo.OrderSpecification(
                orderReference="dummy reference",
                orderRemark="dummy remark",
                deliveryOptions=oseo.deliveryOptions(
                    onlineDataAccess=BIND(
                        protocol="http"
                    )
                ),
                orderType="PRODUCT_ORDER",
                orderItem=[
                    oseo.CommonOrderItemType(
                        itemId="dummy item id1",
                        productOrderOptionsId="dummy productorderoptionsid1",
                        orderItemRemark="dumm item remark1",
                        productId=oseo.ProductIdType(
                            identifier="dummy catalog identifier1",
                            collectionId=col_id
                        )
                    ),
                ],
            ),
            statusNotification="None"
        )

        security = wsse.Security(
            wsse.UsernameToken(
                pyoseo_server_user,
                wsse.Password(pyoseo_server_password, Type="BBBB#VITO")
            ))
        soap_request_env = soap12.Envelope(
            Header=BIND(security),
            Body=BIND(submit)
        )
        request_data = soap_request_env.toxml(encoding="utf-8")
        response = requests.post(pyoseo_remote_server, data=request_data)
        response_data = response.text
        print("response_data: {}".format(response_data))
        soap_response_env = soap12.CreateFromDocument(response_data)
        submit_ack = soap_response_env.Body.wildcardElements()[0]
        print("submit_ack type: {}".format(type(submit_ack)))
        assert submit_ack._element().name().localName() == "SubmitAck"
        assert submit_ack.status == "success"
        assert (submit_ack.orderReference ==
                submit.orderSpecification.orderReference)
