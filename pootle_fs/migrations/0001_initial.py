# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_project', '0002_auto_20150923_1715'),
        ('pootle_store', '0002_make_suggestion_user_not_null'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProjectFS',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('url', models.URLField()),
                ('fs_type', models.CharField(max_length=32)),
                ('enabled', models.BooleanField(default=True)),
                ('fetch_frequency', models.IntegerField(default=0)),
                ('push_frequency', models.IntegerField(default=0)),
                ('pootle_config', models.CharField(default=b'.pootle.ini', max_length=32)),
                ('project', models.ForeignKey(related_name='fs', to='pootle_project.Project', unique=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='StoreFS',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('pootle_path', models.CharField(max_length=255)),
                ('path', models.CharField(max_length=255)),
                ('last_sync_revision', models.IntegerField(null=True, blank=True)),
                ('last_sync_mtime', models.DateTimeField(null=True, blank=True)),
                ('last_sync_hash', models.CharField(max_length=32, null=True, blank=True)),
                ('project', models.ForeignKey(related_name='store_fs', to='pootle_project.Project')),
                ('store', models.ForeignKey(related_name='fs', blank=True, to='pootle_store.Store', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
