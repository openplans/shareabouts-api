from django.contrib.auth import models as auth_models
from django.contrib.gis.db import models
from django.core.cache import cache
from django.core.urlresolvers import reverse


class TimeStampedModel (models.Model):
    created_datetime = models.DateTimeField(auto_now_add=True)
    updated_datetime = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class CacheClearingModel (object):
    def clear_keys_with_prefix(self, prefix):
        self.clear_keys_with_prefixes(prefix)

    def clear_keys_with_prefixes(self, *prefixes):
        keys = set()
        for prefix in prefixes:
            keys |= cache.get(prefix + '_keys') or set()
            keys.add(prefix + '_keys')
        cache.delete_many(keys)


class SubmittedThing (CacheClearingModel, TimeStampedModel):
    """
    A SubmittedThing generally comes from the end-user.  It may be a place, a
    comment, a vote, etc.

    """
    submitter_name = models.CharField(max_length=256, null=True, blank=True)
    data = models.TextField(default='{}')
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
    owner = models.ForeignKey(auth_models.User)
    display_name = models.CharField(max_length=128)
    slug = models.SlugField(max_length=128, default=u'')

    def __unicode__(self):
        return self.slug

    class Meta:
        unique_together = (('owner', 'slug'),
                           )
    
    def save(self, *args, **kwargs):
        result = super(DataSet, self).save(*args, **kwargs)
        
        # Collect information for cache keys
        owner = self.owner.username
        slug = self.slug
        
        instance_path = reverse('dataset_instance_by_user', args=[owner, slug])
        collection_path = reverse('dataset_collection_by_user', args=[owner])
        
        self.clear_keys_with_prefixes(instance_path, collection_path)
        
        return result


class Place (SubmittedThing):
    """
    A Place is a submitted thing with some geographic information, to which
    other submissions such as comments or surveys can be attached.

    """
    location = models.PointField()

    objects = models.GeoManager()

    def save(self, *args, **kwargs):
        result = super(Place, self).save(*args, **kwargs)
        
        # Collect information for cache keys
        owner = self.dataset.owner.username
        dataset = self.dataset.slug
        pk = self.pk
        
        instance_path = reverse('place_instance_by_dataset', args=[owner, dataset, pk])
        collection_path = reverse('place_collection_by_dataset', args=[owner, dataset])
        activity_path = reverse('activity_collection_by_dataset', args=[owner, dataset])
        self.clear_keys_with_prefixes(instance_path, collection_path, activity_path)
        
        return result


class SubmissionSet (CacheClearingModel, models.Model):
    """
    A submission set is a collection of user Submissions attached to a place.
    For example, comments will be a submission set with a submission_type of
    'comment'.

    """
    place = models.ForeignKey(Place, related_name='submission_sets')
    submission_type = models.CharField(max_length=128)

    class Meta(object):
        unique_together = (('place', 'submission_type'),
                           )

    def save(self, *args, **kwargs):
        result = super(SubmissionSet, self).save(*args, **kwargs)
        
        # Collect information for cache keys
        owner = self.place.dataset.owner.username
        dataset = self.place.dataset.slug
        pk = self.place.pk
        
        instance_path = reverse('place_instance_by_dataset', args=[owner, dataset, pk])
        collection_path = reverse('place_collection_by_dataset', args=[owner, dataset])
        activity_path = reverse('activity_collection_by_dataset', args=[owner, dataset])
        self.clear_keys_with_prefixes(instance_path, collection_path, activity_path)
        
        return result


class Submission (SubmittedThing):
    """
    A Submission is the simplest flavor of SubmittedThing.
    It belongs to a SubmissionSet, and thus indirectly to a Place.
    Used for representing eg. comments, votes, ...
    """
    parent = models.ForeignKey(SubmissionSet, related_name='children')

    def save(self, *args, **kwargs):
        result = super(Submission, self).save(*args, **kwargs)
        
        # Collect information for cache keys
        owner = self.dataset.owner.username
        dataset = self.dataset.slug
        place_id = self.parent.place.id
        type = self.parent.submission_type
        id = self.pk
        
        # Clear related cache values
        specific_instance_path = reverse('submission_instance_by_dataset', args=[owner, dataset, place_id, type, id])
        general_instance_path = reverse('submission_instance_by_dataset', args=[owner, dataset, place_id, 'submissions', id])
        specific_collection_path = reverse('submission_collection_by_dataset', args=[owner, dataset, place_id, type])
        general_collection_path = reverse('submission_collection_by_dataset', args=[owner, dataset, place_id, 'submissions'])
        specific_all_path = reverse('all_submissions_by_dataset', args=[owner, dataset, type])
        general_all_path = reverse('all_submissions_by_dataset', args=[owner, dataset, 'submissions'])
        activity_path = reverse('activity_collection_by_dataset', args=[owner, dataset])
        
        self.clear_keys_with_prefixes(
            specific_instance_path, general_instance_path,
            specific_collection_path, general_collection_path,
            specific_all_path, general_all_path,
            activity_path)
        
        return result


class Activity (TimeStampedModel):
    """
    Metadata about SubmittedThings:
    what happened when.
    """
    action = models.CharField(max_length=16, default='create')
    data = models.ForeignKey(SubmittedThing)

    def save(self, *args, **kwargs):
        keys = cache.get('activity_keys') or set()
        keys.add('activity_keys')
        cache.delete_many(keys)

        return super(Activity, self).save(*args, **kwargs)

    @property
    def submitter_name(self):
        return self.data.submitter_name
