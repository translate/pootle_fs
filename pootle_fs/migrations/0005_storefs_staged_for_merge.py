# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_fs', '0004_projectfs_current_config'),
    ]

    operations = [
        migrations.AddField(
            model_name='storefs',
            name='staged_for_merge',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
