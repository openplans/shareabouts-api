from collections import defaultdict
from django.core.cache import cache
from django.core.urlresolvers import reverse
from . import utils


class Cache (object):
    def get_meta_key(self, prefix):
        return prefix + '_keys'

    def get_keys_with_prefixes(self, *prefixes):
        keys = set()
        for prefix in prefixes:
            meta_key = self.get_meta_key(prefix)
            keys |= cache.get(meta_key) or set()
            keys.add(meta_key)
        return keys

    def clear_keys(self, *keys):
        cache.delete_many(keys)

    def get_instance_params_key(self, inst_key):
        from django.db.models import Model
        if isinstance(inst_key, Model):
            obj = inst_key
            inst_key = obj.pk
        return '%s:%s' % (self.__class__.__name__, inst_key)

    def clear_instance_params(self, obj):
        instance_params_key = self.get_instance_params_key(obj)
        cache.delete(instance_params_key)

    def get_cached_instance_params(self, inst_key, obj_getter):
        instance_params_key = self.get_instance_params_key(inst_key)
        params = cache.get(instance_params_key)

        if params is None:
            obj = obj_getter()
            params = self.get_instance_params(obj)
            cache.set(instance_params_key, params)
        return params

    def get_other_keys(self, *params):
        return set()

    def clear_instance(self, obj):
        # Collect information for cache keys
        params = self.get_cached_instance_params(obj.pk, lambda: obj)
        # Collect the prefixes for cached requests
        prefixes = self.get_request_prefixes(*params)
        prefixed_keys = self.get_keys_with_prefixes(*prefixes)
        # Collect other related keys
        other_keys = self.get_other_keys(*params) | set([self.get_instance_params_key(obj.pk)])
        # Clear all the keys
        self.clear_keys(*(prefixed_keys | other_keys))


class DataSetCache (Cache):
    def get_instance_params(self, dataset_obj):
        owner = dataset_obj.owner.username
        dataset = dataset_obj.slug
        return (owner, dataset)

    def get_request_prefixes(self, owner, dataset):
        instance_path = reverse('dataset_instance_by_user', args=[owner, dataset])
        collection_path = reverse('dataset_collection_by_user', args=[owner])
        return (instance_path, collection_path)

    def get_submission_sets_key(self, dataset):
        return '%s:%s:%s' % (self.__class__.__name__, dataset, 'submission_sets')

    def calculate_submission_sets(self, dataset):
        # Import SubmissionSet here to avoid circular dependencies.
        from django.db.models import Count
        from .models import SubmissionSet

        submission_sets = defaultdict(list)

        qs = SubmissionSet.objects.filter(place__dataset_id=dataset)
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

    def get_submission_sets(self, dataset):
        """
        A mapping from Place ids to attributes.  Helps to cut down
        significantly on the number of queries.

        There should be at most one SubmissionSet of a given type for one place.
        NOTE: dataset is a dataset id, not a slug.
        """
        submission_sets_key = self.get_submission_sets_key(dataset)
        submission_sets = cache.get(submission_sets_key)
        if submission_sets is None:
            submission_sets = self.calculate_submission_sets(dataset)
            cache.set(submission_sets_key, submission_sets)
        return submission_sets


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
    dataset_cache = DataSetCache()

    def get_instance_params(self, submission_obj):
        owner = submission_obj.dataset.owner.username
        dataset = submission_obj.dataset.slug
        ds_id = submission_obj.dataset.pk
        place = submission_obj.parent.place.pk
        set_name = submission_obj.parent.submission_type
        submission = submission_obj.pk
        return (owner, dataset, ds_id, place, set_name, submission)

    def get_other_keys(self, owner, dataset, ds_id, place, set_name, submission):
        ds_submission_sets_key = self.dataset_cache.get_submission_sets_key(ds_id)
        return set([ds_submission_sets_key])

    def get_request_prefixes(self, owner, dataset, ds_id, place, set_name, submission):
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
