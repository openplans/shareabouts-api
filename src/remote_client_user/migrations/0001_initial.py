# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('oauth2', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='ClientPermissions',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('allow_remote_signin', models.BooleanField(default=False)),
                ('allow_remote_signup', models.BooleanField(default=False)),
                ('client', models.OneToOneField(related_name='permissions', to='oauth2.Client')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
