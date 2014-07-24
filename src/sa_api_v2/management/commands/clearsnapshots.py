from django.core.management.base import BaseCommand, CommandError
from django.utils.timezone import now, timedelta
from sa_api_v2.models import DataSnapshotRequest

import logging
log = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Clear any bulk data snapshots (and requests) older than a day.'

    def handle(self, *args, **options):
        log.info('Clearing bulk data snapshots older than a day')

        # Delete requests. Should cascade to snapshots.
        cutoff = now() - timedelta(days=1)
        DataSnapshotRequest.objects.filter(requested_at__lt=cutoff).delete()
