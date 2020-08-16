import ujson as json
from django.conf import settings
from django.db.models import query

if settings.USE_GEODB:
    from django.contrib.gis.db import models
else:
    from django.db import models

from django.core.files.storage import get_storage_class
from django.db.models.signals import post_save
from django.utils.timezone import now
from .. import cache
from .. import utils
from .caching import CacheClearingModel
from .data_indexes import IndexedValue, FilterByIndexMixin
from .mixins import CloneableModelMixin
from .profiles import User
from PIL import Image, UnidentifiedImageError


class TimeStampedModel (models.Model):
    created_datetime = models.DateTimeField(default=now, blank=True, db_index=True)
    updated_datetime = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        abstract = True


class ModelWithDataBlob (models.Model):
    data = models.TextField(default='{}')

    class Meta:
        abstract = True


class SubmittedThingQuerySet (FilterByIndexMixin, query.QuerySet):
    pass


class SubmittedThingManager (FilterByIndexMixin, models.Manager):
    use_for_related_fields = True

    def create(self, silent=False, source='', reindex=True, *args, **kwargs):
        """
        Creates a new object with the given kwargs, saving it to the database
        and returning the created object.
        """
        obj = self.model(**kwargs)
        self._for_write = True
        obj.save(silent=silent, source=source, reindex=reindex, force_insert=True, using=self.db)
        return obj

    def get_queryset(self):
        return SubmittedThingQuerySet(self.model, using=self._db)


class SubmittedThing (CloneableModelMixin, CacheClearingModel, ModelWithDataBlob, TimeStampedModel):
    """
    A SubmittedThing generally comes from the end-user.  It may be a place, a
    comment, a vote, etc.

    """
    submitter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='things', null=True, blank=True)
    dataset = models.ForeignKey('DataSet', on_delete=models.CASCADE, related_name='things', blank=True)
    visible = models.BooleanField(default=True, blank=True, db_index=True)

    objects = SubmittedThingManager()

    class Meta:
        app_label = 'sa_api_v2'
        db_table = 'sa_api_submittedthing'

    def index_values(self, indexes=None):
        if indexes is None:
            indexes = self.dataset.indexes.all()

        if len(indexes) == 0:
            return

        data = json.loads(self.data)
        for index in indexes:
            IndexedValue.objects.sync(self, index, data=data)

    def get_clone_save_kwargs(self):
        return {'silent': True, 'reindex': False, 'clear_cache': False}

    def emit_action(self, source='', is_new=None):
        action = Action()
        action.action = 'create' if is_new else 'update'
        action.thing = self
        action.source = source
        action.save()

        return self

    def save(self, silent=False, source='', reindex=True, *args, **kwargs):
        is_new = (self.id == None)

        ret = super(SubmittedThing, self).save(*args, **kwargs)

        if reindex:
            self.index_values()

        # All submitted things generate an action if not silent.
        if not (silent or getattr(self, 'silent', False)):
            self.emit_action(is_new=is_new, source=source)

        return ret


class DataSet (CloneableModelMixin, CacheClearingModel, models.Model):
    """
    A DataSet is a named collection of data, eg. Places, owned by a user,
    and intended for a coherent purpose, eg. display on a single map.
    """
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='datasets')
    display_name = models.CharField(max_length=128)
    slug = models.SlugField(max_length=128, default='')

    cache = cache.DataSetCache()
    # previous_version = 'sa_api_v1.models.DataSet'

    def __str__(self):
        return self.__unicode__()

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
    def get_key(self, key_string):
        for ds_key in self.keys.all():
            if ds_key.key == key_string:
                return ds_key
        return None

    @utils.memo
    def get_origin(self, origin_header):
        for ds_origin in self.origins.all():
            if ds_origin.match(ds_origin.pattern, origin_header):
                return ds_origin
        return None

    def reindex(self):
        things = self.things.all()
        indexes = self.indexes.all()

        for thing in things:
            thing.index_values(indexes)

    def clone_related(self, onto):
        # Clone all the places. Submissions will be cloned as part of the
        # places.
        for thing in self.things.all():
            try: place = thing.full_place
            except Place.DoesNotExist: continue
            if place:
                place.clone(overrides={'dataset': onto})

        for group in self.groups.all():
            group.clone(overrides={'dataset': onto})

        for index in self.indexes.all():
            index.clone(overrides={'dataset': onto})

        for permission in self.permissions.all():
            permission.clone(overrides={'dataset': onto})

        for origin in self.origins.all():
            origin.clone(overrides={'dataset': onto})

        for key in self.keys.all():
            key.clone(overrides={'dataset': onto})

        self.reindex()


