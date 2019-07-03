from collections import defaultdict
from django.conf import settings
from django.core import cache as django_cache
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from . import utils

import logging
logger = logging.getLogger('sa_api_v2.cache')


# A sentinel object to differentiate from None
Undefined = object()

class CacheBuffer (object):
    def __init__(self, initial_buffer=None):
        # When we get a value from the remote cache, it goes in to the buffer
        # so that we can retrieve it quickly on our next try.
        self.buffer = initial_buffer or {}
        self.timeouts = {}

        # When we set a value, it goes into the queue as well as the buffer.
        # Values are not set in the remote cache from the queue until we call
        # flush.
        self.queue = {}
        self.delete_queue = set()

    def get_many(self, keys):
        results = {}
        unseen_keys = []

        for key in keys:
            try:
                value = self.buffer[key]
                if value is not Undefined:
                    results[key] = value
            except KeyError:
                unseen_keys.append(key)

        if unseen_keys:
            new_results = django_cache.cache.get_many(unseen_keys)
            if new_results:
                results.update(new_results)
                self.buffer.update(new_results)

        # TODO: Is this what's supposed to happen? get_many returns None for
        #       each key that wasn't found?
        all_results = dict([(key, Undefined) for key in set(keys) - set(results.keys())])
        self.buffer.update(all_results)
        return results

    def get(self, key, default=None):
        if key in self.delete_queue:
            return None

        try:
            value = self.buffer[key]
            return None if value is Undefined else value
        except KeyError:
            value = django_cache.cache.get(key, default)
            self.buffer[key] = value
            return value

    def set(self, key, value, timeout=Undefined):
        self.buffer[key] = self.queue[key] = value
        self.timeouts[key] = timeout

        try: self.delete_queue.remove(key)
        except KeyError: pass

    def set_many(self, mapping, timeout=Undefined):
        self.buffer.update(mapping)
        self.queue.update(mapping)

        for key in mapping:
            self.timeouts[key] = timeout

            try: self.delete_queue.remove(key)
            except KeyError: pass

    def delete(self, key):
        try: del self.queue[key]
        except KeyError: pass

        try: del self.buffer[key]
        except KeyError: pass

        try: del self.timeouts[key]
        except KeyError: pass

        self.delete_queue.add(key)

    def delete_many(self, keys):
        for key in keys:
            try: del self.queue[key]
            except KeyError: pass

            try: del self.buffer[key]
            except KeyError: pass

            try: del self.timeouts[key]
            except KeyError: pass

        self.delete_queue.update(keys)

    # === Set operations

    def add(self, skey, members):
        members = set(members)

        if skey in self.srem_queue:
            self.srem_queue[skey] -= members
            if not self.srem_queue[skey]:
                del self.srem_queue[skey]

        new_members = (self.sadd_queue.get(skey) or set()) | members
        self.sadd_queue[skey] = new_members

        svalue = (self.buffer.get(skey) or set()) | members
        self.buffer[skey] = svalue

    def remove(self, skey, members):
        members = set(members)

        if skey in self.sadd_queue:
            self.sadd_queue[skey] -= members
            if not self.sadd_queue[skey]:
                del self.sadd_queue[skey]

        old_members = (self.srem_queue.get(skey) or set()) | members
        self.srem_queue[skey] = old_members

        svalue = (self.buffer.get(skey) or set()) - members
        self.buffer[skey] = svalue

    # === Flush, reset

    def flush(self):
        timed_queues = defaultdict(dict)

        if self.queue:
            for key, value in self.queue.items():
                timeout = self.timeouts[key]
                timed_queues[timeout][key] = value

            for timeout, queue in timed_queues.items():
                if timeout is not Undefined:
                    django_cache.cache.set_many(queue, timeout)
                else:
                    django_cache.cache.set_many(queue, settings.API_CACHE_TIMEOUT)

        # if self.sadd_queue:
        #     for key, value in self.sadd_queue.iteritems():

        if self.delete_queue:
            django_cache.cache.delete_many(self.delete_queue)

        self.reset()

    def reset(self):
        self.queue = {}
        self.delete_queue = set()
        self.timeouts = {}
        self.buffer = {}
