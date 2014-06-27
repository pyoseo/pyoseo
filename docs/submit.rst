Submit operation
================

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

Upon receiving such a request, the server will store the order request in the
database with an initial status of ???. The order is then sent to a processing
queue, where it will be processed in due time. This means that Submit is an
asynchronous operation.
Depending on the request, the server can reply back in one of three ways:

* the server ankowledges the ordering request but will not try to contact the
  client to notify it of further status changes regarding the order
* the server actively notifies the client of every status change regarding the
  order. This method is not currently implemented in pyoseo.
* the server notifies the client when the order has been processed and is
  ready. This method is not currently implemented in pyoseo.

The following sequence diagram depicts an outline of pyoseo's implementation of
the Submit operation.

.. image:: images/seqdiag_submit.png

In short, when a Submit request is made:

* The web server sends the request to the 
  :func:`oseoserver.views.oseo_endpoint` django view. This view validates
  that the HTTP request is of type POST and then instantiates an
  :class:`oseoserver.server.OseoServer` instance.
* The instantiated server receives the request and authenticates the user 
  by calling its own :func:`oseoserver.server.OseoServer.authenticate_request`
  method.
* Based on the type of OSEO request received, the server creates an 
  appropriate processing class. For Submit requests, the server instantiates
  a :class:`oseoserver.operations.submit.Submit` object to do the processing.
* Processing of a Submit order breaks down to:

  * Inserting a new record for the order in the database. Order records are of
    type :class:`oseoserver.models.Order`
  * Sending the order to the celery queue, where it will be processed as one of
    the tasks defined in :mod:`oseoserver.tasks`

For more info refer to section 12 of the OSEO specification.

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

