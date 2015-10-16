# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_fs', '0003_storefs_staged_for_removal'),
    ]

    operations = [
        migrations.AddField(
            model_name='projectfs',
            name='current_config',
            field=models.FileField(null=True, upload_to=b'', blank=True),
            preserve_default=True,
        ),
    ]
