Getstatus operation
===================

Overview
--------

The Getstatus operation is the method that the client can call in order to
retrieve the status of previously submitted orders.

GetStatus requests can be used in one of two ways:

* Order search. The client provides filtering criteria which allow querying the
  status of multiple orders

* Order retrieve. The client provides the exact order identifier for which the
  status is to be queried

The ammount of information returned depends on the presentation method selected
by the client:

* Brief. Only general order information is returned
* Full. Information related to all of the order items in the order is returned

For more info refer to section 14 of the `OSEO specification`_.

.. _OSEO specification: http://www.opengeospatial.org/standards/oseo

Implementation
--------------

Upon receiving an OSEO Getstatus request, the following workflow is set in motion:

1. The web server sends the request to the 
   :func:`~oseoserver.views.oseo_endpoint` django view. This view validates
   that the HTTP request is of type POST and then instantiates an
   :class:`~oseoserver.server.OseoServer` instance.

#. The instantiated server receives the request and authenticates the user 
   by calling the external authentication class. See :doc:`customauth` for
   more information. If authentication is successfull, the server then parses
   the request, validating that it complies with the OSEO schema

#. Based on the type of OSEO request received, the server creates an 
   appropriate processing class. For Getstatus requests, the server 
   instantiates a :class:`~oseoserver.operations.getstatus.GetStatus` object to
   process the request and handles the processing to it.

#. Processing of a GetStatus request breaks down to:

   * Searching the database for the requests order
   * For each order (and possibly each order item), retrieve its relevant
     status and other relevant details

#. After getting the information from the database, the 
   :class:`~oseoserver.operations.submit.Submit` object returns a valid OSEO 
   XML response back to the :class:`~oseoserver.server.OseoServer` instance.

#. The :class:`~oseoserver.server.OseoServer` wraps it up in a SOAP envelope
   and passes it to the :func:`~oseoserver.views.oseo_endpoint` django view.

#. The django view wraps it up with the correct HTTP headers and returns it to
   the client, as a valid OSEO SubmitResponse.

#. When the processing queue is free, it will process the order, updating its
   status in the database when appropriate.

Example
-------

An example GetStatus request could be

.. code:: xml

   <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ns="http://www.opengis.net/oseo/1.0" 
   xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd">
      <soapenv:Header>
         <!-- SOAP headers here -->
      </soapenv:Header>
      <soapenv:Body>
         <ns:GetStatus service="OS" version="1.0.0">
            <ns:orderId>1</ns:orderId>
            <ns:presentation>full</ns:presentation>
         </ns:GetStatus>
      </soapenv:Body>
   </soapenv:Envelope>

Here the client is asking the server to perform a GetStatus operation by order
retrieve and using full presentation mode.

Upon receiving such a request, pyoseo's response will be something like

.. code:: xml

   <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ows="http://www.opengis.net/ows/2.0">
      <soap:Body>
         <ns1:GetStatusResponse xmlns:ns1="http://www.opengis.net/oseo/1.0">
            <ns1:status>success</ns1:status>
            <ns1:orderMonitorSpecification>
               <ns1:orderReference>Test reference</ns1:orderReference>
               <ns1:orderRemark>A remark</ns1:orderRemark>
               <ns1:deliveryOptions>
                  <ns1:onlineDataAccess>
                     <ns1:protocol>ftp</ns1:protocol>
                  </ns1:onlineDataAccess>
               </ns1:deliveryOptions>
               <ns1:orderType>PRODUCT_ORDER</ns1:orderType>
               <ns1:orderId>1</ns1:orderId>
               <ns1:orderStatusInfo>
                  <ns1:status>Completed</ns1:status>
               </ns1:orderStatusInfo>
               <ns1:orderDateTime>2014-06-24T14:31:45.322658Z</ns1:orderDateTime>
               <ns1:orderItem>
                  <ns1:itemId>item_01</ns1:itemId>
                  <ns1:productOrderOptionsId>pyoseo options</ns1:productOrderOptionsId>
                  <ns1:productId>
                     <ns1:identifier>01729024-8dba-11e3-b102-0019995d2a58</ns1:identifier>
                  </ns1:productId>
                  <ns1:orderItemStatusInfo>
                     <ns1:status>Downloaded</ns1:status>
                  </ns1:orderItemStatusInfo>
               </ns1:orderItem>
               <ns1:orderItem>
                  <ns1:itemId>item_02</ns1:itemId>
                  <ns1:productOrderOptionsId>pyoseo options</ns1:productOrderOptionsId>
                  <ns1:productId>
                     <ns1:identifier>96aa298c-c9d7-11e3-89f2-0019995d2a58</ns1:identifier>
                  </ns1:productId>
                  <ns1:orderItemStatusInfo>
                     <ns1:status>Downloaded</ns1:status>
                  </ns1:orderItemStatusInfo>
               </ns1:orderItem>
               <ns1:orderItem>
                  <ns1:itemId>item_03</ns1:itemId>
                  <ns1:productOrderOptionsId>pyoseo options</ns1:productOrderOptionsId>
                  <ns1:productId>
                     <ns1:identifier>ca6c6afa-c9f0-11e3-89f2-0019995d2a58</ns1:identifier>
                  </ns1:productId>
                  <ns1:orderItemStatusInfo>
                     <ns1:status>Completed</ns1:status>
                  </ns1:orderItemStatusInfo>
               </ns1:orderItem>
               <ns1:orderItem>
                  <ns1:itemId>item_04</ns1:itemId>
                  <ns1:productOrderOptionsId>pyoseo options</ns1:productOrderOptionsId>
                  <ns1:productId>
                     <ns1:identifier>1f9cca80-c9f9-11e3-89f2-0019995d2a58</ns1:identifier>
                  </ns1:productId>
                  <ns1:orderItemStatusInfo>
                     <ns1:status>Completed</ns1:status>
                  </ns1:orderItemStatusInfo>
               </ns1:orderItem>
               <ns1:orderItem>
                  <ns1:itemId>item_05</ns1:itemId>
                  <ns1:productOrderOptionsId>pyoseo options</ns1:productOrderOptionsId>
                  <ns1:productId>
                     <ns1:identifier>00c808c2-ca03-11e3-89f2-0019995d2a58</ns1:identifier>
                  </ns1:productId>
                  <ns1:orderItemStatusInfo>
                     <ns1:status>Completed</ns1:status>
                  </ns1:orderItemStatusInfo>
               </ns1:orderItem>
            </ns1:orderMonitorSpecification>
         </ns1:GetStatusResponse>
      </soap:Body>
   </soap:Envelope>

The response shows information about the order, including its status. It also
includes information on all of the order items which are part of the order.
