# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('oseoserver', '0014_auto_20141227_2013'),
    ]

    operations = [
        migrations.CreateModel(
            name='OseoGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('description', models.TextField(blank=True)),
                ('authentication_class', models.CharField(help_text=b'Python path to a custom authentication class to use whenvalidating orders for users belonging to this group', max_length=255, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.RemoveField(
            model_name='collection',
            name='catalogue_id',
        ),
        migrations.AddField(
            model_name='batch',
            name='completed_on',
            field=models.DateTimeField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='batch',
            name='created_on',
            field=models.DateTimeField(default=datetime.datetime(2014, 12, 30, 19, 3, 26, 272996), auto_now_add=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='batch',
            name='updated_on',
            field=models.DateTimeField(null=True, editable=False, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='collection',
            name='authorized_groups',
            field=models.ManyToManyField(to='oseoserver.OseoGroup', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='collection',
            name='catalogue_endpoint',
            field=models.CharField(default='dummy', help_text=b'URL of the CSW server where this collection is available', max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='collection',
            name='collection_id',
            field=models.CharField(default='dummy', help_text=b'Identifier of the dataset series for this collection in the catalogue', unique=True, max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='collection',
            name='item_preparation_class',
            field=models.CharField(default='dummy', help_text=b'Python path to a custom class used for preparing order items', max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='oseouser',
            name='oseo_group',
            field=models.ForeignKey(default=1, to='oseoserver.OseoGroup'),
            preserve_default=False,
        ),
    ]
