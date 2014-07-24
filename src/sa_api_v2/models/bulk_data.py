import time
import uuid
from django.contrib.gis.db import models


class DataSnapshotRequest (models.Model):
    FORMAT_CHOICES = (
        ('json', 'JSON/GeoJSON'),
        ('csv', 'CSV'),
    )

    # Describe the data requested
    dataset = models.ForeignKey('DataSet')
    submission_set = models.CharField(max_length=128)
    format = models.CharField(max_length=16, choices=FORMAT_CHOICES)
    include_private = models.BooleanField()
    include_invisible = models.BooleanField()
    include_submissions = models.BooleanField()
    # Describe the requester
    requester = models.ForeignKey('User', null=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    # Describe the fulfillment status
    status = models.TextField(default='', blank=True)
    fulfilled_at = models.DateTimeField(null=True)
    guid = models.TextField(unique=True, default='', blank=True)

    class Meta:
        app_label = 'sa_api_v2'
        db_table = 'sa_api_datasnapshotrequest'

    def __unicode__(self):
        return 'Bulk request for %s %s' % (self.dataset, self.submission_set)

    @staticmethod
    def get_current_time_bucket():
        timestamp = time.time()
        return timestamp - (timestamp % 60)  # Each minute


class DataSnapshot (models.Model):
    request = models.OneToOneField('DataSnapshotRequest', related_name='fulfillment')
    content = models.TextField()

    class Meta:
        app_label = 'sa_api_v2'
        db_table = 'sa_api_datasnapshot'
