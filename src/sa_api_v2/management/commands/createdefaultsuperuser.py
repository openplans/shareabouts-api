from os import environ
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

import logging
log = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Create a one-off default administrative user.'

    def handle(self, *args, **options):
        log.info('Creating user...')

        User = get_user_model()
        User.objects.create_superuser(
            username=environ.get('SHAREABOUTS_ADMIN_USERNAME', 'admin'),
            email=environ.get('SHAREABOUTS_ADMIN_EMAIL', 'admin@example.com'),
            password=environ.get('SHAREABOUTS_ADMIN_PASSWORD', 'admin'))