cache_buffer = CacheBuffer()


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
            keys |= cache_buffer.get(meta_key) or set()
            keys.add(meta_key)
        logger.debug('Keys with prefixes "%s": "%s"' % ('", "'.join(prefixes), '", "'.join(keys)))
        return keys

    def clear_keys(self, *keys):
        """
        Delete all of the data from the cache identified by the given keys.
        """
        logger.debug('Deleting: "%s"' % '", "'.join(keys))
        cache_buffer.delete_many(keys)

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
        cache_buffer.delete(instance_params_key)

    def get_cached_instance_params(self, inst_key, obj_getter):
        """
        Get the instance parameters cached for the given instance key. If no
        params are cached, run the obj_getter to get the actual instance and
        calculate the parameters based on that object. The getter is a function
        so that it does not get evaluated if it doesn't have to be, since
        evaluating it may involve additional queries.
        """
        # instance_params_key = self.get_instance_params_key(inst_key)
        # params = cache_buffer.get(instance_params_key)

        # if params is None:
        #     obj = obj_getter()
        #     params = self.get_instance_params(obj)
        #     logger.debug('Setting instance parameters for "%s": %r' % (instance_params_key, params))
        #     cache_buffer.set(instance_params_key, params)
        # else:
        #     logger.debug('Found instance parameters for "%s": %r' % (instance_params_key, params))
        # return params
        obj = obj_getter()
        params = self.get_instance_params(obj)
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
        data = cache_buffer.get(key)

        if data is None:
            data = data_getter()
            cache_buffer.set(key, data)

            # Cache the key itself
            meta_key = self.get_serialized_data_meta_key(inst_key)
            keys = cache_buffer.get(meta_key) or set()
            keys.add(key)
            cache_buffer.set(meta_key, keys)

        return data

    def get_serialized_data_keys(self, inst_key):
        meta_key = self.get_serialized_data_meta_key(inst_key)
        if meta_key is not None:
            keys = cache_buffer.get(meta_key)
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


class UserCache (Cache):
    def get_instance_params(self, user_obj):
        params = {'user_id': user_obj.id}
        return params

    # == Raw query caching
    @classmethod
    def get_instance_key(cls, **params):
        return ':'.join(['user-instance', str(params['user_id'])])

    @classmethod
    def get_instance(cls, **params):
        """
        Get a full cached user instance.
        """
        key = cls.get_instance_key(**params)
        return cache_buffer.get(key)

    @classmethod
    def set_instance(cls, instance, **params):
        key = cls.get_instance_key(**params)
        cache_buffer.set(key, instance)

    # == Cache invalidation
    @classmethod
    def get_request_prefixes(cls, **params):
        return set()

    @classmethod
    def get_other_keys(cls, **params):
        return set([cls.get_instance_key(**params)])


class DataSetCache (Cache):
    # == Raw query caching
    def get_instance_key(self, **params):
        return ':'.join(['dataset-instance', params['owner_username'], params['dataset_slug']])

    def get_instance(self, **params):
        """
        Get a full cached dataset instance.
        """
        key = self.get_instance_key(**params)
        return cache_buffer.get(key)

    def set_instance(self, instance, **params):
        key = self.get_instance_key(**params)
        cache_buffer.set(key, instance)

    def get_permissions_key(self, **params):
        return ':'.join(['dataset-permissions', params['owner_username'], params['dataset_slug']])

    def get_permissions(self, **params):
        key = self.get_permissions_key(**params)
        return cache_buffer.get(key)

    def save_permissions(self, permissions, **params):
        key = self.get_permissions_key(**params)
        cache_buffer.set(key, permissions)

    # == Serialized data caching
    def get_bulk_data_cache_key(self, dataset_id, submission_set_name, format, **flags):
        return 'bulk_data:%s:%s:%s:%s' % (
            dataset_id, submission_set_name, format,
            ':'.join(k for k, v in list(flags.items()) if v))

    def get_instance_params(self, dataset_obj):
        params = {
            'owner_username': dataset_obj.owner.username,
            'owner_id': dataset_obj.owner.pk,
            'dataset_slug': dataset_obj.slug,
            'dataset_id': dataset_obj.pk,
        }
        return params

    # == Cache invalidation
    def get_request_prefixes(self, **params):
        owner, dataset = list(map(params.get, ('owner_username', 'dataset_slug')))
        prefixes = super(DataSetCache, self).get_request_prefixes(**params)

        instance_path = reverse('dataset-detail', args=[owner, dataset])
        collection_path = reverse('dataset-list', args=[owner])
        prefixes.update([instance_path, collection_path])

        return prefixes

    def get_other_keys(self, **params):
        return set([self.get_instance_key(**params), self.get_permissions_key(**params)])


class PlaceCache (Cache):
    dataset_cache = DataSetCache()

    def get_instance_params(self, place_obj):
        params = self.dataset_cache.get_cached_instance_params(
            place_obj.dataset_id, lambda: place_obj.dataset).copy()
        params.update({
            'place_id': place_obj.pk,
            'thing_id': place_obj.pk,
            'thing_type': 'place'
        })
        return params

    def get_request_prefixes(self, **params):
        owner, dataset, place = list(map(params.get, ('owner_username', 'dataset_slug', 'place_id')))
        prefixes = super(PlaceCache, self).get_request_prefixes(**params)

        instance_path = reverse('place-detail', args=[owner, dataset, place])
        collection_path = reverse('place-list', args=[owner, dataset])
        dataset_instance_path = reverse('dataset-detail', args=[owner, dataset])
        dataset_collection_path = reverse('dataset-list', args=[owner])
        action_collection_path = reverse('action-list', args=[owner, dataset])
        prefixes.update([instance_path, collection_path, dataset_instance_path,
                         dataset_collection_path, action_collection_path])

        return prefixes


