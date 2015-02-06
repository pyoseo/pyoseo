# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
from decimal import Decimal


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Batch',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
                'verbose_name_plural': 'batches',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Collection',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('catalogue_id', models.CharField(unique=True, max_length=255)),
                ('short_name', models.CharField(unique=True, max_length=50)),
                ('product_price', models.DecimalField(default=Decimal('0'), help_text=b'The price of an individual product', max_digits=5, decimal_places=2)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CollectionConfiguration',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('enabled', models.BooleanField(default=False)),
                ('automatic_approval', models.BooleanField(default=False, help_text=b'Should this type of order be approved automatically for the selected collection?')),
                ('name', models.CharField(max_length=100)),
                ('description', models.CharField(max_length=255, blank=True)),
                ('order_processing_fee', models.DecimalField(default=Decimal('0'), max_digits=5, decimal_places=2)),
                ('collection', models.ForeignKey(to='oseoserver.Collection')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CustomizableItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('status', models.CharField(default=b'Submitted', help_text=b'initial status', max_length=50, choices=[(b'Submitted', b'Submitted'), (b'Accepted', b'Accepted'), (b'InProduction', b'InProduction'), (b'Suspended', b'Suspended'), (b'Cancelled', b'Cancelled'), (b'Completed', b'Completed'), (b'Failed', b'Failed'), (b'Terminated', b'Terminated'), (b'Downloaded', b'Downloaded')])),
                ('additional_status_info', models.TextField(help_text=b'Additional information about the status', blank=True)),
                ('mission_specific_status_info', models.TextField(help_text=b'Additional information about the status that is specific to the mission', blank=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('completed_on', models.DateTimeField(null=True, blank=True)),
                ('status_changed_on', models.DateTimeField(null=True, editable=False, blank=True)),
                ('remark', models.TextField(help_text=b'Some specific remark about the item', blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DeliveryInformation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('first_name', models.CharField(max_length=50, blank=True)),
                ('last_name', models.CharField(max_length=50, blank=True)),
                ('company_ref', models.CharField(max_length=50, blank=True)),
                ('street_address', models.CharField(max_length=50, blank=True)),
                ('city', models.CharField(max_length=50, blank=True)),
                ('state', models.CharField(max_length=50, blank=True)),
                ('postal_code', models.CharField(max_length=50, blank=True)),
                ('country', models.CharField(max_length=50, blank=True)),
                ('post_box', models.CharField(max_length=50, blank=True)),
                ('telephone', models.CharField(max_length=50, blank=True)),
                ('fax', models.CharField(max_length=50, blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DeliveryOption',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('delivery_fee', models.DecimalField(default=Decimal('0'), max_digits=5, decimal_places=2)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DeliveryOptionGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text=b'Id for the group of options', max_length=40)),
                ('description', models.CharField(help_text=b'Description of the order option group', max_length=255, blank=True)),
                ('collection_configuration', models.ForeignKey(related_name='oseoserver_deliveryoptiongroup_related', to='oseoserver.CollectionConfiguration')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='GroupedDeliveryOption',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('group', models.ForeignKey(to='oseoserver.DeliveryOptionGroup')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='GroupedOption',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='GroupedPaymentOption',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='GroupedSceneSelectionOption',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='InvoiceAddress',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('first_name', models.CharField(max_length=50, blank=True)),
                ('last_name', models.CharField(max_length=50, blank=True)),
                ('company_ref', models.CharField(max_length=50, blank=True)),
                ('street_address', models.CharField(max_length=50, blank=True)),
                ('city', models.CharField(max_length=50, blank=True)),
                ('state', models.CharField(max_length=50, blank=True)),
                ('postal_code', models.CharField(max_length=50, blank=True)),
                ('country', models.CharField(max_length=50, blank=True)),
                ('post_box', models.CharField(max_length=50, blank=True)),
                ('telephone', models.CharField(max_length=50, blank=True)),
                ('fax', models.CharField(max_length=50, blank=True)),
            ],
            options={
                'verbose_name_plural': 'invoice addresses',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MediaDelivery',
            fields=[
                ('deliveryoption_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='oseoserver.DeliveryOption')),
                ('package_medium', models.CharField(blank=True, max_length=20, choices=[(b'NTP', b'NTP'), (b'DAT', b'DAT'), (b'Exabyte', b'Exabyte'), (b'CD-ROM', b'CD-ROM'), (b'DLT', b'DLT'), (b'D1', b'D1'), (b'DVD', b'DVD'), (b'BD', b'BD'), (b'LTO', b'LTO'), (b'LTO2', b'LTO2'), (b'LTO4', b'LTO4')])),
                ('shipping_instructions', models.CharField(blank=True, max_length=100, choices=[(b'as each product is ready', b'as each product is ready'), (b'once all products are ready', b'once all products are ready'), (b'other', b'other')])),
            ],
            options={
                'verbose_name_plural': 'media deliveries',
            },
            bases=('oseoserver.deliveryoption',),
        ),
        migrations.CreateModel(
            name='OnlineAddress',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('protocol', models.CharField(default=b'ftp', max_length=20, choices=[(b'ftp', b'ftp'), (b'sftp', b'sftp'), (b'ftps', b'ftps')])),
                ('server_address', models.CharField(max_length=255)),
                ('user_name', models.CharField(max_length=50, blank=True)),
                ('user_password', models.CharField(max_length=50, blank=True)),
                ('path', models.CharField(max_length=1024, blank=True)),
                ('delivery_information', models.ForeignKey(to='oseoserver.DeliveryInformation')),
            ],
            options={
                'verbose_name_plural': 'online addresses',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='OnlineDataAccess',
            fields=[
                ('deliveryoption_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='oseoserver.DeliveryOption')),
                ('protocol', models.CharField(default=b'ftp', unique=True, max_length=20, choices=[(b'ftp', b'ftp'), (b'sftp', b'sftp'), (b'ftps', b'ftps'), (b'P2P', b'P2P'), (b'wcs', b'wcs'), (b'wms', b'wms'), (b'e-mail', b'e-mail'), (b'dds', b'dds'), (b'http', b'http'), (b'https', b'https')])),
            ],
            options={
                'verbose_name_plural': 'online data accesses',
            },
            bases=('oseoserver.deliveryoption',),
        ),
        migrations.CreateModel(
            name='OnlineDataDelivery',
            fields=[
                ('deliveryoption_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='oseoserver.DeliveryOption')),
                ('protocol', models.CharField(default=b'ftp', unique=True, max_length=20, choices=[(b'ftp', b'ftp'), (b'sftp', b'sftp'), (b'ftps', b'ftps'), (b'P2P', b'P2P'), (b'wcs', b'wcs'), (b'wms', b'wms'), (b'e-mail', b'e-mail'), (b'dds', b'dds'), (b'http', b'http'), (b'https', b'https')])),
            ],
            options={
                'verbose_name_plural': 'online data deliveries',
            },
            bases=('oseoserver.deliveryoption',),
        ),
        migrations.CreateModel(
            name='Option',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('description', models.CharField(max_length=255, blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='OptionChoice',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('value', models.CharField(help_text=b'Value for this option', max_length=255)),
                ('option', models.ForeignKey(related_name='choices', to='oseoserver.Option')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='OptionGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text=b'Id for the group of options', max_length=40)),
                ('description', models.CharField(help_text=b'Description of the order option group', max_length=255, blank=True)),
                ('collection_configuration', models.ForeignKey(related_name='oseoserver_optiongroup_related', to='oseoserver.CollectionConfiguration')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('customizableitem_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='oseoserver.CustomizableItem')),
                ('last_describe_result_access_request', models.DateTimeField(null=True, blank=True)),
                ('reference', models.CharField(help_text=b'Some specific reference about this order', max_length=30, blank=True)),
                ('packaging', models.CharField(blank=True, max_length=30, choices=[(b'bzip2', b'bzip2')])),
                ('priority', models.CharField(blank=True, max_length=30, choices=[(b'STANDARD', b'STANDARD'), (b'FAST_TRACK', b'FAST_TRACK')])),
            ],
            options={
            },
            bases=('oseoserver.customizableitem',),
        ),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('customizableitem_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='oseoserver.CustomizableItem')),
                ('identifier', models.CharField(help_text=b'identifier for this order item. It is the product Id in the catalog', max_length=255, blank=True)),
                ('item_id', models.CharField(help_text=b'Id for the item in the order request', max_length=30)),
                ('file_name', models.CharField(help_text=b'name of the file that this order item represents', max_length=255, blank=True)),
                ('downloads', models.SmallIntegerField(default=0, help_text=b'Number of times this order item has been downloaded.')),
                ('batch', models.ForeignKey(related_name='order_items', to='oseoserver.Batch')),
                ('collection', models.ForeignKey(to='oseoserver.Collection')),
            ],
            options={
            },
            bases=('oseoserver.customizableitem',),
        ),
        migrations.CreateModel(
            name='OrderType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(default=b'PRODUCT_ORDER', unique=True, max_length=30, choices=[(b'PRODUCT_ORDER', b'PRODUCT_ORDER'), (b'MASSIVE_ORDER', b'MASSIVE_ORDER'), (b'SUBSCRIPTION_ORDER', b'SUBSCRIPTION_ORDER'), (b'TASKING_ORDER', b'TASKING_ORDER')])),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='OseoUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('disk_quota', models.SmallIntegerField(default=50, help_text=b'Disk space available to each user. Expressed in Gigabytes')),
                ('order_availability_days', models.SmallIntegerField(default=10, help_text=b'How many days does a completed order stay on the server, waiting to be downloaded')),
                ('delete_downloaded_order_files', models.BooleanField(default=True, help_text=b'If this option is selected, ordered items will be deleted from the server as soon as their download has been aknowledged. If not, the ordered items are only deleted after the expiration of the "order availability time" period.')),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PaymentOption',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('description', models.CharField(max_length=255, blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PaymentOptionGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text=b'Id for the group of options', max_length=40)),
                ('description', models.CharField(help_text=b'Description of the order option group', max_length=255, blank=True)),
                ('collection_configuration', models.ForeignKey(related_name='oseoserver_paymentoptiongroup_related', to='oseoserver.CollectionConfiguration')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SceneSelectionOption',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('description', models.CharField(max_length=255, blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SceneSelectionOptionChoice',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('value', models.CharField(help_text=b'Value for this option', max_length=255)),
                ('scene_selection_option', models.ForeignKey(related_name='choices', to='oseoserver.SceneSelectionOption')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SceneSelectionOptionGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text=b'Id for the group of options', max_length=40)),
                ('description', models.CharField(help_text=b'Description of the order option group', max_length=255, blank=True)),
                ('collection_configuration', models.ForeignKey(related_name='oseoserver_sceneselectionoptiongroup_related', to='oseoserver.CollectionConfiguration')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SelectedDeliveryOption',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('copies', models.PositiveSmallIntegerField(null=True, blank=True)),
                ('annotation', models.TextField(blank=True)),
                ('special_instructions', models.TextField(blank=True)),
                ('customizable_item', models.OneToOneField(related_name='selected_delivery_option', null=True, blank=True, to='oseoserver.CustomizableItem')),
                ('option', models.ForeignKey(to='oseoserver.DeliveryOption')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SelectedOption',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('value', models.CharField(help_text=b'Value for this option', max_length=255)),
                ('customizable_item', models.ForeignKey(related_name='selected_options', to='oseoserver.CustomizableItem')),
                ('option', models.ForeignKey(to='oseoserver.Option')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SelectedPaymentOption',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('option', models.ForeignKey(to='oseoserver.PaymentOption')),
                ('order_item', models.ForeignKey(to='oseoserver.OrderItem')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SelectedSceneSelectionOption',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('value', models.CharField(help_text=b'Value for this option', max_length=255)),
                ('option', models.ForeignKey(to='oseoserver.SceneSelectionOption')),
                ('order_item', models.ForeignKey(to='oseoserver.OrderItem')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='order',
            name='order_type',
            field=models.ForeignKey(related_name='orders', to='oseoserver.OrderType'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='order',
            name='user',
            field=models.ForeignKey(related_name='orders', to='oseoserver.OseoUser'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='invoiceaddress',
            name='order',
            field=models.OneToOneField(related_name='invoice_address', to='oseoserver.Order'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='groupedsceneselectionoption',
            name='group',
            field=models.ForeignKey(to='oseoserver.SceneSelectionOptionGroup'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='groupedsceneselectionoption',
            name='option',
            field=models.ForeignKey(to='oseoserver.SceneSelectionOption'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='groupedpaymentoption',
            name='group',
            field=models.ForeignKey(to='oseoserver.PaymentOptionGroup'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='groupedpaymentoption',
            name='option',
            field=models.ForeignKey(to='oseoserver.PaymentOption'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='groupedoption',
            name='group',
            field=models.ForeignKey(to='oseoserver.OptionGroup'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='groupedoption',
            name='option',
            field=models.ForeignKey(to='oseoserver.Option'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='groupeddeliveryoption',
            name='option',
            field=models.ForeignKey(to='oseoserver.DeliveryOption'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='deliveryinformation',
            name='order',
            field=models.OneToOneField(related_name='delivery_information', to='oseoserver.Order'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='collectionconfiguration',
            name='order_type',
            field=models.ForeignKey(to='oseoserver.OrderType'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='batch',
            name='order',
            field=models.ForeignKey(related_name='batches', to='oseoserver.Order'),
            preserve_default=True,
        ),
    ]
