from django.contrib.auth.models import User
from django.contrib.gis.db import models
from django.conf import settings
from django.core.files.storage import get_storage_class
from django.core.urlresolvers import reverse
from . import cache
from . import utils


class TimeStampedModel (models.Model):
    created_datetime = models.DateTimeField(auto_now_add=True)
    updated_datetime = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class CacheClearingModel (object):
    def save(self, *args, **kwargs):
        result = super(CacheClearingModel, self).save(*args, **kwargs)

        if hasattr(self, 'cache'):
            self.cache.clear_instance(self)

        return result

    def delete(self, *args, **kwargs):
        if hasattr(self, 'cache'):
            self.cache.clear_instance(self)

        return super(CacheClearingModel, self).delete(*args, **kwargs)


class ModelWithDataBlob (models.Model):
    data = models.TextField(default='{}')

    class Meta:
        abstract = True


#class Submitter (CacheClearingModel, ModelWithDataBlob, TimeStampedModel):
#    account = models.ForeignKey('User', null=True, blank=True)
#
#    @property
#    def places(self):
#        return Place.objects.filter(submittedthing_ptr__submitter=self)
#
#    @property
#    def submissions(self):
#        return Sumbission.objects.filter(submittedthing_ptr__submitter=self)


class SubmittedThing (CacheClearingModel, ModelWithDataBlob, TimeStampedModel):
    """
    A SubmittedThing generally comes from the end-user.  It may be a place, a
    comment, a vote, etc.

    """
#    submitter = models.ForeignKey('Submitter', related_name='things')
    submitter_name = models.CharField(max_length=256, null=True, blank=True)
    dataset = models.ForeignKey('DataSet', related_name='submitted_thing_set',
                                blank=True)
    visible = models.BooleanField(default=True, blank=True)

    def save(self, silent=False, *args, **kwargs):
        is_new = (self.id == None)

        ret = super(SubmittedThing, self).save(*args, **kwargs)

        # All submitted things generate an action if not silent.
        if not silent:
            activity = Activity()
            activity.action = 'create' if is_new else 'update'
            activity.data = self
            activity.save()

        return ret


class DataSet (CacheClearingModel, models.Model):
    """
    A DataSet is a named collection of data, eg. Places, owned by a user,
    and intended for a coherent purpose, eg. display on a single map.
    """
    owner = models.ForeignKey(User, related_name='datasets')
    display_name = models.CharField(max_length=128)
    slug = models.SlugField(max_length=128, default=u'')

    cache = cache.DataSetCache()

    def __unicode__(self):
        return self.slug

    class Meta:
        unique_together = (('owner', 'slug'),
                           )


class Place (SubmittedThing):
    """
    A Place is a submitted thing with some geographic information, to which
    other submissions such as comments or surveys can be attached.

    """
    location = models.PointField()

    objects = models.GeoManager()
    cache = cache.PlaceCache()


class SubmissionSet (CacheClearingModel, models.Model):
    """
    A submission set is a collection of user Submissions attached to a place.
    For example, comments will be a submission set with a submission_type of
    'comment'.

    """
    place = models.ForeignKey(Place, related_name='submission_sets')
    submission_type = models.CharField(max_length=128)

    cache = cache.SubmissionSetCache()

    class Meta(object):
        unique_together = (('place', 'submission_type'),
                           )


class Submission (SubmittedThing):
    """
    A Submission is the simplest flavor of SubmittedThing.
    It belongs to a SubmissionSet, and thus indirectly to a Place.
    Used for representing eg. comments, votes, ...
    """
    parent = models.ForeignKey(SubmissionSet, related_name='children')

    cache = cache.SubmissionCache()


class Activity (CacheClearingModel, TimeStampedModel):
    """
    Metadata about SubmittedThings:
    what happened when.
    """
    action = models.CharField(max_length=16, default='create')
    data = models.ForeignKey(SubmittedThing)

    cache = cache.ActivityCache()

    @property
    def submitter_name(self):
        return self.data.submitter_name


def timestamp_filename(attachment, filename):
    # NOTE: It would be nice if this were a staticmethod in Attachment, but
    # Django 1.4 tries to convert the function to a string when we do that.
    return ''.join(['attachments/', utils.base62_time(), '-', filename])

AttachmentStorage = get_storage_class(settings.ATTACHMENT_STORAGE)


class Attachment (CacheClearingModel, TimeStampedModel):
    """
    A file attached to a submitted thing.
    """
    file = models.FileField(upload_to=timestamp_filename, storage=AttachmentStorage())
    name = models.CharField(max_length=128, null=True, blank=True)
    thing = models.ForeignKey('SubmittedThing', related_name='attachments')

    cache = cache.AttachmentCache()

#
