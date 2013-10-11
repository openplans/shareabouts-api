from collections import defaultdict
from django.conf import settings
from django.core.cache import cache
from django.core.urlresolvers import reverse
from . import utils

import logging
logger = logging.getLogger('sa_api_v2.cache')


class Cache (object):
    """
    The base class for objects responsible for caching Shareabouts data
    structure information

    """

    def get_meta_key(self, prefix):
        """
        Data identified by a number of keys may be cached for any given object.
        A meta-key keeps track of a set of related keys, for the purposes of
        invalidating all of those keys at once when the associated object is
        updated.

        For example, data associated with a particular dataset with a primary
        key of 23 might have cache keys that all begin with the prefix
        "datasets:23". The cache keys themselves would be stored in a list
        identified by the meta-key "dataset:23_keys".
        """
        return prefix + '_keys'

    def get_request_prefixes(self, **params):
        # Override in derived classes
        return set()

    def get_keys_with_prefixes(self, *prefixes):
        """
        Return a set of keys that begin with the given prefixes, including
        meta-keys.
        """
        keys = set()
        for prefix in prefixes:
            meta_key = self.get_meta_key(prefix)
            keys |= cache.get(meta_key) or set()
            keys.add(meta_key)
        logger.debug('Keys with prefixes "%s": "%s"' % ('", "'.join(prefixes), '", "'.join(keys)))
        return keys

    def clear_keys(self, *keys):
        """
        Delete all of the data from the cache identified by the given keys.
        """
        logger.debug('Deleting: "%s"' % '", "'.join(keys))
        cache.delete_many(keys)

    def get_instance_params_key(self, inst_key):
        """
        Keys related to an instance can be reconstructed without having to
        query the database for the instance by using characteristic parameters
        related to the instance. Those parameters themselves are cached with
        this key.
        """
        from django.db.models import Model
        if isinstance(inst_key, Model):
            obj = inst_key
            inst_key = obj.pk
        return '%s:%s' % (self.__class__.__name__, inst_key)

    def clear_instance_params(self, obj):
        """
        Clear the instance parameters. Useful for when we delete a particular
        instance, or when the identifying information for the instance changes
        which, for well-chosen characteristic parameters, should never happen.
        """
        instance_params_key = self.get_instance_params_key(obj)
        logger.debug('Deleting: "%s"' % instance_params_key)
        cache.delete(instance_params_key)

    def get_cached_instance_params(self, inst_key, obj_getter):
        """
        Get the instance parameters cached for the given instance key. If no
        params are cached, run the obj_getter to get the actual instance and
        calculate the parameters based on that object. The getter is a function
        so that it does not get evaluated if it doesn't have to be, since
        evaluating it may involve additional queries.
        """
        instance_params_key = self.get_instance_params_key(inst_key)
        params = cache.get(instance_params_key)

        if params is None:
            obj = obj_getter()
            params = self.get_instance_params(obj)
            logger.debug('Setting instance parameters for "%s": %r' % (instance_params_key, params))
            cache.set(instance_params_key, params, settings.API_CACHE_TIMEOUT)
        else:
            logger.debug('Found instance parameters for "%s": %r' % (instance_params_key, params))
        return params

    def get_serialized_data_meta_key(self, inst_key):
        inst_params_key = self.get_instance_params_key(inst_key)
        return inst_params_key + ':_keys'

    def get_serialized_data_key(self, inst_key, **params):
        inst_params_key = self.get_instance_params_key(inst_key)
        keyvals = ['='.join(map(str, item)) for item in sorted(params.items())]
        return '%s:%s' % (inst_params_key, ':'.join(keyvals))

    def get_serialized_data(self, inst_key, data_getter, **params):
        key = self.get_serialized_data_key(inst_key, **params)
        data = cache.get(key)

        if data is None:
            data = data_getter()
            cache.set(key, data)

            # Cache the key itself
            meta_key = self.get_serialized_data_meta_key(inst_key)
            keys = cache.get(meta_key) or set()
            keys.add(key)
            cache.set(meta_key, keys, settings.API_CACHE_TIMEOUT)

        return data

    def get_serialized_data_keys(self, inst_key):
        meta_key = self.get_serialized_data_meta_key(inst_key)
        if meta_key is not None:
            keys = cache.get(meta_key)
            return (keys or set()) | set([meta_key])
        else:
            return set()

    def get_other_keys(self, **params):
        return set()

    def clear_instance(self, obj):
        # Collect information for cache keys
        params = self.get_cached_instance_params(obj.pk, lambda: obj)
        # Collect the prefixes for cached requests
        prefixes = self.get_request_prefixes(**params)
        prefixed_keys = self.get_keys_with_prefixes(*prefixes)
        #Serialized data keys
        data_keys = self.get_serialized_data_keys(obj)
        # Collect other related keys
        other_keys = self.get_other_keys(**params) | set([self.get_instance_params_key(obj.pk)])
        # Clear all the keys
        self.clear_keys(*(prefixed_keys | data_keys | other_keys))


class DataSetCache (Cache):
    def get_instance_params(self, dataset_obj):
        params = {
            'owner_username': dataset_obj.owner.username,
            'owner_id': dataset_obj.owner.pk,
            'dataset_slug': dataset_obj.slug,
            'dataset_id': dataset_obj.pk,
        }
        return params

    def get_request_prefixes(self, **params):
        owner, dataset = map(params.get, ('owner_username', 'dataset_slug'))
        prefixes = super(DataSetCache, self).get_request_prefixes(**params)

        instance_path = reverse('dataset-detail', args=[owner, dataset])
        collection_path = reverse('dataset-list', args=[owner])
        prefixes.update([instance_path, collection_path])

        return prefixes


