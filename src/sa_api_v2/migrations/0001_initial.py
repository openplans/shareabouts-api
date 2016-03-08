# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.core.validators
import storages.backends.s3boto
import sa_api_v2.models.mixins
import sa_api_v2.models.core
import django.contrib.gis.db.models.fields
import sa_api_v2.models.profiles
import sa_api_v2.apikey.models
import django.utils.timezone
from django.conf import settings
import sa_api_v2.models.caching


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0006_require_contenttypes_0002'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(null=True, verbose_name='last login', blank=True)),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, max_length=30, validators=[django.core.validators.RegexValidator('^[\\w.@+-]+$', 'Enter a valid username. This value may contain only letters, numbers and @/./+/-/_ characters.', 'invalid')], help_text='Required. 30 characters or fewer. Letters, digits and @/./+/-/_ only.', unique=True, verbose_name='username')),
                ('first_name', models.CharField(max_length=30, verbose_name='first name', blank=True)),
                ('last_name', models.CharField(max_length=30, verbose_name='last name', blank=True)),
                ('email', models.EmailField(max_length=254, verbose_name='email address', blank=True)),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
            ],
            options={
                'db_table': 'auth_user',
            },
            bases=(sa_api_v2.models.caching.CacheClearingModel, models.Model),
            managers=[
                ('objects', sa_api_v2.models.profiles.ShareaboutsUserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Action',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_datetime', models.DateTimeField(default=django.utils.timezone.now, db_index=True, blank=True)),
                ('updated_datetime', models.DateTimeField(auto_now=True, db_index=True)),
                ('action', models.CharField(default=b'create', max_length=16)),
                ('source', models.TextField(null=True, blank=True)),
            ],
            options={
                'ordering': ['-created_datetime'],
                'db_table': 'sa_api_activity',
            },
            bases=(sa_api_v2.models.caching.CacheClearingModel, models.Model),
        ),
        migrations.CreateModel(
            name='ApiKey',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('key', models.CharField(default=sa_api_v2.apikey.models.generate_unique_api_key, unique=True, max_length=32)),
                ('logged_ip', models.IPAddressField(null=True, blank=True)),
                ('last_used', models.DateTimeField(default=django.utils.timezone.now, blank=True)),
            ],
            options={
                'db_table': 'apikey_apikey',
            },
            bases=(sa_api_v2.models.mixins.CloneableModelMixin, models.Model),
        ),
        migrations.CreateModel(
            name='Attachment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_datetime', models.DateTimeField(default=django.utils.timezone.now, db_index=True, blank=True)),
                ('updated_datetime', models.DateTimeField(auto_now=True, db_index=True)),
                ('file', models.FileField(storage=storages.backends.s3boto.S3BotoStorage(), upload_to=sa_api_v2.models.core.timestamp_filename)),
                ('name', models.CharField(max_length=128, null=True, blank=True)),
            ],
            options={
                'db_table': 'sa_api_attachment',
            },
            bases=(sa_api_v2.models.caching.CacheClearingModel, models.Model),
        ),
        migrations.CreateModel(
            name='DataIndex',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('attr_name', models.CharField(max_length=100, verbose_name=b'Attribute name', db_index=True)),
                ('attr_type', models.CharField(default=b'string', max_length=10, verbose_name=b'Attribute type', choices=[(b'string', b'String')])),
            ],
            bases=(sa_api_v2.models.mixins.CloneableModelMixin, models.Model),
        ),
        migrations.CreateModel(
            name='DataSet',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('display_name', models.CharField(max_length=128)),
                ('slug', models.SlugField(default='', max_length=128)),
                ('owner', models.ForeignKey(related_name='datasets', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'sa_api_dataset',
            },
            bases=(sa_api_v2.models.mixins.CloneableModelMixin, sa_api_v2.models.caching.CacheClearingModel, models.Model),
        ),
        migrations.CreateModel(
            name='DataSetPermission',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('submission_set', models.CharField(help_text=b'Either the name of a submission set (e.g., "comments"), or "places". Leave blank to refer to all things.', max_length=128, blank=True)),
                ('can_retrieve', models.BooleanField(default=True)),
                ('can_create', models.BooleanField(default=False)),
                ('can_update', models.BooleanField(default=False)),
                ('can_destroy', models.BooleanField(default=False)),
                ('can_access_protected', models.BooleanField(default=False)),
                ('priority', models.PositiveIntegerField(blank=True)),
                ('dataset', models.ForeignKey(related_name='permissions', to='sa_api_v2.DataSet')),
            ],
            bases=(sa_api_v2.models.mixins.CloneableModelMixin, sa_api_v2.models.caching.CacheClearingModel, models.Model),
        ),
        migrations.CreateModel(
            name='DataSnapshot',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('json', models.TextField()),
                ('csv', models.TextField()),
            ],
            options={
                'db_table': 'sa_api_datasnapshot',
            },
        ),
        migrations.CreateModel(
            name='DataSnapshotRequest',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('submission_set', models.CharField(max_length=128)),
                ('include_private', models.BooleanField(default=False)),
                ('include_invisible', models.BooleanField(default=False)),
                ('include_submissions', models.BooleanField(default=False)),
                ('requested_at', models.DateTimeField(auto_now_add=True)),
                ('status', models.TextField(default=b'', blank=True)),
                ('fulfilled_at', models.DateTimeField(null=True)),
                ('guid', models.TextField(default=b'', unique=True, blank=True)),
                ('dataset', models.ForeignKey(to='sa_api_v2.DataSet')),
                ('requester', models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'db_table': 'sa_api_datasnapshotrequest',
            },
        ),
        migrations.CreateModel(
            name='Group',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text=b'What is the name of the group to which users with this group belong? For example: "judges", "administrators", "winners", ...', max_length=32)),
                ('dataset', models.ForeignKey(related_name='groups', to='sa_api_v2.DataSet', help_text=b'Which dataset does this group apply to?')),
                ('submitters', models.ManyToManyField(related_name='_groups', to=settings.AUTH_USER_MODEL, blank=True)),
            ],
            options={
                'db_table': 'sa_api_group',
            },
            bases=(sa_api_v2.models.mixins.CloneableModelMixin, models.Model),
        ),
        migrations.CreateModel(
            name='GroupPermission',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('submission_set', models.CharField(help_text=b'Either the name of a submission set (e.g., "comments"), or "places". Leave blank to refer to all things.', max_length=128, blank=True)),
                ('can_retrieve', models.BooleanField(default=True)),
                ('can_create', models.BooleanField(default=False)),
                ('can_update', models.BooleanField(default=False)),
                ('can_destroy', models.BooleanField(default=False)),
                ('can_access_protected', models.BooleanField(default=False)),
                ('priority', models.PositiveIntegerField(blank=True)),
                ('group', models.ForeignKey(related_name='permissions', to='sa_api_v2.Group')),
            ],
            bases=(sa_api_v2.models.mixins.CloneableModelMixin, sa_api_v2.models.caching.CacheClearingModel, models.Model),
        ),
        migrations.CreateModel(
            name='IndexedValue',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('value', models.CharField(max_length=100, null=True, db_index=True)),
                ('index', models.ForeignKey(related_name='values', to='sa_api_v2.DataIndex')),
            ],
        ),
        migrations.CreateModel(
            name='KeyPermission',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('submission_set', models.CharField(help_text=b'Either the name of a submission set (e.g., "comments"), or "places". Leave blank to refer to all things.', max_length=128, blank=True)),
                ('can_retrieve', models.BooleanField(default=True)),
                ('can_create', models.BooleanField(default=False)),
                ('can_update', models.BooleanField(default=False)),
                ('can_destroy', models.BooleanField(default=False)),
                ('can_access_protected', models.BooleanField(default=False)),
                ('priority', models.PositiveIntegerField(blank=True)),
                ('key', models.ForeignKey(related_name='permissions', to='sa_api_v2.ApiKey')),
            ],
            bases=(sa_api_v2.models.mixins.CloneableModelMixin, sa_api_v2.models.caching.CacheClearingModel, models.Model),
        ),
        migrations.CreateModel(
            name='Origin',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('pattern', models.CharField(help_text=b'The origin pattern, e.g., https://*.github.io, http://localhost:*, http*://map.phila.gov', max_length=100)),
                ('logged_ip', models.IPAddressField(null=True, blank=True)),
                ('last_used', models.DateTimeField(default=django.utils.timezone.now, blank=True)),
                ('dataset', models.ForeignKey(related_name='origins', blank=True, to='sa_api_v2.DataSet')),
            ],
            options={
                'db_table': 'cors_origin',
            },
            bases=(sa_api_v2.models.mixins.CloneableModelMixin, models.Model),
        ),
        migrations.CreateModel(
            name='OriginPermission',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('submission_set', models.CharField(help_text=b'Either the name of a submission set (e.g., "comments"), or "places". Leave blank to refer to all things.', max_length=128, blank=True)),
                ('can_retrieve', models.BooleanField(default=True)),
                ('can_create', models.BooleanField(default=False)),
                ('can_update', models.BooleanField(default=False)),
                ('can_destroy', models.BooleanField(default=False)),
                ('can_access_protected', models.BooleanField(default=False)),
                ('priority', models.PositiveIntegerField(blank=True)),
                ('origin', models.ForeignKey(related_name='permissions', to='sa_api_v2.Origin')),
            ],
            bases=(sa_api_v2.models.mixins.CloneableModelMixin, sa_api_v2.models.caching.CacheClearingModel, models.Model),
        ),
        migrations.CreateModel(
            name='SubmittedThing',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_datetime', models.DateTimeField(default=django.utils.timezone.now, db_index=True, blank=True)),
                ('updated_datetime', models.DateTimeField(auto_now=True, db_index=True)),
                ('data', models.TextField(default=b'{}')),
                ('visible', models.BooleanField(default=True, db_index=True)),
            ],
            options={
                'db_table': 'sa_api_submittedthing',
            },
            bases=(sa_api_v2.models.mixins.CloneableModelMixin, sa_api_v2.models.caching.CacheClearingModel, models.Model),
        ),
        migrations.CreateModel(
            name='Webhook',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_datetime', models.DateTimeField(default=django.utils.timezone.now, db_index=True, blank=True)),
                ('updated_datetime', models.DateTimeField(auto_now=True, db_index=True)),
                ('submission_set', models.CharField(max_length=128)),
                ('event', models.CharField(default=b'add', max_length=128, choices=[(b'add', b'On add')])),
                ('url', models.URLField(max_length=2048)),
                ('dataset', models.ForeignKey(related_name='webhooks', to='sa_api_v2.DataSet')),
            ],
            options={
                'db_table': 'sa_api_webhook',
            },
        ),
        migrations.CreateModel(
            name='Place',
            fields=[
                ('submittedthing_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='sa_api_v2.SubmittedThing')),
                ('geometry', django.contrib.gis.db.models.fields.GeometryField(srid=4326)),
            ],
            options={
                'ordering': ['-updated_datetime'],
                'db_table': 'sa_api_place',
            },
            bases=('sa_api_v2.submittedthing',),
        ),
        migrations.CreateModel(
            name='Submission',
            fields=[
                ('submittedthing_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='sa_api_v2.SubmittedThing')),
                ('set_name', models.TextField(db_index=True)),
                ('place', models.ForeignKey(related_name='submissions', to='sa_api_v2.Place')),
            ],
            options={
                'ordering': ['-updated_datetime'],
                'db_table': 'sa_api_submission',
            },
            bases=('sa_api_v2.submittedthing',),
        ),
        migrations.AddField(
            model_name='submittedthing',
            name='dataset',
            field=models.ForeignKey(related_name='things', blank=True, to='sa_api_v2.DataSet'),
        ),
        migrations.AddField(
            model_name='submittedthing',
            name='submitter',
            field=models.ForeignKey(related_name='things', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='indexedvalue',
            name='thing',
            field=models.ForeignKey(related_name='indexed_values', to='sa_api_v2.SubmittedThing'),
        ),
        migrations.AddField(
            model_name='datasnapshot',
            name='request',
            field=models.OneToOneField(related_name='fulfillment', to='sa_api_v2.DataSnapshotRequest'),
        ),
        migrations.AddField(
            model_name='dataindex',
            name='dataset',
            field=models.ForeignKey(related_name='indexes', to='sa_api_v2.DataSet'),
        ),
        migrations.AddField(
            model_name='attachment',
            name='thing',
            field=models.ForeignKey(related_name='attachments', to='sa_api_v2.SubmittedThing'),
        ),
        migrations.AddField(
            model_name='apikey',
            name='dataset',
            field=models.ForeignKey(related_name='keys', blank=True, to='sa_api_v2.DataSet'),
        ),
        migrations.AddField(
            model_name='action',
            name='thing',
            field=models.ForeignKey(related_name='actions', db_column=b'data_id', to='sa_api_v2.SubmittedThing'),
        ),
        migrations.AddField(
            model_name='user',
            name='groups',
            field=models.ManyToManyField(related_query_name='user', related_name='user_set', to='auth.Group', blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', verbose_name='groups'),
        ),
        migrations.AddField(
            model_name='user',
            name='user_permissions',
            field=models.ManyToManyField(related_query_name='user', related_name='user_set', to='auth.Permission', blank=True, help_text='Specific permissions for this user.', verbose_name='user permissions'),
        ),
        migrations.AlterUniqueTogether(
            name='group',
            unique_together=set([('name', 'dataset')]),
        ),
        migrations.AlterUniqueTogether(
            name='dataset',
            unique_together=set([('owner', 'slug')]),
        ),
    ]