class Webhook (TimeStampedModel):
    """
    A Webhook is a user-defined HTTP callback for POSTing place or submitted
    thing as JSON to a specified URL after a specified event.

    """
    EVENT_CHOICES = (
        ('add', 'On add'),
    )

    dataset = models.ForeignKey('DataSet', on_delete=models.CASCADE, related_name='webhooks')
    submission_set = models.CharField(max_length=128)
    event = models.CharField(max_length=128, choices=EVENT_CHOICES, default='add')
    url = models.URLField(max_length=2048)

    class Meta:
        app_label = 'sa_api_v2'
        db_table = 'sa_api_webhook'

    def __str__(self):
        return 'On %s data in %s' % (self.event, self.submission_set)




class Place (SubmittedThing):
    """
    A Place is a submitted thing with some geographic information, to which
    other submissions such as comments or surveys can be attached.

    """
    submittedthing_ptr = models.OneToOneField('SubmittedThing', parent_link=True, on_delete=models.CASCADE, related_name='full_place')

    if settings.USE_GEODB:
        geometry = models.GeometryField()
    else:
        geometry = models.TextField()

    objects = SubmittedThingManager()
    cache = cache.PlaceCache()
    # previous_version = 'sa_api_v1.models.Place'

    class Meta:
        app_label = 'sa_api_v2'
        db_table = 'sa_api_place'
        ordering = ['-updated_datetime']

    def clone_related(self, onto):
        data_overrides = {'place': onto, 'dataset': onto.dataset}
        for submission in self.submissions.all():
            submission.clone(overrides=data_overrides)

    def __str__(self):
        return str(self.id)


class Submission (SubmittedThing):
    """
    A Submission is the simplest flavor of SubmittedThing.
    It belongs to a Place.
    Used for representing eg. comments, votes, ...
    """
    submittedthing_ptr = models.OneToOneField('SubmittedThing', parent_link=True, on_delete=models.CASCADE, related_name='full_submission')
    place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name='submissions')
    set_name = models.TextField(db_index=True)

    objects = SubmittedThingManager()
    cache = cache.SubmissionCache()
    # previous_version = 'sa_api_v1.models.Submission'

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
    thing = models.ForeignKey(SubmittedThing, on_delete=models.CASCADE, db_column='data_id', related_name='actions')
    source = models.TextField(blank=True, null=True)

    cache = cache.ActionCache()
    # previous_version = 'sa_api_v1.models.Activity'

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
    thing = models.ForeignKey('SubmittedThing', on_delete=models.CASCADE, related_name='attachments')
    height = models.IntegerField(blank=True, null=True)
    width = models.IntegerField(blank=True, null=True)

    cache = cache.AttachmentCache()
    # previous_version = 'sa_api_v1.models.Attachment'

    def apply_image_dimensions(self):
        """
        Returns True if the image could be opened and the size extracted.
        Otherwise returns False.
        """
        try:
            image = Image.open(self.file)
            self.width, self.height = image.size
            return True
        except (ValueError, EOFError, UnidentifiedImageError) as e:
            return False

    def save(self, *args, **kwargs):
        if self.width is None or self.height is None:
            self.apply_image_dimensions()
        super(Attachment, self).save(*args, **kwargs)


    class Meta:
        app_label = 'sa_api_v2'
        db_table = 'sa_api_attachment'


#
