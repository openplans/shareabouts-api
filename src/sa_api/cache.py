from collections import defaultdict
from django.core.cache import cache
from django.core.urlresolvers import reverse
from . import utils

import logging
logger = logging.getLogger('sa_api.cache')

class Cache (object):
    def get_meta_key(self, prefix):
        return prefix + '_keys'

    def get_keys_with_prefixes(self, *prefixes):
        keys = set()
        for prefix in prefixes:
            meta_key = self.get_meta_key(prefix)
            keys |= cache.get(meta_key) or set()
            keys.add(meta_key)
        logger.debug('Keys with prefixes "%s": "%s"' % ('", "'.join(prefixes), '", "'.join(keys)))
        return keys

    def clear_keys(self, *keys):
        logger.debug('Deleting: "%s"' % '", "'.join(keys))
        cache.delete_many(keys)

    def get_instance_params_key(self, inst_key):
        from django.db.models import Model
        if isinstance(inst_key, Model):
            obj = inst_key
            inst_key = obj.pk
        return '%s:%s' % (self.__class__.__name__, inst_key)

    def clear_instance_params(self, obj):
        instance_params_key = self.get_instance_params_key(obj)
        logger.debug('Deleting: "%s"' % instance_params_key)
        cache.delete(instance_params_key)

    def get_cached_instance_params(self, inst_key, obj_getter):
        """
        Get the instance parameters cached for the given instance key. If no
        params are cached, run the obj_getter to get the actual instance and
        calculate the parameters based on that object. The getter is a function
        so that it does not get evaluated if it doesn't have to be.
        """
        instance_params_key = self.get_instance_params_key(inst_key)
        params = cache.get(instance_params_key)

        if params is None:
            obj = obj_getter()
            params = self.get_instance_params(obj)
            logger.debug('Setting instance parameters for "%s": %r' % (instance_params_key, params))
            cache.set(instance_params_key, params)
        else:
            logger.debug('Found instance parameters for "%s": %r' % (instance_params_key, params))
        return params

    def get_other_keys(self, **params):
        return set()

    def clear_instance(self, obj):
        # Collect information for cache keys
        params = self.get_cached_instance_params(obj.pk, lambda: obj)
        # Collect the prefixes for cached requests
        prefixes = self.get_request_prefixes(**params)
        prefixed_keys = self.get_keys_with_prefixes(*prefixes)
        # Collect other related keys
        other_keys = self.get_other_keys(**params) | set([self.get_instance_params_key(obj.pk)])
        # Clear all the keys
        self.clear_keys(*(prefixed_keys | other_keys))


class DataSetCache (Cache):
    def get_instance_params(self, dataset_obj):
        params = {
            'owner': dataset_obj.owner.username,
            'owner_id': dataset_obj.owner.pk,
            'dataset': dataset_obj.slug,
            'dataset_id': dataset_obj.pk,
        }
        return params

    def get_request_prefixes(self, **params):
        owner, dataset = map(params.get, ('owner', 'dataset'))
        instance_path = reverse('dataset_instance_by_user', args=[owner, dataset])
        collection_path = reverse('dataset_collection_by_user', args=[owner])
        return (instance_path, collection_path)

    def get_submission_sets_key(self, owner_id):
        return '%s:%s:%s' % (self.__class__.__name__, owner_id, 'submission_sets')


class ThingWithAttachmentCache (Cache):
    dataset_cache = DataSetCache()

    def get_instance_params(self, thing_obj):
        params = self.dataset_cache.get_cached_instance_params(
            thing_obj.dataset_id, lambda: thing_obj.dataset)
        params.update({
            'thing': thing_obj.pk
        })
        return params

    def get_attachments_key(self, dataset_id):
        return 'dataset:%s:%s' % (dataset_id, 'attachments-by-thing_id')

    def calculate_attachments(self, dataset_id):
        """
        Cache all the attachments for all the places in the given dataset. Helps
        to cut down on database hits when doing operations on several places.
        """
        # Import Attachment here to avoid circular dependencies.
        from .models import Attachment

        attachments = defaultdict(list)

        qs = Attachment.objects.filter(thing__dataset_id=dataset_id)
