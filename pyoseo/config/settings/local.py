from __future__ import absolute_import

from .base import *

DEBUG = True
SENDFILE_BACKEND = "sendfile.backends.development"

OSEOSERVER_PRODUCT_ORDER = {
    "enabled": True,
    "automatic_approval": True,
    "notify_creation": True,
    "item_processor": ("oseoserver.orderpreparation.exampleorderprocessor."
                       "ExampleOrderProcessor"),
    "item_availability_days": 10,
}

OSEOSERVER_PROCESSING_OPTIONS = []

OSEOSERVER_ONLINE_DATA_ACCESS_OPTIONS = [
    {
        "protocol":"http",
        "fee": 0,
    },
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
]
