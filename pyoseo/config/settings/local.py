from __future__ import absolute_import

from .base import *

DEBUG = True
SENDFILE_BACKEND = "sendfile.backends.development"

LOGGING["loggers"]["giosystemordering"] = {
    "handlers": ["console"],
    "level": "DEBUG",
}

OSEOSERVER_PRODUCT_ORDER = {
    "enabled": True,
    "automatic_approval": True,
    "notify_creation": True,
    "item_processor": "giosystemordering.orderprocessor.OrderProcessor",
    "item_availability_days": 10,
}

OSEOSERVER_PROCESSING_OPTIONS = [
    {
        "name": "MapProjection",
        "description": "Change the coordinate system of the order item",
        "multiple_entries": False,
        "choices": ["first", "second"],
    },
    {
        "name": "Format",
        "description": "Change the file format of the order item",
        "multiple_entries": False,
        "choices": ["first", "second"],
    },
    {
        "name": "RegionOfInterest",
        "description": "Specify a region of interest for cropping the order item",
        "multiple_entries": False,
        "choices": ["first", "second"],
    },
    {
        "name": "Bands",
        "description": "Subset the order item with only the chosen bands",
        "multiple_entries": True,
        "choices": ["first", "second"],
    },
]

OSEOSERVER_ONLINE_DATA_ACCESS_OPTIONS = [
    {
        "protocol":"http",
        "fee": 0,
    },
    {
        "protocol":"ftp",
        "fee": 0,
    }
]

OSEOSERVER_COLLECTIONS = [
    {
        "name": "dummy_collection",
        "catalogue_endpoint": "http://localhost",
        "collection_identifier": "dummy_collection_id",
        "product_price": 0,
        "generation_frequency": "Once per hour",
        "product_order": {
            "enabled": True,
            "order_processing_fee": 0,
            "options": ["dummy option",],
            "online_data_access_options": ["http",],
            "online_data_delivery_options": [],
            "media_delivery_options": [],
            "payment_options": [],
            "scene_selection_options": [],
        },
    },
    {
        "name": "lst",
        "catalogue_endpoint": "http://geoland2.meteo.pt/csw",
        "collection_identifier": "urn:cgls:global:lst_v1_0.045degree",
        "product_price": 0,
        "generation_frequency": "Once per hour",
        "product_order": {
            "enabled": True,
            "order_processing_fee": 0,
            "options": ["Bands", "RegionOfInterest",],
            "online_data_access_options": ["http", "ftp"],
            "online_data_delivery_options": [],
            "media_delivery_options": [],
            "payment_options": [],
            "scene_selection_options": [],
        },
    },
]