#        qs = qs.values('file', 'name', 'thing_id')
        # NOTE: To build the back-reference URL, I'd need information about
        # the thing's dataset (like thing__dataset__owner__username and such),
        # but I'd also need to know whether the thing is a place or a
        # submission.  I'd rather avoid that right now.

        for attachment in qs:
            attachments[attachment.thing.pk].append({
                'name': attachment.name,
                'url': attachment.file.url,
                'created_datetime': attachment.created_datetime,
                'updated_datetime': attachment.updated_datetime,
            })

        return attachments

    def get_attachments(self, dataset_id):
        """
        A mapping from Place id to attachments. This is so that when we request
        all the places in a dataset, we don't end up doing a query for the
        attachments on each place; we can just do it once.
        """
        attachments_key = self.get_attachments_key(dataset_id)
        attachments = cache.get(attachments_key)
        if attachments is None:
            attachments = self.calculate_attachments(dataset_id)
            cache.set(attachments_key, attachments)
        return attachments


class PlaceCache (ThingWithAttachmentCache, Cache):
    dataset_cache = DataSetCache()

    def get_instance_params(self, place_obj):
        params = self.dataset_cache.get_cached_instance_params(
            place_obj.dataset_id, lambda: place_obj.dataset)
        params.update({
            'place': place_obj.pk
        })
        return params

    def get_request_prefixes(self, **params):
        owner, dataset, place = map(params.get, ('owner', 'dataset', 'place'))
        instance_path = reverse('place_instance_by_dataset', args=[owner, dataset, place])
        collection_path = reverse('place_collection_by_dataset', args=[owner, dataset])
        activity_path = reverse('activity_collection_by_dataset', args=[owner, dataset])
        return (instance_path, collection_path, activity_path)

    def get_submission_sets_key(self, dataset_id):
        return '%s:%s:%s' % (self.__class__.__name__, dataset_id, 'submission_sets')

    def calculate_submission_sets(self, dataset_id):
        """
        Cache all the submission set metadata for all the places in the given
        dataset. Helps to cut down on database hits when doing operations on
        several places.

        Because of this, it's more efficient to modify many places in a batch,
        as opposed to doing a few places, then a few submissions, etc.
        """
        # Import SubmissionSet here to avoid circular dependencies.
        from django.db.models import Count
        from .models import SubmissionSet

        submission_sets = defaultdict(list)

        qs = SubmissionSet.objects.filter(place__dataset_id=dataset_id)
        qs = qs.annotate(length=Count('children'))
        qs = qs.values('submission_type', 'length',
                       'place__dataset__owner__username',
                       'place__dataset__slug', 'place_id')

        for submission_set in qs:
            set_name, length, owner, dataset, place = \
                map(submission_set.get, ['submission_type', 'length',
                       'place__dataset__owner__username',
                       'place__dataset__slug', 'place_id'])

            # Ignore empty sets
            if length <= 0:
                continue

            submission_sets[place].append({
                'type': set_name,
                'length': length,
                'url': reverse('submission_collection_by_dataset', kwargs={
                    'dataset__owner__username': owner,
                    'dataset__slug': dataset,
                    'place_id': place,
                    'submission_type': set_name
                })
            })

        return submission_sets

    def get_submission_sets(self, dataset_id):
        """
        A mapping from Place ids to attributes.  Helps to cut down
        significantly on the number of queries.

        There should be at most one SubmissionSet of a given type for one place.
        """
        submission_sets_key = self.get_submission_sets_key(dataset_id)
        submission_sets = cache.get(submission_sets_key)
        if submission_sets is None:
            submission_sets = self.calculate_submission_sets(dataset_id)
            cache.set(submission_sets_key, submission_sets)
        return submission_sets


