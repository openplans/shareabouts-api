# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sa_api_v2', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='datasetpermission',
            name='can_access_protected',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='grouppermission',
            name='can_access_protected',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='keypermission',
            name='can_access_protected',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='originpermission',
            name='can_access_protected',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
