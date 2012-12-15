from django.core.cache import cache
from django.core.urlresolvers import reverse
from . import utils


class Cache (object):
    def get_meta_key(self, prefix):
        return prefix + '_keys'

    def clear_keys_with_prefixes(self, *prefixes):
        # Clear the cache for all the keys managed by this class
        keys = set()
        for prefix in prefixes:
            meta_key = self.get_meta_key(prefix)
            keys |= cache.get(meta_key) or set()
            keys.add(meta_key)
        cache.delete_many(keys)

    def get_instance_params_key(self, obj):
        return '%s:%s' % (self.__class__.__name__, obj.pk)

    def clear_instance_params(self, obj):
        instance_params_key = self.get_instance_params_key(obj)
        cache.delete(instance_params_key)

    def get_cached_instance_params(self, obj):
        instance_params_key = self.get_instance_params_key(obj)
        params = cache.get(instance_params_key)

        if params is None:
            params = self.get_instance_params(obj)
            cache.set(instance_params_key, params)
        return params

    def clear_instance(self, obj):
        # Collect information for cache keys
        params = self.get_cached_instance_params(obj)
        # Collect the prefixes for cached requests
        prefixes = self.get_request_prefixes(*params)
        # Clear all the keys
        self.clear_keys_with_prefixes(*prefixes)
        self.clear_instance_params(obj)


class DataSetCache (Cache):
    def get_instance_params(self, dataset_obj):
        owner = dataset_obj.owner.username
        dataset = dataset_obj.slug
        return (owner, dataset)

    def get_request_prefixes(self, owner, dataset):
        instance_path = reverse('dataset_instance_by_user', args=[owner, dataset])
        collection_path = reverse('dataset_collection_by_user', args=[owner])
        return (instance_path, collection_path)


class PlaceCache (Cache):
    def get_instance_params(self, place_obj):
        owner = place_obj.dataset.owner.username
        dataset = place_obj.dataset.slug
        place = place_obj.pk
        return (owner, dataset, place)

    def get_request_prefixes(self, owner, dataset, place):
        instance_path = reverse('place_instance_by_dataset', args=[owner, dataset, place])
        collection_path = reverse('place_collection_by_dataset', args=[owner, dataset])
        activity_path = reverse('activity_collection_by_dataset', args=[owner, dataset])
        return (instance_path, collection_path, activity_path)


class SubmissionSetCache (Cache):
    # NOTE: A SubmissionSet doesn't live on its own, only on a place. So,
    # invalidating a SubmissionSet should invalidate its place.
    def get_instance_params(self, submissionset_obj):
        owner = submissionset_obj.place.dataset.owner.username
        dataset = submissionset_obj.place.dataset.slug
        place = submissionset_obj.place.pk
        return (owner, dataset, place)

    def get_request_prefixes(self, owner, dataset, place):
        instance_path = reverse('place_instance_by_dataset', args=[owner, dataset, place])
        collection_path = reverse('place_collection_by_dataset', args=[owner, dataset])
        dataset_path = reverse('dataset_instance_by_user', args=[owner, dataset])
        activity_path = reverse('activity_collection_by_dataset', args=[owner, dataset])
        return (instance_path, collection_path, dataset_path, activity_path)


class SubmissionCache (Cache):
    def get_instance_params(self, submission_obj):
        owner = submission_obj.dataset.owner.username
        dataset = submission_obj.dataset.slug
        place = submission_obj.parent.place.pk
        set_name = submission_obj.parent.submission_type
        submission = submission_obj.pk
        return (owner, dataset, place, set_name, submission)

    def get_request_prefixes(self, owner, dataset, place, set_name, submission):
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
