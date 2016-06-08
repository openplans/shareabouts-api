# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.OAUTH2_PROVIDER_APPLICATION_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ClientPermissions',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('allow_remote_signin', models.BooleanField(default=False)),
                ('allow_remote_signup', models.BooleanField(default=False)),
                ('client', models.OneToOneField(related_name='permissions', to=settings.OAUTH2_PROVIDER_APPLICATION_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
