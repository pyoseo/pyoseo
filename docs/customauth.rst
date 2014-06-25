Hooking up your authentication framework
========================================

Each organization has their preferred authentication and authorization
solution. Instead of trying to support them all, pyoseo requires you to 
implement the one you want to use by providing a hook for a custom 
authentication class in its settings and then calling it whenever it needs to
authenticate a user.

.. note::
   If you do not implement your own custom authentication class, pyoseo will
   simply process every request using a default user. Its fine to use this in a
   testing environment, but we recommend against it in production.

Authentication classes
----------------------

In order to let some user perform orders with pyoseo, you must create an
authentication class and specify it in the
:attr:`~pyoseo.settings.OSEOSERVER_AUTHENTICATION_CLASS` setting.

  .. code:: python

     # pyoseo settings
     OSEOSERVER_AUTHENTICATION_CLASS = 'mymodule.MyAuthenticationClass'

The authentication class must include an `authenticate_request` method. This 
method will be called by pyoseo whenever it needs to authenticate a user.
It must have the following signature:

.. py:class:: MyAuthentication

   .. py:method:: authenticate_request(request_element, soap_version)

      :arg request_element: The full request object
      :type request_element: lxml.etree.Element
      :arg soap_version: The SOAP version in use. The OSEO specification
                         text states that SOAP 1.2 should be used. However,
                         the WSDL distributed with the specification uses
                         SOAP 1.1. This method supports both versions.
      :type soap_version: str
      :return: The user_name and password of the successfully authenticated
               user
      :rtype: (str, str)

The rest of the authentication class can include whatever you want.

Example
-------

The following example shows how a custom authentication class can be used to
check for the presence of a user and password in the SOAP headers of a request

.. code:: python

   import oseoserver.errors as errors

   class ExampleAuth(object):

       def authenticate_request(request_element, soap_version):
            if soap_version is None:
                raise errors.NonSoapRequestError('%s requires requests to use '
                                                 'the SOAP protocol' %
                                                 self.__class__.__name__)
            soap_ns_map = {
                '1.1': 'soap1.1',
                '1.2': 'soap',
            }
            soap_ns_key = soap_ns_map[soap_version]
            try:
                user, vito_token, vito_pass = self.get_identity_token(
                    request_element,
                    soap_ns_key
                )
                valid_request = self.validate_vito_identity(vito_token, vito_pass)
                if valid_request:
                    user_name, password = self.get_user_data(user)
                else:
                    raise Exception('Could not validate VITO identity')
            except Exception as err:
                logger.error(err)
                raise oseoserver.errors.OseoError(
                    'AuthenticationFailed',
                    'Invalid or missing identity information',
                    locator='identity_token'
                )
            return user_name, password

