from django.db import migrations


def update_usernames(apps, schema_editor):
    UserSocialAuth = apps.get_model('social_django', 'UserSocialAuth')
    User = apps.get_model('sa_api_v2', 'User')

    for social_auth in UserSocialAuth.objects.select_related('user').all():
        user = social_auth.user
        if not user:
            continue
        provider = social_auth.provider
        prefix = f'{provider}:'
        if not user.username.startswith(prefix):
            new_username = f'{prefix}{user.username}'

            counter = 1
            base_new_username = new_username
            while User.objects.filter(username=new_username).exclude(pk=user.pk).exists():
                new_username = f'{base_new_username}{counter}'
                counter += 1

            user.username = new_username
            user.save(update_fields=['username'])


def reverse_usernames(apps, schema_editor):
    UserSocialAuth = apps.get_model('social_django', 'UserSocialAuth')

    for social_auth in UserSocialAuth.objects.select_related('user').all():
        user = social_auth.user
        if not user:
            continue
        provider = social_auth.provider
        prefix = f'{provider}:'
        if user.username.startswith(prefix):
            user.username = user.username[len(prefix):]
            user.save(update_fields=['username'])


class Migration(migrations.Migration):
    dependencies = [
        ('dynamic_social_auth', '0006_oauth2provider_default_scope'),
        ('social_django', '0001_initial'),
        ('sa_api_v2', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(update_usernames, reverse_code=reverse_usernames),
    ]
