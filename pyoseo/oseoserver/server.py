# Copyright 2015 Ricardo Garcia Silva
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

"""
This module defines the OseoServer class, which implements general request 
processing operations and then delegates to specialized operation classes
that preform each OSEO operation.

.. code:: python

   s = oseoserver.OseoServer()
   result, status_code, response_headers = s.process_request(request)
"""

# Creating the ParameterData element:
#
# * create an appropriate XML Schema Definition file (xsd)
# * generate pyxb bindings for the XML schema with:
#
#  pyxbgen --schema-location=pyoseo.xsd --module=pyoseo_schema
#
# * in ipython
#
#  import pyxb.binding.datatypes as xsd
#  import pyxb.bundles.opengis.oseo as oseo
#  import pyoseo_schema
#
#  pd = oseo.ParameterData()
#  pd.encoding = 'XMLEncoding'
#  pd.values = xsd.anyType()
#  pd.values.append(pyoseo_schema.fileFormat('o valor'))
#  pd.values.append(pyoseo_schema.projection('a projeccao'))
#  pd.toxml()

import logging

from django.conf import settings as django_settings
from django.core.exceptions import ObjectDoesNotExist
from lxml import etree
import pyxb.bundles.opengis.oseo_1_0 as oseo
import pyxb.bundles.opengis.ows as ows_bindings
import pyxb
from mailqueue.models import MailerMessage
from django.contrib.auth.models import User
from django.conf import settings

from oseoserver import tasks
import models
import errors
import utilities
from auth.usernametoken import UsernameTokenAuthentication

logger = logging.getLogger('.'.join(('pyoseo', __name__)))


