import ujson as json
from django.contrib.gis.db import models
from django.conf import settings
from django.core.files.storage import get_storage_class
from django.core.exceptions import ObjectDoesNotExist
from django.utils.timezone import now
from django.utils.importlib import import_module
from .. import cache
from .. import utils
from .data_indexes import IndexedValue
from .profiles import User
import sa_api_v1.models


class TimeStampedModel (models.Model):
    created_datetime = models.DateTimeField(default=now, blank=True, db_index=True)
    updated_datetime = models.DateTimeField(auto_now=True, db_index=True)

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

        try:
            previous_version = self.get_previous_version()
            if previous_version:
                previous_version.cache.clear_instance(previous_version)
        except ObjectDoesNotExist:
            pass

        try:
            next_version = self.get_next_version()
            if next_version:
                next_version.cache.clear_instance(next_version)
        except ObjectDoesNotExist:
            pass

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


class SubmittedThing (CacheClearingModel, ModelWithDataBlob, TimeStampedModel):
    """
    A SubmittedThing generally comes from the end-user.  It may be a place, a
    comment, a vote, etc.

    """
    submitter = models.ForeignKey(User, related_name='things', null=True, blank=True)
    dataset = models.ForeignKey('DataSet', related_name='things', blank=True)
    visible = models.BooleanField(default=True, blank=True, db_index=True)

    class Meta:
        app_label = 'sa_api_v2'
        db_table = 'sa_api_submittedthing'

    def index_values(self):
        indexes = self.dataset.indexes.all()

        if len(indexes) == 0:
            return

        data = json.loads(self.data)
        for index in indexes:
            IndexedValue.objects.sync(self, index, data=data)

    def save(self, silent=False, source='', reindex=True, *args, **kwargs):
        is_new = (self.id == None)

        ret = super(SubmittedThing, self).save(*args, **kwargs)

        if reindex:
            self.index_values()

        # All submitted things generate an action if not silent.
        if not silent:
            action = Action()
            action.action = 'create' if is_new else 'update'
            action.thing = self
            action.source = source
            action.save()

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
    previous_version = 'sa_api_v1.models.DataSet'

    def __unicode__(self):
        return self.slug

    class Meta:
        app_label = 'sa_api_v2'
        db_table = 'sa_api_dataset'
        unique_together = (('owner', 'slug'),
                           )

    @property
    def places(self):
        if not hasattr(self, '_places'):
            self._places = Place.objects.filter(dataset=self)
        return self._places

    @property
    def submissions(self):
        if not hasattr(self, '_submissions'):
            self._submissions = Submission.objects.filter(dataset=self)
        return self._submissions

    @utils.memo
    def get_permissions(self):
        return self.permissions


class Place (SubmittedThing):
    """
    A Place is a submitted thing with some geographic information, to which
    other submissions such as comments or surveys can be attached.

    """
    geometry = models.GeometryField()

    objects = models.GeoManager()
    cache = cache.PlaceCache()
    previous_version = 'sa_api_v1.models.Place'

    class Meta:
        app_label = 'sa_api_v2'
        db_table = 'sa_api_place'
        ordering = ['-updated_datetime']


class SubmissionSet (CacheClearingModel, models.Model):
    """
    A submission set is a collection of user Submissions attached to a place.
    For example, comments will be a submission set with a submission_type of
    'comment'.

    """
    place = models.ForeignKey(Place, related_name='submission_sets')
    name = models.CharField(max_length=128)

    cache = cache.SubmissionSetCache()
    previous_version = 'sa_api_v1.models.SubmissionSet'

    class Meta(object):
        app_label = 'sa_api_v2'
        db_table = 'sa_api_submissionset'
        unique_together = (('place', 'name'),
                           )


class Submission (SubmittedThing):
    """
    A Submission is the simplest flavor of SubmittedThing.
    It belongs to a SubmissionSet, and thus indirectly to a Place.
    Used for representing eg. comments, votes, ...
    """
    parent = models.ForeignKey(SubmissionSet, related_name='children')

    @property
    def place(self):
        return self.parent.place

    @property
    def place_id(self):
        return self.parent.place_id

    @property
    def set_name(self):
        return self.parent.name

    cache = cache.SubmissionCache()
    previous_version = 'sa_api_v1.models.Submission'

    class Meta:
        app_label = 'sa_api_v2'
        db_table = 'sa_api_submission'
        ordering = ['-updated_datetime']


class Action (CacheClearingModel, TimeStampedModel):
    """
    Metadata about SubmittedThings:
    what happened when.
    """
    action = models.CharField(max_length=16, default='create')
    thing = models.ForeignKey(SubmittedThing, db_column='data_id', related_name='actions')
    source = models.TextField(blank=True, null=True)

    cache = cache.ActionCache()
    previous_version = 'sa_api_v1.models.Activity'

    class Meta:
        app_label = 'sa_api_v2'
        db_table = 'sa_api_activity'
        ordering = ['-created_datetime']

    @property
    def submitter(self):
        return self.thing.submitter


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
    previous_version = 'sa_api_v1.models.Attachment'

    class Meta:
        app_label = 'sa_api_v2'
        db_table = 'sa_api_attachment'


#
