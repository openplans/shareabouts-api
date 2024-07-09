# Generated by Django 4.2.9 on 2024-02-12 03:24

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("dynamic_social_auth", "0002_alter_oauth2provider_options_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="oauth2provider",
            name="access_token_param",
            field=models.CharField(
                default="access_token",
                help_text="\n        The query string key for the `access_token` parameter when retrieving\n        user data. This field is only used if `user_data_url` is specified, and\n        `use_querystring_for_user_data` is True.\n    ",
                max_length=32,
            ),
        ),
        migrations.AddField(
            model_name="oauth2provider",
            name="auth_header_prefix",
            field=models.CharField(
                default="bearer",
                help_text="\n        The prefix for the `Authorization` header when retrieving user data.\n        This field is only used if `user_data_url` is specified, and\n        `use_auth_header_for_user_data` is True.\n    ",
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name="oauth2provider",
            name="use_auth_header_for_user_data",
            field=models.BooleanField(
                default=True,
                help_text="\n        After auth token is retrieved, if `use_auth_header_for_user_data` is\n        True, and `user_data_url` is specified, then retrieve user data from\n        the URL, putting the access token in an Authorization header\n    ",
            ),
        ),
        migrations.AddField(
            model_name="oauth2provider",
            name="use_querystring_for_user_data",
            field=models.BooleanField(
                default=False,
                help_text="\n        After auth token is retrieved, if `use_querystring_for_user_data` is\n        True, and `user_data_url` is specified, then retrieve user data from\n        the URL, putting the access token in the query string.\n    ",
            ),
        ),
        migrations.AddField(
            model_name="oauth2provider",
            name="user_data_url",
            field=models.URLField(
                blank=True,
                help_text="\n        URL to load user data from, after the access token is retrieved.\n    ",
                null=True,
            ),
        ),
    ]