class SubmissionSetCache (Cache):
    place_cache = PlaceCache()

    # NOTE: A SubmissionSet doesn't live on its own, only on a place. So,
    # invalidating a SubmissionSet should invalidate its place.
    def get_instance_params(self, submissionset_obj):
        params = self.place_cache.get_cached_instance_params(
            submissionset_obj.place_id, lambda: submissionset_obj.place)
        params.update({
            'set_name': submissionset_obj.submission_type
        })
        return params

    def get_request_prefixes(self, **params):
        owner, dataset, place = map(params.get, ['owner', 'dataset', 'place'])
        instance_path = reverse('place_instance_by_dataset', args=[owner, dataset, place])
        collection_path = reverse('place_collection_by_dataset', args=[owner, dataset])
        dataset_path = reverse('dataset_instance_by_user', args=[owner, dataset])
        activity_path = reverse('activity_collection_by_dataset', args=[owner, dataset])
        return (instance_path, collection_path, dataset_path, activity_path)


class SubmissionCache (ThingWithAttachmentCache, Cache):
    dataset_cache = DataSetCache()
    place_cache = PlaceCache()
    submissionset_cache = SubmissionSetCache()

    def get_instance_params(self, submission_obj):
        params = self.submissionset_cache.get_cached_instance_params(
            submission_obj.parent_id, lambda: submission_obj.parent)
        params.update({
            'submission': submission_obj.pk
        })
        return params

    def get_other_keys(self, **params):
        owner_id, dataset_id = map(params.get, ['owner_id', 'dataset_id'])
        dataset_submission_sets_key = self.dataset_cache.get_submission_sets_key(owner_id)
        place_submission_sets_key = self.place_cache.get_submission_sets_key(dataset_id)
        return set([dataset_submission_sets_key, place_submission_sets_key])

    def get_request_prefixes(self, **params):
        owner, dataset, place, set_name, submission = map(params.get, ['owner', 'dataset', 'place', 'set_name', 'submission'])
        specific_instance_path = reverse('submission_instance_by_dataset', args=[owner, dataset, place, set_name, submission])
        general_instance_path = reverse('submission_instance_by_dataset', args=[owner, dataset, place, 'submissions', submission])
        specific_collection_path = reverse('submission_collection_by_dataset', args=[owner, dataset, place, set_name])
        general_collection_path = reverse('submission_collection_by_dataset', args=[owner, dataset, place, 'submissions'])
        specific_all_path = reverse('all_submissions_by_dataset', args=[owner, dataset, set_name])
        general_all_path = reverse('all_submissions_by_dataset', args=[owner, dataset, 'submissions'])
        dataset_path = reverse('dataset_instance_by_user', args=[owner, dataset])
        activity_path = reverse('activity_collection_by_dataset', args=[owner, dataset])

        return (specific_instance_path, general_instance_path,
                specific_collection_path, general_collection_path,
                specific_all_path, general_all_path, dataset_path,
                activity_path)


class ActivityCache (Cache):
    def clear_instance(self, obj):
        keys = cache.get('activity_keys') or set()
        keys.add('activity_keys')
        cache.delete_many(keys)


class AttachmentCache (Cache):
    thing_cache = ThingWithAttachmentCache()

    def get_instance_params(self, attachment_obj):
        params = self.thing_cache.get_cached_instance_params(
            attachment_obj.thing_id, lambda: attachment_obj.thing)
        params.update({
            'attachment': attachment_obj.name,
            'attachment_id': attachment_obj.pk,
        })
        return params

    def get_request_prefixes(self, **params):
        return set()

    def get_other_keys(self, **params):
        dataset_id = params.get('dataset_id')
        thing_attachments_key = self.thing_cache.get_attachments_key(dataset_id)
        return set([thing_attachments_key])