class ThingWithAttachmentCache (Cache):
    dataset_cache = DataSetCache()

    def get_instance_params(self, thing_obj):
        params = self.dataset_cache.get_cached_instance_params(
            thing_obj.dataset_id, lambda: thing_obj.dataset)
        params.update({
            'thing_id': thing_obj.pk
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
            attachments[attachment.thing_id].append({
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
            cache.set(attachments_key, attachments, settings.API_CACHE_TIMEOUT)
        return attachments


class PlaceCache (ThingWithAttachmentCache, Cache):
    dataset_cache = DataSetCache()

    def get_instance_params(self, place_obj):
        params = self.dataset_cache.get_cached_instance_params(
            place_obj.dataset_id, lambda: place_obj.dataset)
        params.update({
            'place_id': place_obj.pk,
            'thing_id': place_obj.pk
        })
        return params

    def get_request_prefixes(self, **params):
        owner, dataset, place = map(params.get, ('owner_username', 'dataset_slug', 'place_id'))
        prefixes = super(PlaceCache, self).get_request_prefixes(**params)

        instance_path = reverse('place-detail', args=[owner, dataset, place])
        collection_path = reverse('place-list', args=[owner, dataset])
        dataset_instance_path = reverse('dataset-detail', args=[owner, dataset])
        dataset_collection_path = reverse('dataset-list', args=[owner])
        action_collection_path = reverse('action-list', args=[owner, dataset])
        prefixes.update([instance_path, collection_path, dataset_instance_path, 
                         dataset_collection_path, action_collection_path])

        return prefixes


class SubmissionSetCache (Cache):
    place_cache = PlaceCache()

    # NOTE: A SubmissionSet doesn't live on its own, only on a place. So,
    # invalidating a SubmissionSet should invalidate its place.
    def get_instance_params(self, submissionset_obj):
        params = self.place_cache.get_cached_instance_params(
            submissionset_obj.place_id, lambda: submissionset_obj.place)
        params.update({
            'submission_set_name': submissionset_obj.name
        })
        return params

    def get_request_prefixes(self, **params):
        owner, dataset, place = map(params.get, ['owner_username', 'dataset_slug', 'place_id'])
        prefixes = super(SubmissionSetCache, self).get_request_prefixes(**params)

        instance_path = reverse('place-detail', args=[owner, dataset, place])
        collection_path = reverse('place-list', args=[owner, dataset])
        dataset_path = reverse('dataset-detail', args=[owner, dataset])
        action_collection_path = reverse('action-list', args=[owner, dataset])

        prefixes.update([instance_path, collection_path, dataset_path, action_collection_path])

        return prefixes


class SubmissionCache (ThingWithAttachmentCache, Cache):
    dataset_cache = DataSetCache()
    place_cache = PlaceCache()
    submissionset_cache = SubmissionSetCache()

    def get_instance_params(self, submission_obj):
        params = self.submissionset_cache.get_cached_instance_params(
            submission_obj.parent_id, lambda: submission_obj.parent)
        params.update({
            'submission_id': submission_obj.pk,
            'thing_id': submission_obj.pk
        })
        return params

    def get_other_keys(self, **params):
        dataset_id, place_id = map(params.get, ['dataset_id', 'place_id'])
        dataset_serialized_data_keys = self.dataset_cache.get_serialized_data_keys(dataset_id)
        place_serialized_data_keys = self.place_cache.get_serialized_data_keys(place_id)
        return dataset_serialized_data_keys | place_serialized_data_keys

    def get_request_prefixes(self, **params):
        owner, dataset, place, submission_set_name, submission = map(params.get, ['owner_username', 'dataset_slug', 'place_id', 'submission_set_name', 'submission_id'])
        prefixes = super(SubmissionCache, self).get_request_prefixes(**params)

        specific_instance_path = reverse('submission-detail', args=[owner, dataset, place, submission_set_name, submission])
        general_instance_path = reverse('submission-detail', args=[owner, dataset, place, 'submissions', submission])
        specific_collection_path = reverse('submission-list', args=[owner, dataset, place, submission_set_name])
        general_collection_path = reverse('submission-list', args=[owner, dataset, place, 'submissions'])
        specific_all_path = reverse('dataset-submission-list', args=[owner, dataset, submission_set_name])
        general_all_path = reverse('dataset-submission-list', args=[owner, dataset, 'submissions'])
        place_instance_path = reverse('place-detail', args=[owner, dataset, place])
        place_collection_path = reverse('place-list', args=[owner, dataset])
        dataset_instance_path = reverse('dataset-detail', args=[owner, dataset])
        dataset_collection_path = reverse('dataset-list', args=[owner])
        action_collection_path = reverse('action-list', args=[owner, dataset])

        prefixes.update([specific_instance_path, general_instance_path,
                         specific_collection_path, general_collection_path,
                         specific_all_path, general_all_path,
                         place_instance_path, place_collection_path,
                         dataset_instance_path, dataset_collection_path,
                         action_collection_path])

        return prefixes


class ActionCache (Cache):
    def clear_instance(self, obj):
        keys = cache.get('action_keys') or set()
        keys.add('action_keys')
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
        thing_id = params.get('thing_id')
        thing_attachments_key = self.thing_cache.get_attachments_key(dataset_id)
        thing_serialized_data_keys = self.thing_cache.get_serialized_data_keys(thing_id)

        # Union the two sets
        return set([thing_attachments_key]) | thing_serialized_data_keys
