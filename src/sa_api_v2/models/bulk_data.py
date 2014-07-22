from django.contrib.gis.db import models


class BulkDataRequest (models.Model):
    # Describe the data requested
    dataset = models.ForeignKey('DataSet')
    submission_set = models.CharField(max_length=128)
    format = models.CharField(max_length=16)
    include_private = models.BooleanField()
    include_invisible = models.BooleanField()
    include_submissions = models.BooleanField()
    # Describe the requester
    requester = models.ForeignKey('User', null=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    # Describe the fulfillment
    fulfilled_at = models.DateTimeField(null=True)

    class Meta:
        app_label = 'sa_api_v2'
        db_table = 'sa_api_bulkdatarequest'

    def __unicode__(self):
        return 'Bulk request for %s %s' % (self.dataset, self.submission_set)


class BulkData (models.Model):
    request = models.OneToOneField('BulkDataRequest', related_name='fulfillment', null=True)
    content = models.TextField()

    class Meta:
        app_label = 'sa_api_v2'
        db_table = 'sa_api_bulkdata'
