# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_fs', '0002_auto_20151012_2136'),
    ]

    operations = [
        migrations.AddField(
            model_name='storefs',
            name='staged_for_removal',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
