from os import environ
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

import logging
log = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Create a dataset that can be used with the sample shareabouts client settings.'

    def handle(self, *args, **options):
        from sa_api_v2.models import DataSet, User, KeyPermission
        from sa_api_v2.apikey.models import ApiKey

        username = environ.get('SHAREABOUTS_DATASET_USERNAME', 'demo-user')
        slug = environ.get('SHAREABOUTS_DATASET_SLUG', 'demo-data')
        key = environ.get('SHAREABOUTS_DATASET_KEY', 'NTNhODE3Y2IzODlmZGZjMWU4NmU3NDhj')

        user, created = User.objects.get_or_create(username=username)
        ds, created = DataSet.objects.get_or_create(owner=user, display_name=slug, slug=slug)
        key, created = ApiKey.objects.get_or_create(dataset=ds, key=key)

        if key.permissions.count() == 0:
            key.permissions.add(
                KeyPermission(submission_set='places', can_retrieve=True, can_create=True, can_update=False, can_destroy=False),
                KeyPermission(submission_set='comments', can_retrieve=True, can_create=True, can_update=False, can_destroy=False),
                KeyPermission(submission_set='supports', can_retrieve=True, can_create=True, can_update=False, can_destroy=True),
                bulk=False,
            )
