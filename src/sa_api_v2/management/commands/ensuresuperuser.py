from os import environ
from django.contrib.auth import get_user_model
from django.contrib.auth.management.commands import createsuperuser

import logging
log = logging.getLogger(__name__)


class Command(createsuperuser.Command):
    help = "Used to create a superuser, if one doesn't exist."

    def handle(self, *args, **options):
        username = environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')

        UserModel = get_user_model()
        if UserModel.objects.filter(username=username).exists():
            log.info(f'Superuser {username} already exists.')
            return

        return super().handle(*args, **options)
