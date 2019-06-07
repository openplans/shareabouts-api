import time
import uuid
from django.db import models


class DataSnapshotRequest (models.Model):
    # Describe the data requested
    dataset = models.ForeignKey('DataSet', on_delete=models.CASCADE)
    submission_set = models.CharField(max_length=128)
    include_private = models.BooleanField(default=False)
    include_invisible = models.BooleanField(default=False)
    include_submissions = models.BooleanField(default=False)
    # Describe the requester
    requester = models.ForeignKey('User', null=True, on_delete=models.CASCADE)
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
    request = models.OneToOneField('DataSnapshotRequest', related_name='fulfillment', on_delete=models.CASCADE)
    json = models.TextField()
    csv = models.TextField()

    @property
    def geojson(self):
        return self.json

    @geojson.setter
    def geojson(self, value):
        self.json = value

    class Meta:
        app_label = 'sa_api_v2'
        db_table = 'sa_api_datasnapshot'