class OseoServer(object):
    """
    Handle requests that come from Django and process them.

    This class performs some pre-processing of requests, such as schema
    validation and user authentication. It then offloads the actual processing
    of requests to specialized OSEO operation classes. After the request has
    been processed, there is also some post-processing stuff, such as wrapping
    the result with the correct SOAP headers.

    Clients of this class should use only the process_request method.
    """

    MASSIVE_ORDER_REFERENCE = 'Massive order'
    """Identifies an order as being a 'massive order'"""

    DEFAULT_USER_NAME = 'oseoserver_user'
    """Used for anonymous servers"""

    OSEO_VERSION = "1.0.0"

    MAX_ORDER_ITEMS = 200  # this could be moved to the admin
    """Maximum number of products that can be ordered at a time"""

    STATUS_NOTIFICATIONS = {
        models.Order.NONE: None,
        models.Order.FINAL: None,
        models.Order.ALL: None
    }

    ENCODING = "utf-8"
    _namespaces = {
        "soap": "http://www.w3.org/2003/05/soap-envelope",
        "soap1.1": "http://schemas.xmlsoap.org/soap/envelope/",
        "wsse": "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-"
                "wssecurity-secext-1.0.xsd",
        "ows": "http://www.opengis.net/ows/2.0",
    }
    _exception_codes = {
        "AuthorizationFailed": "client",
        "AuthenticationFailed": "client",
        "InvalidOrderIdentifier": "client",
        "NoApplicableCode": "client",
        "UnsupportedCollection": "client",
        "InvalidParameterValue": "client",
    }

    OPERATION_CLASSES = {
        "GetCapabilities": "oseoserver.operations.getcapabilities."
                           "GetCapabilities",
        "Submit": "oseoserver.operations.submit.Submit",
        "DescribeResultAccess": "oseoserver.operations.describeresultaccess."
                                "DescribeResultAccess",
        "GetOptions": "oseoserver.operations.getoptions.GetOptions",
        "GetStatus": "oseoserver.operations.getstatus.GetStatus",
    }

    def process_request(self, request_data):
        """
        Entry point for the ordering service.

        This method receives the raw request data as a string and then parses
        it into a valid pyxb OSEO object. It will then send the request to the
        appropriate operation processing class.

        :arg request_data: The raw request data
        :type request_data: str
        :return: The response XML document, as a string, the HTTP status
                 code and a dictionary with HTTP headers to be set by the 
                 wsgi server
        :rtype: tuple(str, int, dict)
        """

        element = etree.fromstring(request_data)
        response_headers = dict()
        soap_version = self._is_soap(element)
        if soap_version is not None:
            data = self._get_soap_data(element, soap_version)
            if soap_version == '1.2':
                logger.debug('SOAP 1.2 request')
                response_headers['Content-Type'] = 'application/soap+xml'
            else:
                logger.debug('SOAP 1.1 request')
                response_headers['Content-Type'] = 'text/xml'
        else:
            logger.debug('Non SOAP request')
            data = element
            response_headers['Content-Type'] = 'application/xml'
        try:
            user = self.authenticate_request(element, soap_version)
            schema_instance = self.parse_xml(data)
            operation, op_name = self._get_operation(schema_instance)
            response, status_code, info = operation(schema_instance, user)
            if op_name == "Submit":
                self.dispatch_order(info["order"])
            if soap_version is not None:
                result = self._wrap_soap(response, soap_version)
            else:
                result = response.toxml(encoding=self.ENCODING)
        except errors.OseoError as err:
            if err.code == 'AuthorizationFailed':
                status_code = 401
                # we should probably also adjust the response's headers to 
                # include a WWW-authenticate HTTP header as well
            else:
                status_code = 400
            result = self.create_exception_report(err.code, err.text,
                                                  soap_version,
                                                  locator=err.locator)
        except errors.InvalidPackagingError as e:
            status_code = 400
            result = self.create_exception_report(
                "NoApplicableCode",
                "Invalid packaging value: {}".format(e),
                soap_version)
        except (errors.InvalidOptionError,
                errors.InvalidOptionValueError,
                errors.InvalidGlobalOptionError,
                errors.InvalidGlobalOptionValueError) as e:
            status_code = 400
            result = self.create_exception_report(
                "InvalidParameterValue",
                "Invalid value for parameter",
                soap_version,
                e.option)
        except errors.NonSoapRequestError as e:
            status_code = 400
            result = e
        except errors.InvalidSettingsError as e:
            status_code = 500
            result = e
        except pyxb.UnrecognizedDOMRootNodeError as e:
            status_code = 400
            result = self.create_exception_report(
                "NoApplicableCode",
                "Unsupported operation: {}".format(e.node.tagName),
                soap_version)
        except pyxb.UnrecognizedContentError as e:
            status_code = 400
            result = self.create_exception_report(
                "NoApplicableCode",
                str(e),
                soap_version)
        except pyxb.SimpleFacetValueError as e:
            status_code = 400
            result = self.create_exception_report(
                "NoApplicableCode",
                str(e),
                soap_version)
        return result, status_code, response_headers

    def authenticate_request(self, request_element, soap_version):
        """
        Authenticate an OSEO request.

        Verify that the incoming request is made by a valid user.
        PyOSEO uses SOAP-WSS UsernameToken Profile v1.0 authentication. The
        specification is available at:

        https://www.oasis-open.org/committees/download.php/16782/wss-v1.1-spec-os-UsernameTokenProfile.pdf

        Request authentication can be customized according to the
        needs of each ordering server. This method plugs into that by
        trying to load an external authentication class.

        There are two auth scenarios:

        * A returning user
        * A new user

        The actual authentication is done by a custom class. This class
        is specified for each OseoGroup instance in its `authentication_class`
        attribute.

        The custom authentication class must provide the following API:

        .. py:function:: authenticate_request(user_name, password, **kwargs)

        .. py:function:: is_user(user_name, password, **kwargs)
        """

        auth = UsernameTokenAuthentication()
        user_name, password, extra = auth.get_details(request_element,
                                                      soap_version)
        logger.debug("user_name: {}".format(user_name))
        logger.debug("password: {}".format(password))
        logger.debug("extra: {}".format(extra))
        try:
            user = models.OseoUser.objects.get(user__username=user_name)
            auth_class = user.oseo_group.authentication_class
        except models.OseoUser.DoesNotExist:
            user = self.add_user(user_name, password, **extra)
            auth_class = user.oseo_group.authentication_class
        try:
            instance = utilities.import_class(auth_class)
            authenticated = instance.authenticate_request(user_name, password,
                                                          **extra)
            if not authenticated:
                text = "Invalid or missing identity information"
                raise errors.OseoError("AuthenticationFailed", text,
                                       locator="identity_token")
        except errors.OseoError:
            raise  # this error is handled by the calling method
        except Exception as e:
            # other errors are re-raised as InvalidSettings
            logger.error('exception class: {}'.format(
                         e.__class__.__name__))
            logger.error('exception args: {}'.format(e.args))
            raise errors.InvalidSettingsError('Invalid authentication '
                                              'class')
        logger.info('User {} authenticated successfully'.format(user_name))
        return user

    def add_user(self, user_name, password, **kwargs):
        oseo_user = None
        groups = models.OseoGroup.objects.all()
        found_group = False
        current = 0
        while not found_group and current < len(groups):
            current_group = groups[current]
            custom_auth = utilities.import_class(
                current_group.authentication_class)
            if custom_auth.is_user(user_name, password, **kwargs):
                found_group = True
                user = models.User.objects.create_user(user_name,
                                                       password=None)
                oseo_user = models.OseoUser.objects.get(user=user)
                oseo_user.oseo_group = current_group
                oseo_user.save()
            current += 1
        return oseo_user

    def create_exception_report(self, code, text, soap_version, locator=None):
        """
        :arg code: OSEO exception code. Can be any of the defined
                   exceptionCode values in the OSEO and OWS Common 
                   specifications.
        :type code: str
        :arg text: Text to display in the exception report
        :type text: str
        :arg soap_version: Version of the SOAP protocol to use, if any
        :type soap_version: str or None
        :arg locator: value to display in the 'locator' field
        :type locator: str
        :return: A string with the XML exception report
        """

        exception = ows_bindings.Exception(exceptionCode=code)
        if locator is not None:
            exception.locator = locator
        exception.append(text)
        exception_report = ows_bindings.ExceptionReport(
            version=self.OSEO_VERSION)
        exception_report.append(exception)
        if soap_version is not None:
            soap_code = self._exception_codes[code]
            result = self._wrap_soap_fault(exception_report, soap_code,
                                           soap_version)
        else:
            result = exception_report.toxml(encoding=self.ENCODING)
        return result

    def _is_soap(self, request_element):
        """
        Look for SOAP requests.

        Although the OSEO spec states that SOAP v1.2 is to be used, pyoseo
        accepts both SOAP v1.1 and SOAP v1.2

        :arg request_element: the raw input request
        :type request_element: lxml.etree.Element instance
        """

        ns, tag = request_element.tag.split('}')
        ns = ns[1:]
        result = None
        if tag == 'Envelope':
            if ns == self._namespaces['soap']:
                result = '1.2'
            elif ns == self._namespaces['soap1.1']:
                result = '1.1'
        return result

    def parse_xml(self, xml):
        """
        Parse the input XML request and return a valid PyXB object

        :arg xml: the XML element with the request
        :xml type: lxml.etree.Element
        :return: The instance generated by pyxb
        """

        document = etree.tostring(xml, encoding=self.ENCODING,
                                  pretty_print=True)
        oseo_request = oseo.CreateFromDocument(document)
        return oseo_request

    def _get_operation(self, pyxb_request):
        oseo_op = pyxb_request.toDOM().firstChild.tagName.partition(":")[-1]
        op = self.OPERATION_CLASSES[oseo_op]
        return utilities.import_class(op), oseo_op

    def _get_soap_data(self, element, soap_version):
        """
        :arg element: The full request object
        :type element: lxml.etree.Element
        :arg soap_version: The SOAP version in use
        :type soap_version: str
        :return: The contents of the soap:Body element.
        :rtype: lxml.etree.Element
        """

        if soap_version == '1.2':
            path = '/soap:Envelope/soap:Body/*[1]'
        else:
            path = '/soap1.1:Envelope/soap1.1:Body/*[1]'
        xml_element = element.xpath(path, namespaces=self._namespaces)
        return xml_element[0]

    def _wrap_soap(self, response, soap_version):
        """
        :arg response: the pyxb instance with the previously generated response
        :type response: pyxb.bundles.opengis.oseo
        :arg soap_version: The SOAP version in use
        :type soap_version: str
        :return: A string with the XML response
        """

        soap_env_ns = {
            'ows': self._namespaces['ows'],
        }
        if soap_version == '1.2':
            soap_env_ns['soap'] = self._namespaces['soap']
        else:
            soap_env_ns['soap'] = self._namespaces['soap1.1']
        soap_env = etree.Element('{%s}Envelope' % soap_env_ns['soap'],
                                 nsmap=soap_env_ns)
        soap_body = etree.SubElement(soap_env, '{%s}Body' %
                                     soap_env_ns['soap'])

        response_string = response.toxml(encoding=self.ENCODING)
        response_string = response_string.encode(self.ENCODING)
        response_element = etree.fromstring(response_string)
        soap_body.append(response_element)
        return etree.tostring(soap_env, encoding=self.ENCODING,
                              pretty_print=True)

    def _wrap_soap_fault(self, exception_report, soap_code, soap_version):
        """
        :arg exception_report: The pyxb instance with the previously generated
                               exception report
        :type exception_report: pyxb.bundles.opengis.ows.ExceptionReport
        :arg soap_code: Can be either 'server' or 'client'
        :type soap_code: str
        :arg soap_version: The SOAP version in use
        :type soap_version: str
        """

        code_msg = 'soap:{}'.format(soap_code.capitalize())
        reason_msg = '{} exception was encountered'.format(
            soap_code.capitalize())
        exception_string = exception_report.toxml(encoding=self.ENCODING)
        exception_string = exception_string.encode(self.ENCODING)
        exception_element = etree.fromstring(exception_string)
        soap_env_ns = {
            'ows': self._namespaces['ows'],
        }
        if soap_version == '1.2':
            soap_env_ns['soap'] = self._namespaces['soap']
        else:
            soap_env_ns['soap'] = self._namespaces['soap1.1']
        soap_env = etree.Element('{{{}}}Envelope'.format(soap_env_ns['soap']),
                                 nsmap=soap_env_ns)
        soap_body = etree.SubElement(soap_env, '{{{}}}Body'.format(
                                     soap_env_ns['soap']))
        soap_fault = etree.SubElement(soap_body, '{{{}}}Fault'.format(
                                      soap_env_ns['soap']))
        if soap_version == '1.2':
            fault_code = etree.SubElement(soap_fault, '{{{}}}Code'.format(
                                          soap_env_ns['soap']))
            code_value = etree.SubElement(fault_code, '{{{}}}Value'.format(
                                          soap_env_ns['soap']))
            code_value.text = code_msg
            fault_reason = etree.SubElement(soap_fault, '{{{}}}Reason'.format(
                                            soap_env_ns['soap']))
            reason_text = etree.SubElement(fault_reason, '{{{}}}Text'.format(
                                           soap_env_ns['soap']))
            reason_text.text = reason_msg
            fault_detail = etree.SubElement(soap_fault, '{{{}}}Detail'.format(
                                            soap_env_ns['soap']))
            fault_detail.append(exception_element)
        else:
            fault_code = etree.SubElement(soap_fault, 'faultcode')
            fault_code.text = code_msg
            fault_string = etree.SubElement(soap_fault, 'faultstring')
            fault_string.text = reason_msg
            fault_actor = etree.SubElement(soap_fault, 'faultactor')
            fault_actor.text = ''
            detail = etree.SubElement(soap_fault, 'detail')
            detail.append(exception_element)
        return etree.tostring(soap_env, encoding=self.ENCODING,
                              pretty_print=True)

    def dispatch_order(self, order, force=False, **kwargs):
        """Dispatch an order for processing in the async queue."""

        if force:
            order.status = models.CustomizableItem.ACCEPTED
        if order.status == models.CustomizableItem.SUBMITTED:
            utilities.send_moderation_email(order)
        elif order.status == models.CustomizableItem.ACCEPTED:
            logger.debug("sending order {} to processing queue...".format(
                order.id))
            if order.order_type.name == models.Order.PRODUCT_ORDER:
                tasks.process_product_order.apply_async((order.id,))
            elif order.order_type.name == models.Order.SUBSCRIPTION_ORDER:
                tasks.process_subscription_order.apply_async((order.id, kwargs))

    def process_subscriptions(self, current_timeslot):
        for s in models.SubscriptionOrder.objects.filter(active=True):
            self.dispatch_order(s, current_timeslot=current_timeslot)

    def process_product_orders(self):
        for order in models.ProductOrder.objects.filter(
                status=models.CustomizableItem.ACCEPTED):
            self.dispatch_order(order)

    def reprocess_order(self, order_id):
        order = models.Order.objects.get(id=order_id)
        self.dispatch_order(order, force=True)

    def moderate_order(self, order, approved, rejection_details=""):
        """
        Decide on approval of an order.

        The OSEO standard does not really define any moderation workflow
        for orders. As such, none of the defined statuses fits exactly with
        this process. We are abusing the CANCELLED status for this.

        :param order:
        :param approved:
        :param rejection_details:
        :return:
        """
        if approved:
            order.status = models.CustomizableItem.ACCEPTED
            order.additional_status_info = ("Order has been approved and is "
                                            "waiting in the processing queue")
        else:
            order.status = models.CustomizableItem.CANCELLED
            if rejection_details != "":
                order.additional_status_info = rejection_details
            else:
                order.additional_status_info = ("Order request has been "
                                                "rejected by the "
                                                "administrators.")
        order.save()
        self.dispatch_order(order)
