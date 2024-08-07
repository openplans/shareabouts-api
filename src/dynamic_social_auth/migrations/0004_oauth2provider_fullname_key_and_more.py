# Generated by Django 4.2.9 on 2024-02-12 05:10

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("dynamic_social_auth", "0003_oauth2provider_access_token_param_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="oauth2provider",
            name="fullname_key",
            field=models.CharField(
                default="fullname",
                help_text="\n        The default key name where the user's full name field is defined, it’s\n        primarily used for display purposes.\n    ",
            ),
        ),
        migrations.AddField(
            model_name="oauth2provider",
            name="username_key",
            field=models.CharField(
                default="username",
                help_text="\n        The default key name where the user name field is defined, it’s used in\n        the auth process when some basic user data is returned.\n    ",
            ),
        ),
    ]
