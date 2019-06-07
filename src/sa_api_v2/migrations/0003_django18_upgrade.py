# -*- coding: utf-8 -*-


from django.db import migrations, models
import sa_api_v2.models.profiles
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('sa_api_v2', '0002_auto__add_protected_access_flag'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='user',
            managers=[
                ('objects', sa_api_v2.models.profiles.ShareaboutsUserManager()),
            ],
        ),
        migrations.AlterField(
            model_name='action',
            name='action',
            field=models.CharField(max_length=16, default='create'),
        ),
        migrations.AlterField(
            model_name='action',
            name='thing',
            field=models.ForeignKey(on_delete=models.CASCADE, db_column='data_id', related_name='actions', to='sa_api_v2.SubmittedThing'),
        ),
        migrations.AlterField(
            model_name='apikey',
            name='logged_ip',
            field=models.GenericIPAddressField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='dataindex',
            name='attr_name',
            field=models.CharField(verbose_name='Attribute name', max_length=100, db_index=True),
        ),
        migrations.AlterField(
            model_name='dataindex',
            name='attr_type',
            field=models.CharField(verbose_name='Attribute type', max_length=10, default='string', choices=[('string', 'String')]),
        ),
        migrations.AlterField(
            model_name='datasetpermission',
            name='submission_set',
            field=models.CharField(max_length=128, blank=True, help_text='Either the name of a submission set (e.g., "comments"), or "places". Leave blank to refer to all things.'),
        ),
        migrations.AlterField(
            model_name='datasnapshotrequest',
            name='guid',
            field=models.TextField(unique=True, blank=True, default=''),
        ),
        migrations.AlterField(
            model_name='datasnapshotrequest',
            name='status',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AlterField(
            model_name='group',
            name='dataset',
            field=models.ForeignKey(on_delete=models.CASCADE, help_text='Which dataset does this group apply to?', related_name='groups', to='sa_api_v2.DataSet'),
        ),
        migrations.AlterField(
            model_name='group',
            name='name',
            field=models.CharField(max_length=32, help_text='What is the name of the group to which users with this group belong? For example: "judges", "administrators", "winners", ...'),
        ),
        migrations.AlterField(
            model_name='grouppermission',
            name='submission_set',
            field=models.CharField(max_length=128, blank=True, help_text='Either the name of a submission set (e.g., "comments"), or "places". Leave blank to refer to all things.'),
        ),
        migrations.AlterField(
            model_name='keypermission',
            name='submission_set',
            field=models.CharField(max_length=128, blank=True, help_text='Either the name of a submission set (e.g., "comments"), or "places". Leave blank to refer to all things.'),
        ),
        migrations.AlterField(
            model_name='origin',
            name='logged_ip',
            field=models.GenericIPAddressField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='origin',
            name='pattern',
            field=models.CharField(max_length=100, help_text='The origin pattern, e.g., https://*.github.io, http://localhost:*, http*://map.phila.gov'),
        ),
        migrations.AlterField(
            model_name='originpermission',
            name='submission_set',
            field=models.CharField(max_length=128, blank=True, help_text='Either the name of a submission set (e.g., "comments"), or "places". Leave blank to refer to all things.'),
        ),
        migrations.AlterField(
            model_name='submittedthing',
            name='data',
            field=models.TextField(default='{}'),
        ),
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(verbose_name='email address', max_length=254, blank=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='groups',
            field=models.ManyToManyField(verbose_name='groups', blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.Group'),
        ),
        migrations.AlterField(
            model_name='user',
            name='last_login',
            field=models.DateTimeField(verbose_name='last login', blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='username',
            field=models.CharField(verbose_name='username', max_length=30, unique=True, help_text='Required. 30 characters or fewer. Letters, digits and @/./+/-/_ only.', validators=[django.core.validators.RegexValidator('^[\\w.@+-]+$', 'Enter a valid username. This value may contain only letters, numbers and @/./+/-/_ characters.', 'invalid')], error_messages={'unique': 'A user with that username already exists.'}),
        ),
        migrations.AlterField(
            model_name='webhook',
            name='event',
            field=models.CharField(max_length=128, default='add', choices=[('add', 'On add')]),
        ),
    ]