class SubmissionCache (Cache):
    dataset_cache = DataSetCache()
    place_cache = PlaceCache()

    def get_instance_params(self, submission_obj):
        params = self.place_cache.get_cached_instance_params(
            submission_obj.place_id, lambda: submission_obj.place).copy()
        params.update({
            'submission_set_name': submission_obj.set_name,
            'submission_id': submission_obj.pk,
            'thing_id': submission_obj.pk,
            'thing_type': 'submission'
        })
        return params

    def get_other_keys(self, **params):
        dataset_id, place_id, submission_set_name = list(map(params.get, ['dataset_id', 'place_id', 'submission_set_name']))
        dataset_serialized_data_keys = self.dataset_cache.get_serialized_data_keys(dataset_id)
        place_serialized_data_keys = self.place_cache.get_serialized_data_keys(place_id)
        return dataset_serialized_data_keys | place_serialized_data_keys

    def get_request_prefixes(self, **params):
        owner, dataset, place, submission_set_name, submission = list(map(params.get, ['owner_username', 'dataset_slug', 'place_id', 'submission_set_name', 'submission_id']))
        prefixes = super(SubmissionCache, self).get_request_prefixes(**params)

        # TODO: it's pretty clear that a developer should be able to register
        # a URL with or cache key or prefix or something to be cleared. How
        # would that work?
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
        keys = cache_buffer.get('action_keys') or set()
        keys.add('action_keys')
        cache_buffer.delete_many(keys)


class ThingWithAttachmentCache (Cache):
    place_cache = PlaceCache()
    submission_cache = SubmissionCache()

    def get_instance_params(self, thing_obj):
        try:
            return self.place_cache.get_instance_params(thing_obj.full_place)
        except ObjectDoesNotExist:
            return self.submission_cache.get_instance_params(thing_obj.full_submission)

    def get_serialized_data_keys(self, thing_obj):
        try:
            return self.place_cache.get_instance_params(thing_obj.full_place)
        except ObjectDoesNotExist:
            return self.submission_cache.get_instance_params(thing_obj.full_submission)

    def get_attachments_key(self, dataset_id):
        return 'dataset:%s:%s' % (dataset_id, 'attachments-by-thing_id')


class AttachmentCache (Cache):
    thing_cache = ThingWithAttachmentCache()
    place_cache = PlaceCache()
    submission_cache = SubmissionCache()

    def get_instance_params(self, attachment_obj):
        params = self.thing_cache.get_cached_instance_params(
            attachment_obj.thing_id, lambda: attachment_obj.thing).copy()
        params.update({
            'attachment': attachment_obj.name,
            'attachment_id': attachment_obj.pk,
        })
        return params

    def get_request_prefixes(self, **params):
        prefixes = super(AttachmentCache, self).get_request_prefixes(**params)
        if params['thing_type'] == 'submission':
            return prefixes | self.get_submission_attachment_request_prefixes(**params)
        else:
            return prefixes | self.get_place_attachment_request_prefixes(**params)

    def get_submission_attachment_request_prefixes(self, **params):
        owner, dataset, place, submission_set_name, submission = list(map(params.get, ['owner_username', 'dataset_slug', 'place_id', 'submission_set_name', 'submission_id']))
        prefixes = set()

        specific_instance_path = reverse('submission-detail', args=[owner, dataset, place, submission_set_name, submission])
        general_instance_path = reverse('submission-detail', args=[owner, dataset, place, 'submissions', submission])
        specific_collection_path = reverse('submission-list', args=[owner, dataset, place, submission_set_name])
        general_collection_path = reverse('submission-list', args=[owner, dataset, place, 'submissions'])
        specific_all_path = reverse('dataset-submission-list', args=[owner, dataset, submission_set_name])
        general_all_path = reverse('dataset-submission-list', args=[owner, dataset, 'submissions'])
        action_collection_path = reverse('action-list', args=[owner, dataset])

        prefixes.update([specific_instance_path, general_instance_path,
                         specific_collection_path, general_collection_path,
                         specific_all_path, general_all_path,
                         action_collection_path])

        return prefixes

    def get_place_attachment_request_prefixes(self, **params):
        owner, dataset, place = list(map(params.get, ('owner_username', 'dataset_slug', 'place_id')))
        prefixes = set()

        instance_path = reverse('place-detail', args=[owner, dataset, place])
        collection_path = reverse('place-list', args=[owner, dataset])
        action_collection_path = reverse('action-list', args=[owner, dataset])
        prefixes.update([instance_path, collection_path, action_collection_path])

        return prefixes

    def get_other_keys(self, **params):
        dataset_id = params.get('dataset_id')
        thing_id = params.get('thing_id')
        thing_attachments_key = self.thing_cache.get_attachments_key(dataset_id)

        if params['thing_type'] == 'submission':
            thing_serialized_data_keys = self.submission_cache.get_serialized_data_keys(thing_id)
        else:
            thing_serialized_data_keys = self.place_cache.get_serialized_data_keys(thing_id)

        # Union the two sets
        return set([thing_attachments_key]) | thing_serialized_data_keys
