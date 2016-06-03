from __future__ import absolute_import

from .base import *

DEBUG = True
EMAIL_HOST_USER = "ricardo.silva@ipma.pt"
SENDFILE_BACKEND = "sendfile.backends.development"

OSEOSERVER_PRODUCT_ORDER = {
    "enabled": False,
    "automatic_approval": False,
    "notify_creation": True,
    "item_processor": "oseoserver.orderpreparation.exampleorderprocessor."
                      "ExampleOrderProcessor",
    "item_availability_days": 10,
}

OSEOSERVER_PROCESSING_OPTIONS = [
    {
        "name": "dummy option",
        "description": "A dummy option",
        "multiple_entries": False,
        "choices": ["first", "second"],
    }
]

OSEOSERVER_ONLINE_DATA_ACCESS_OPTIONS = [
    "http",
    "ftp",
]

OSEOSERVER_COLLECTIONS = [
    {
        "name": "dummy_collection",
        "catalogue_endpoint": "http://localhost",
        "collection_identifier": "dummy_collection_id",
        "product_price": 0,
        "generation_frequency": "Once per hour",
        "product_order": {
            "enabled": False,
            "order_processing_fee": 0,
            "options": ["dummy option",],
            "online_data_access_options": ["http",],
            "online_data_delivery_options": [],
            "media_delivery_options": [],
            "payment_options": [],
            "scene_selection_options": [],
        },
    },
]
