"""
Load initial data into pyoseo
"""

from django.core.management import BaseCommand
import oseoserver.models as models


class Command(BaseCommand):
    args = ""

    help = __doc__

    _products = (
        ("LST", "364a3048-d012-11e1-9678-0019995d2a56"),
        ("LST10", "phony"),
    )

    _option_groups = (
        ("pyoseo options", "Options available for customizing orders "
         "and individual order items"),
    )

    _order_types = (
        "PRODUCT_ORDER",
        "MASSIVE_ORDER",
        "SUBSCRIPTION_ORDER",
        "TASKING_ORDER",
    )

    _online_data_accesses = ("http", "ftp")


    def handle(self, *args, **options):
        self._create_products()
        self._create_option_groups()
        self._create_order_types()
        self._create_online_data_accesses()
        self._create_group_delivery_options()
        self._create_deliveryoption_order_types()

    def _create_option_groups(self):
        self.stdout.write("Creating default option groups...")
        for name, desc in self._option_groups:
            obj, created = models.OptionGroup.objects.get_or_create(
                name=name,
                description=desc
            )

    def _create_order_types(self):
        self.stdout.write("Creating default order types...")
        for t in self._order_types:
            obj, created = models.OrderType.objects.get_or_create(name=t)

    def _create_online_data_accesses(self):
        self.stdout.write("Creating default online data access protocols...")
        for p in self._online_data_accesses:
            obj, created = models.OnlineDataAccess.objects.get_or_create(
                protocol=p)

    def _create_products(self):
        self.stdout.write("Creating default products...")
        for name, collection in self._products:
            obj, created = models.Product.objects.get_or_create(
                short_name=name, collection_id=collection)

    def _create_group_delivery_options(self):
        self.stdout.write("Creating default group delivery options...")
        opt_group = models.OptionGroup.objects.get(
            name=self._option_groups[0][0])
        for access in self._online_data_accesses:
            online_data_access = models.OnlineDataAccess.objects.get(
                protocol=access)
            del_opt = online_data_access.deliveryoption_ptr
            obj, created = models.GroupDeliveryOption.objects.get_or_create(
                delivery_option=del_opt, option_group=opt_group)

    def _create_deliveryoption_order_types(self):
        self.stdout.write("Creating default delivery option order types...")
        for access in self._online_data_accesses:
            online_data_access = models.OnlineDataAccess.objects.get(
                protocol=access)
            del_opt = online_data_access.deliveryoption_ptr
            for order_type in models.OrderType.objects.all():
                manager = models.DeliveryOptionOrderType.objects
                obj, created = manager.get_or_create(
                    delivery_option=del_opt,
                    order_type=order_type
                )
