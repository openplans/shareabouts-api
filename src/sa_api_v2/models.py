from django.contrib.auth.models import User
from django.contrib.gis.db import models
from django.conf import settings
from django.core.files.storage import get_storage_class
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.signals import post_save
from django.utils.timezone import now
from django.utils.importlib import import_module
from . import cache
from . import utils
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
    submitter = models.ForeignKey(User, related_name='things', null=True, blank=True)
    dataset = models.ForeignKey('DataSet', related_name='things', blank=True)
    visible = models.BooleanField(default=True, blank=True, db_index=True)

    class Meta:
        db_table = 'sa_api_submittedthing'

    def save(self, silent=False, source='', *args, **kwargs):
        is_new = (self.id == None)

        ret = super(SubmittedThing, self).save(*args, **kwargs)

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
        db_table = 'sa_api_attachment'


class Group (models.Model):
    """
    A group of submitters within a dataset.
    """
    dataset = models.ForeignKey('DataSet', help_text='Which dataset does this group apply to?')
    name = models.CharField(max_length=32, help_text='What is the name of the group to which users with this group belong? For example: "judges", "administrators", "winners", ...')
    submitters = models.ManyToManyField(User, related_name='_groups', blank=True)

    class Meta:
        db_table = 'sa_api_group'
        unique_together = [('name', 'dataset')]

    def __unicode__(self):
        return '%s in %s' % (self.name, self.dataset.slug)


class DataPermission (models.Model):
    """
    Rules for what permissions a given authentication method affords.
    """
    submission_set = models.CharField(max_length=128, blank=True, help_text='Either the name of a submission set (e.g., "comments"), or "places". Leave blank to refer to all things.')
    can_retrieve = models.BooleanField(default=True)
    can_create = models.BooleanField(default=False)
    can_update = models.BooleanField(default=False)
    can_destroy = models.BooleanField(default=False)
    priority = models.PositiveIntegerField(blank=True)

    class Meta:
        abstract = True
        ordering = ('priority',)

    def abilities(self):
        abilities = []
        if self.can_create: abilities.append('create')
        if self.can_retrieve: abilities.append('retrieve')
        if self.can_update: abilities.append('update')
        if self.can_destroy: abilities.append('destroy')

        if abilities:
            if len(abilities) > 1: abilities[-1] = 'or ' + abilities[-1]
            return 'can ' + ', '.join(abilities) + ' ' + (self.submission_set or 'anything')
        else:
            return 'can not create, retrieve, update, or destroy ' + (self.submission_set or 'anything') + ' at all'

    def save(self, *args, **kwargs):
        # Use self.__class__ so that inherited models work.
        ModelClass = self.__class__

        if self.priority is None:
            try:
                lowest = ModelClass.objects.order_by('-priority')[0]
                self.priority = lowest.priority + 1
            except IndexError:
                self.priority = 0

        return super(DataPermission, self).save(*args, **kwargs)


class DataSetPermission (DataPermission):
    dataset = models.ForeignKey('DataSet', related_name='permissions')

    def __unicode__(self):
        return '%s %s' % ('submitters', self.abilities())


class GroupPermission (DataPermission):
    group = models.ForeignKey('Group', related_name='permissions')

    def __unicode__(self):
        return '%s %s' % (self.group, self.abilities())


class KeyPermission (DataPermission):
    key = models.ForeignKey('apikey.ApiKey', related_name='permissions')

    def __unicode__(self):
        return 'submitters %s' % (self.abilities(),)


class OriginPermission (DataPermission):
    origin = models.ForeignKey('cors.Origin', related_name='permissions')

    def __unicode__(self):
        return 'submitters %s' % (self.abilities(),)


def create_data_permissions(sender, instance, created, **kwargs):
    """
    Create a default permission instance for a new dataset.
    """
    if created:
        DataSetPermission.objects.create(dataset=instance, submission_set='*',
            can_retrieve=True, can_create=False, can_update=False, can_destroy=False)
post_save.connect(create_data_permissions, sender=DataSet, dispatch_uid="dataset-create-permissions")


def check_data_permission(user, client, do_action, dataset, submission_set):
    """
    Check whether the given user has permission on the submission_set in
    the context of the given client (e.g., an API key or an origin).
    """
    if do_action not in ('retrieve', 'create', 'update', 'delete'):
        raise ValueError

    if isinstance(submission_set, SubmissionSet):
        submission_set = submission_set.name

    # Start with the dataset permission
    for permission in dataset.permissions.all():
        if (permission.submission_set in (submission_set, '*')
            and getattr(permission, 'can_' + do_action, False)):
            return True

    # Then the client permission
    if client is not None:
        for permission in client.permissions.all():
            if (client.dataset == dataset
                and permission.submission_set in (submission_set, '*')
                and getattr(permission, 'can_' + do_action, False)):
                return True

    # Next, check the user's groups
    if user is not None:
        for group in user._groups.all():
            if group.dataset != dataset:
                continue

            for permission in group.permissions.all():
                if (permission.submission_set in (submission_set, '*')
                    and getattr(permission, 'can_' + do_action)):
                    return True

    return False

#
