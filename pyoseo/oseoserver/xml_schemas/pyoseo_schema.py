# ./pyoseo_schema.py
# -*- coding: utf-8 -*-
# PyXB bindings for NM:1bf401cec9a1734de8e2d6a73ea1a055dfb66f01
# Generated 2014-02-25 20:07:11.520997 by PyXB version 1.2.3
# Namespace ipma.pt.pyoseo

import pyxb
import pyxb.binding
import pyxb.binding.saxer
import io
import pyxb.utils.utility
import pyxb.utils.domutils
import sys

# Unique identifier for bindings created at the same time
_GenerationUID = pyxb.utils.utility.UniqueIdentifier('urn:uuid:69780b46-9e58-11e3-92bb-001cbfb1f175')

# Version of PyXB used to generate the bindings
_PyXBVersion = '1.2.3'
# Generated bindings are not compatible across PyXB versions
if pyxb.__version__ != _PyXBVersion:
    raise pyxb.PyXBVersionError(_PyXBVersion)

# Import bindings for namespaces imported into schema
import pyxb.binding.datatypes

# NOTE: All namespace declarations are reserved within the binding
Namespace = pyxb.namespace.NamespaceForURI(u'ipma.pt.pyoseo', create_if_missing=True)
Namespace.configureCategories(['typeBinding', 'elementBinding'])

def CreateFromDocument (xml_text, default_namespace=None, location_base=None):
    """Parse the given XML and use the document element to create a
    Python instance.

    @param xml_text An XML document.  This should be data (Python 2
    str or Python 3 bytes), or a text (Python 2 unicode or Python 3
    str) in the L{pyxb._InputEncoding} encoding.

    @keyword default_namespace The L{pyxb.Namespace} instance to use as the
    default namespace where there is no default namespace in scope.
    If unspecified or C{None}, the namespace of the module containing
    this function will be used.

    @keyword location_base: An object to be recorded as the base of all
    L{pyxb.utils.utility.Location} instances associated with events and
    objects handled by the parser.  You might pass the URI from which
    the document was obtained.
    """

    if pyxb.XMLStyle_saxer != pyxb._XMLStyle:
        dom = pyxb.utils.domutils.StringToDOM(xml_text)
        return CreateFromDOM(dom.documentElement)
    if default_namespace is None:
        default_namespace = Namespace.fallbackNamespace()
    saxer = pyxb.binding.saxer.make_parser(fallback_namespace=default_namespace, location_base=location_base)
    handler = saxer.getContentHandler()
    xmld = xml_text
    if isinstance(xmld, unicode):
        xmld = xmld.encode(pyxb._InputEncoding)
    saxer.parse(io.BytesIO(xmld))
    instance = handler.rootObject()
    return instance

def CreateFromDOM (node, default_namespace=None):
    """Create a Python instance from the given DOM node.
    The node tag must correspond to an element declaration in this module.

    @deprecated: Forcing use of DOM interface is unnecessary; use L{CreateFromDocument}."""
    if default_namespace is None:
        default_namespace = Namespace.fallbackNamespace()
    return pyxb.binding.basis.element.AnyCreateFromDOM(node, default_namespace)


# Atomic simple type: {ipma.pt.pyoseo}FileFormatType
class FileFormatType (pyxb.binding.datatypes.string):

    """An atomic simple type."""

    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, u'FileFormatType')
    _XSDLocation = pyxb.utils.utility.Location('/home/ricardo/dev/pyoseo/pyoseo/xml/pyoseo.xsd', 9, 4)
    _Documentation = None
FileFormatType._InitializeFacetMap()
Namespace.addCategoryObject('typeBinding', u'FileFormatType', FileFormatType)

# Atomic simple type: {ipma.pt.pyoseo}RescaleValuesType
class RescaleValuesType (pyxb.binding.datatypes.boolean):

    """An atomic simple type."""

    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, u'RescaleValuesType')
    _XSDLocation = pyxb.utils.utility.Location('/home/ricardo/dev/pyoseo/pyoseo/xml/pyoseo.xsd', 14, 4)
    _Documentation = None
RescaleValuesType._InitializeFacetMap()
Namespace.addCategoryObject('typeBinding', u'RescaleValuesType', RescaleValuesType)

# Atomic simple type: {ipma.pt.pyoseo}ProjectionType
class ProjectionType (pyxb.binding.datatypes.string):

    """An atomic simple type."""

    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, u'ProjectionType')
    _XSDLocation = pyxb.utils.utility.Location('/home/ricardo/dev/pyoseo/pyoseo/xml/pyoseo.xsd', 19, 4)
    _Documentation = None
ProjectionType._InitializeFacetMap()
Namespace.addCategoryObject('typeBinding', u'ProjectionType', ProjectionType)

# Atomic simple type: {ipma.pt.pyoseo}DatasetType
class DatasetType (pyxb.binding.datatypes.string):

    """An atomic simple type."""

    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, u'DatasetType')
    _XSDLocation = pyxb.utils.utility.Location('/home/ricardo/dev/pyoseo/pyoseo/xml/pyoseo.xsd', 24, 4)
    _Documentation = None
DatasetType._InitializeFacetMap()
Namespace.addCategoryObject('typeBinding', u'DatasetType', DatasetType)

fileFormat = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, u'fileFormat'), FileFormatType, location=pyxb.utils.utility.Location('/home/ricardo/dev/pyoseo/pyoseo/xml/pyoseo.xsd', 8, 4))
Namespace.addCategoryObject('elementBinding', fileFormat.name().localName(), fileFormat)

rescaleValues = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, u'rescaleValues'), RescaleValuesType, location=pyxb.utils.utility.Location('/home/ricardo/dev/pyoseo/pyoseo/xml/pyoseo.xsd', 13, 4))
Namespace.addCategoryObject('elementBinding', rescaleValues.name().localName(), rescaleValues)

projection = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, u'projection'), ProjectionType, location=pyxb.utils.utility.Location('/home/ricardo/dev/pyoseo/pyoseo/xml/pyoseo.xsd', 18, 4))
Namespace.addCategoryObject('elementBinding', projection.name().localName(), projection)

dataset = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, u'dataset'), DatasetType, location=pyxb.utils.utility.Location('/home/ricardo/dev/pyoseo/pyoseo/xml/pyoseo.xsd', 23, 4))
Namespace.addCategoryObject('elementBinding', dataset.name().localName(), dataset)
