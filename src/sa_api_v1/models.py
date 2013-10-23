from django.contrib.auth.models import User
from django.contrib.gis.db import models
from django.conf import settings
from django.core.files.storage import get_storage_class
from django.core.urlresolvers import reverse
from django.utils.importlib import import_module
from . import cache
from . import utils
import ujson as json


class TimeStampedModel (models.Model):
    created_datetime = models.DateTimeField(auto_now_add=True)
    updated_datetime = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class CacheClearingModel (object):
    @classmethod
    def resolve_attr(cls, attr):
        if hasattr(cls, attr):
            value = getattr(cls, attr)
            if isinstance(value, str):
                module_name, class_name = value.rsplit('.', 1)
                value = getattr(import_module(module_name), class_name)
            return value
        else:
            return None

    def get_previous_version(self):
        model = self.resolve_attr('previous_version')
        if model:
            return model.objects.get(pk=self.pk)

    def get_next_version(self):
        model = self.resolve_attr('next_version')
        if model:
            return model.objects.get(pk=self.pk)

    def clear_instance_cache(self):
        if hasattr(self, 'cache'):
            self.cache.clear_instance(self)

        previous_version = self.get_previous_version()
        if previous_version:
            previous_version.cache.clear_instance(previous_version)

        next_version = self.get_next_version()
        if next_version:
            next_version.cache.clear_instance(next_version)

    def save(self, *args, **kwargs):
        result = super(CacheClearingModel, self).save(*args, **kwargs)
        self.clear_instance_cache()
        return result

    def delete(self, *args, **kwargs):
        self.clear_instance_cache()
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
    # submitter_name = models.CharField(max_length=256, null=True, blank=True)
    dataset = models.ForeignKey('DataSet', related_name='submitted_thing_set',
                                blank=True)
    visible = models.BooleanField(default=True, blank=True)

    class Meta:
        db_table = 'sa_api_submittedthing'
        managed = False

    @property
    def submitter_name(self):
        data = json.loads(self.data or '{}')
        return data.get('submitter_name')

    @submitter_name.setter
    def submitter_name(self, value):
        data = json.loads(self.data or '{}')
        data['submitter_name'] = value
        self.data = json.dumps(data)
        return value

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
    owner = models.ForeignKey(User, related_name='datasets_v1')
    display_name = models.CharField(max_length=128)
    slug = models.SlugField(max_length=128, default=u'')

    cache = cache.DataSetCache()
    next_version = 'sa_api_v2.models.DataSet'

    def __unicode__(self):
        return self.slug

    class Meta:
        db_table = 'sa_api_dataset'
        managed = False
        unique_together = (('owner', 'slug'),
                           )


class GeoPointManager (models.GeoManager):
    """
    A special GeoManager that only selects points.
    """
    def get_queryset(self, *args, **kwargs):
        # Compatibility with Django pre-1.5
        super_obj = super(GeoPointManager, self)
        if hasattr(super_obj, 'get_queryset'):
            super_func = super_obj.get_queryset
        else:
            super_func = super_obj.get_query_set

        qs = super_func(*args, **kwargs)
        qs = qs.extra(where=["ST_GeometryType(geometry) = 'ST_Point'"])
        return qs

    # Compatibility with Django pre-1.5
    get_query_set = get_queryset


class Place (SubmittedThing):
    """
    A Place is a submitted thing with some geographic information, to which
    other submissions such as comments or surveys can be attached.

    """
    location = models.PointField(db_column='geometry')

    objects = GeoPointManager()
    cache = cache.PlaceCache()
    next_version = 'sa_api_v2.models.Place'

    class Meta:
        db_table = 'sa_api_place'
        managed = False


class SubmissionSet (CacheClearingModel, models.Model):
    """
    A submission set is a collection of user Submissions attached to a place.
    For example, comments will be a submission set with a submission_type of
    'comment'.

    """
    place = models.ForeignKey(Place, related_name='submission_sets')
    submission_type = models.CharField(max_length=128, db_column='name')

    cache = cache.SubmissionSetCache()
    next_version = 'sa_api_v2.models.SubmissionSet'

    class Meta(object):
        db_table = 'sa_api_submissionset'
        managed = False
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
    next_version = 'sa_api_v2.models.Submission'

    class Meta:
        db_table = 'sa_api_submission'
        managed = False


class Activity (CacheClearingModel, TimeStampedModel):
    """
    Metadata about SubmittedThings:
    what happened when.
    """
    action = models.CharField(max_length=16, default='create')
    data = models.ForeignKey(SubmittedThing)

    cache = cache.ActivityCache()
    next_version = 'sa_api_v2.models.Action'

    @property
    def submitter_name(self):
        return self.data.submitter_name

    class Meta:
        managed = False
        db_table = 'sa_api_activity'


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
    next_version = 'sa_api_v2.models.Attachment'

    class Meta:
        managed = False
        db_table = 'sa_api_attachment'

#
