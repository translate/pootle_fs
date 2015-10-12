# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_fs', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='storefs',
            name='last_sync_hash',
            field=models.CharField(max_length=64, null=True, blank=True),
            preserve_default=True,
        ),
    ]
