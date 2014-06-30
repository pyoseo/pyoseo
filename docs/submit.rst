Submit operation
================

Overview
--------

The Submit operation is the method that the client can call in order to place
an order on the server.

Submit requests can produce one of:

* normal order
* massive order (Not implemented yet)
* subscription order (Not implemented yet)
* tasking request order (Not implemented yet)

Submit requests can take the form of:

* normal order specification
* order via quotation identifier (Not implemented yet)

Depending on the requested notification type, the server can reply back in 
one of three ways:

* the server ankowledges the ordering request but will not try to contact the
  client to notify it of further status changes regarding the order
* the server actively notifies the client of every status change regarding the
  order. This method is not currently implemented in pyoseo.
* the server notifies the client when the order has been processed and is
  ready. This method is not currently implemented in pyoseo.

For more info refer to section 12 of the `OSEO specification`_.

.. _OSEO specification: http://www.opengeospatial.org/standards/oseo

Implementation
--------------

Upon receiving an OSEO Submit request, the following workflow is set in motion:

1. The web server sends the request to the 
   :func:`~oseoserver.views.oseo_endpoint` django view. This view validates
   that the HTTP request is of type POST and then instantiates an
   :class:`~oseoserver.server.OseoServer` instance.

#. The instantiated server receives the request and authenticates the user 
   by calling the external authentication class. See :doc:`customauth` for
   more information. If authentication is successfull, the server then parses
   the request, validating that it complies with the OSEO schema

#. Based on the type of OSEO request received, the server creates an 
   appropriate processing class. For Submit requests, the server instantiates
   a :class:`~oseoserver.operations.submit.Submit` object to process the
   request and handles the processing to it.

#. Processing of a Submit request breaks down to:

   * Inserting a new record for the order in the database
   * Determining the order's initial state. Normal orders are
     :attr:`~oseoserver.models.CustomizableItem.ACCEPTED` by default. Other
     types of order may require a process of approval by the server's admin team
     (although currently this behaviour is not implemented)
   * Sending the accepted order to the celery queue, where it will be processed
     as one of the tasks defined in :mod:`~oseoserver.tasks`

#. After updating the database and (potentially) sending the order to the 
   processing queue, the :class:`~oseoserver.operations.submit.Submit` object 
   returns a valid OSEO XML response back to the 
   :class:`~oseoserver.server.OseoServer` instance.

#. The :class:`~oseoserver.server.OseoServer` wraps it up in a SOAP envelope
   and passes it to the :func:`~oseoserver.views.oseo_endpoint` django view.

#. The django view wraps it up with the correct HTTP headers and returns it to
   the client, as a valid OSEO SubmitResponse.

#. When the processing queue is free, it will process the order, updating its
   status in the database when appropriate.

Example
-------

An example Submit request could be

.. code:: xml

   <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:add="http://www.w3.org/2005/08/addressing" xmlns:ns="http://www.opengis.net/oseo/1.0"
   xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd">
      <soapenv:Header>
          <!-- SOAP headers here -->
      </soapenv:Header>
      <soapenv:Body>
         <ns:Submit service="OS" version="1.0.0">
            <ns:orderSpecification>
               <ns:orderReference>Test reference</ns:orderReference>
               <ns:orderRemark>A remark</ns:orderRemark>
               <ns:deliveryOptions>
                  <ns:onlineDataAccess>
                     <ns:protocol>ftp</ns:protocol>
                  </ns:onlineDataAccess>
               </ns:deliveryOptions>
               <ns:orderType>PRODUCT_ORDER</ns:orderType>
               <ns:orderItem>
                  <ns:itemId>item_01</ns:itemId>
                  <ns:productId>
                     <ns:identifier>01729024-8dba-11e3-b102-0019995d2a58</ns:identifier>
                  </ns:productId>
               </ns:orderItem>
               <ns:orderItem>
                  <ns:itemId>item_02</ns:itemId>
                  <ns:productId>
                     <ns:identifier>96aa298c-c9d7-11e3-89f2-0019995d2a58</ns:identifier>
                  </ns:productId>
               </ns:orderItem>
            </ns:orderSpecification>
            <ns:statusNotification>None</ns:statusNotification>
         </ns:Submit>
      </soapenv:Body>
   </soapenv:Envelope>

Here the client is asking the server to perform a Submit operation, creating
a normal product order that has two order items. Each item is identified by its
corresponding id in the OGC CSW catalogue server where the data records are
stored. PyOSEO can track down order items according to their id from wherever
it is told to. See the section on processing orders for more information on
this topic.

Upon receiving such a request, pyoseo's response will be something like

.. code:: xml

   <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ows="http://www.opengis.net/ows/2.0">
      <soap:Body>
         <ns1:SubmitAck xmlns:ns1="http://www.opengis.net/oseo/1.0">
            <ns1:status>success</ns1:status>
            <ns1:orderId>211</ns1:orderId>
         </ns1:SubmitAck>
      </soap:Body>
   </soap:Envelope>

This response means that pyoseo has aknowledged the order. The order has been
assigned an id, it has been stored in the order database and has been sent to
the order processing daemon, which queues the order for processing as soon as
there are available processing resources.


