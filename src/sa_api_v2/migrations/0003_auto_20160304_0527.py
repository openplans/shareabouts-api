# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import sa_api_v2.models.core
import storages.backends.s3boto


class Migration(migrations.Migration):

    dependencies = [
        ('sa_api_v2', '0002_auto__add_protected_access_flag'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attachment',
            name='file',
            field=models.FileField(storage=storages.backends.s3boto.S3BotoStorage(), upload_to=sa_api_v2.models.core.timestamp_filename),
            preserve_default=True,
        ),
    ]
