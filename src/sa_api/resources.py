"""
DjangoRestFramework resources for the Shareabouts REST API.
"""
import ujson as json
import apikey.models
from collections import defaultdict
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db.models import Count
from djangorestframework import resources
from . import models
from . import utils
from . import forms
from . import cache


def simple_user(user):
    """Return a minimal representation of an auth.User"""
    return {
        'id': user.pk,
        'username': user.username,
    }


class OwnerResource (resources.ModelResource):
    model = User
    fields = ['id', 'username', 'datasets']
    queryset = User.objects.all().annotate(dataset_count=Count('datasets')).filter(dataset_count__gt=0)

    def datasets(self, inst):
        datasets = {
            'url': reverse('dataset_collection_by_user', args=[inst.username]),
            'length': inst.dataset_count
        }
        return datasets


class ModelResourceWithDataBlob (resources.ModelResource):

    """
    Like ModelResource, but automatically serializes/deserializes a
    'data' JSON blob of arbitrary key/value pairs.
    """

    def should_show_private_data(self):
        if not hasattr(self, 'view') or self.view is None:
            return False

        if not hasattr(self.view, 'show_private_data'):
            return False

        if self.view.show_private_data is not True:
            return False

        return True

    def serialize(self, obj, *args, **kwargs):
        # If the object is a place, parse the data blob and add it to the
        # place's fields.
        serialization = super(ModelResourceWithDataBlob, self).serialize(obj, *args, **kwargs)
        if isinstance(obj, self.model):
            data = json.loads(obj.data)
            serialization.pop('data', None)

            if not self.should_show_private_data():
                for key in data.keys():
                    if key.startswith('private-'):
                        del data[key]
            serialization.update(data)

        return serialization

    def validate_request(self, origdata, files=None):
        if origdata:
            data = origdata.copy()
            blob_data = {}

            # Pull off any fields that the model doesn't know about directly
            # and put them into the data blob.
            known_fields = set(self.model._meta.get_all_field_names())

            # Also ignore the following field names (treat them like reserved
            # words).
            known_fields.update(['submissions'])

            # And allow an arbitrary value field named 'data' (don't let the
            # data blob get in the way).
            known_fields.remove('data')

            for key in origdata:
                if key not in known_fields:
                    blob_data[key] = data[key]
                    del data[key]
            data['data'] = json.dumps(blob_data)

        else:
            data = origdata
        return super(ModelResourceWithDataBlob, self).validate_request(data, files)


class AttachmentResource (resources.ModelResource):
    model = models.Attachment
    form = forms.AttachmentForm
    exclude = ['thing', 'file', 'id']
    include = ['url']

    def url(self, inst):
        return inst.file.url


class PlaceResource (ModelResourceWithDataBlob):
    model = models.Place
    form = forms.PlaceForm
    queryset = model.objects.all().select_related()

    dataset_cache = cache.DataSetCache()

    exclude = ['data', 'submittedthing_ptr']
    include = ['url', 'submissions', 'attachments']

    # TODO: this can be abstracted into a mixin.
    def instance_params(self, inst):
        """
        Get arguments from the cache for retrieving information about the
        instance.
        """
        return self.model.cache.get_cached_instance_params(inst.pk, lambda: inst)

    def location(self, place):
        return {
            'lat': place.location.y,
            'lng': place.location.x,
        }

    def dataset(self, place):
        owner, dataset = map(self.instance_params(place).get, ['owner', 'dataset'])
        dataset = {
          'url': reverse('dataset_instance_by_user', args=(owner, dataset))
        }
        return dataset

    def url(self, place):
        owner, dataset = map(self.instance_params(place).get, ['owner', 'dataset'])
        url = reverse('place_instance_by_dataset', args=(owner, dataset, place.pk))
        return url

    def submissions(self, place):
        submission_sets = self.model.cache.get_submission_sets(place.dataset_id)
        return submission_sets.get(place.id, [])

    def attachments(self, place):
        attachments = self.model.cache.get_attachments(place.dataset_id)
        return attachments.get(place.id, [])

    def validate_request(self, origdata, files=None):
        if origdata:
            data = origdata.copy()

            # Convert the location into something that GeoDjango knows how to
            # deal with.
            data['location'] = utils.to_wkt(origdata.get('location'))

        else:
            data = origdata
        return super(PlaceResource, self).validate_request(data, files)

    def filter_response(self, obj):
        """
        Further filter results, beyond DB filtering. This must be done here
        because we cannot filter based on data blob values in the DB directly
        unless we impleent some indexing.
        """
        data = super(PlaceResource, self).filter_response(obj)

        if isinstance(data, list):
            # These filters will have been applied when constructing the queryset
            special_filters = set(['visible', 'format', 'show_private', 'near'])

            for key, values in self.view.request.GET.iterlists():
                if key not in special_filters:
                    data = [item for item in data
                               if item.get(key, None) in values]
        return data


class DataSetResource (resources.ModelResource):
    model = models.DataSet
    form = forms.DataSetForm
    fields = ['id', 'url', 'owner', 'places', 'slug', 'display_name', 'keys', 'submissions']
    queryset = model.objects.all().select_related()

    # TODO: Move this to the cache module. Invalidate on place save.
    @utils.cached_property
    def places_counts(self):
        # TODO: We should check the view attached to the resource to see whether
        #       it refers to a user or a dataset so that we can filter and not
        #       get ALL the places, which is wasteful.
        qs = models.Place.objects.values('dataset_id').annotate(length=Count('dataset'))

        places_counts = dict([(places['dataset_id'], places['length'])
                              for places in qs])
        return places_counts

    # TODO: Move this to the cache module. Invalidate on submission save.
    @utils.cached_property
    def submission_sets(self):
        """
        A mapping from DataSet ids to attributes.  Helps to cut down
        significantly on the number of queries.
        """
        submission_sets = defaultdict(set)
        submission_counts = defaultdict(lambda: defaultdict(int))

        qs = models.SubmissionSet.objects.all().select_related()
        for submission_set in qs.annotate(length=Count('children')):
            # Ignore empty sets
            if submission_set.length <= 0:
                continue

            ds_id = submission_set.place.dataset_id
            ss_type = submission_set.submission_type

            # Keep a total of how many of each submission type you've seen
            submission_counts[ds_id][ss_type] += submission_set.length

            # Build a list of unique submission set types; use tuples so that
            # we can compare values.
            submission_sets[ds_id].add((
                ('type', ss_type),
                ('url', reverse('all_submissions_by_dataset', kwargs={
                    'dataset__owner__username': submission_set.place.dataset.owner.username,
                    'dataset__slug': submission_set.place.dataset.slug,
                    'submission_type': ss_type
                }))
            ))

        # Go through and create a dictionary from all the tuple sets
        for dataset_id, submission_sets_data in submission_sets.items():
            submission_sets[dataset_id] = [dict(data) for data in submission_sets_data]

        # Attach the counts to the dictionaries
        for dataset_id, type_counts in submission_counts.items():
            for submission_set in submission_sets[dataset_id]:
                submission_type = submission_set['type']
                submission_set['length'] = type_counts[submission_type]

        return submission_sets

    def owner(self, dataset):
        return simple_user(dataset.owner)

    # TODO: construct with the cache's instance_params.
    def places(self, dataset):
        url = reverse('place_collection_by_dataset',
                      kwargs={
                         'dataset__owner__username': dataset.owner.username,
                         'dataset__slug': dataset.slug})
        return {'url': url, 'length': self.places_counts.get(dataset.id, 0)}

    def submissions(self, dataset):
        return self.submission_sets[dataset.id]

    # TODO: construct with the cache's instance_params.
    def url(self, instance):
        return reverse('dataset_instance_by_user',
                       kwargs={'owner__username': instance.owner.username,
                               'slug': instance.slug})

    # TODO: construct with the cache's instance_params.
    def keys(self, instance):
        url = reverse('api_key_collection_by_dataset',
                      kwargs={'datasets__owner__username': instance.owner.username,
                              'datasets__slug': instance.slug,
                              })
        return {'url': url}


class SubmissionResource (ModelResourceWithDataBlob):
    model = models.Submission
    form = forms.SubmissionForm
    exclude = ['parent', 'data', 'submittedthing_ptr']
    include = ['type', 'place', 'url', 'attachments']
    queryset = model.objects.select_related().order_by('created_datetime')

    # TODO: this can be abstracted into a mixin.
    def instance_params(self, inst):
        """
        Get arguments from the cache for retrieving information about the
        instance.
        """
        return self.model.cache.get_cached_instance_params(inst.pk, lambda: inst)

    def type(self, submission):
        return submission.parent.submission_type

    def place(self, submission):
        owner, dataset, place = map(self.instance_params(submission).get, ['owner', 'dataset', 'place'])
        url = reverse('place_instance_by_dataset', args=[owner, dataset, place])
        return {'url': url, 'id': place}

    def dataset(self, submission):
        owner, dataset = map(self.instance_params(submission).get, ['owner', 'dataset'])
        url = reverse('dataset_instance_by_user', args=(owner, dataset))
        return {'url': url}

    def attachments(self, submission):
        attachments = self.model.cache.get_attachments(submission.dataset_id)
        return attachments.get(submission.id, [])

    def url(self, submission):
        owner, dataset, place, set_name, pk = map(
            self.instance_params(submission).get, ['owner', 'dataset', 'place', 'set_name', 'submission'])
        return reverse('submission_instance_by_dataset', args=(owner, dataset, place, set_name, pk))


class GeneralSubmittedThingResource (ModelResourceWithDataBlob):
    model = models.SubmittedThing
    fields = ['created_datetime', 'updated_datetime', 'submitter_name', 'id']


class ActivityResource (resources.ModelResource):
    model = models.Activity
    fields = ['action', 'type', 'id', 'place_id', ('data', GeneralSubmittedThingResource)]

    @property
    def queryset(self):
        return models.Activity.objects.filter(data_id__in=self.things)

    # TODO: Move this to the cache module. Invalidate on submitted thing save.
    @utils.cached_property
    def things(self):
        """
        A mapping from SubmittedThing ids to attributes.  Helps to cut down
        significantly on the number of queries.

        """
        things = {}

        for place in self.view.get_places():
            things[place.submittedthing_ptr_id] = {
                'type': 'places',
                'place_id': place.id,
                'data': place
            }
        for submission in self.view.get_submissions():
            things[submission.submittedthing_ptr_id] = {
                'type': submission.parent.submission_type,
                'place_id': submission.parent.place_id,
                'data': submission
            }

        return things

    def type(self, obj):
        return self.things[obj.data_id]['type']

    def place_id(self, obj):
        return self.things[obj.data_id]['place_id']

    def data(self, obj):
        return self.things[obj.data_id]['data']


class ApiKeyResource(resources.ModelResource):

    model = apikey.models.ApiKey

    fields = ('key', 'logged_ip', 'last_used')


class TabularPlaceResource (PlaceResource):
    exclude = PlaceResource.exclude + ['dataset', 'url', 'name', 'updated_datetime']

    def serialize(self, obj, *args, **kwargs):
        serialization = super(TabularPlaceResource, self).serialize(obj, *args, **kwargs)

        if isinstance(obj, self.model):
            for fieldname in ['id', 'submitter_name', 'created_datetime', 'visible', 'location']:
                fieldvalue = serialization.pop(fieldname)
                serialization['place_' + fieldname] = fieldvalue

            submission_sets = serialization.pop('submissions')
            for submission_set in submission_sets:
                serialization[submission_set['type']] = submission_set['length']

        return serialization


class TabularSubmissionResource (SubmissionResource):
    exclude = SubmissionResource.exclude + ['dataset', 'url', 'name', 'updated_datetime']

    def serialize(self, obj, *args, **kwargs):
        serialization = super(TabularSubmissionResource, self).serialize(obj, *args, **kwargs)

        if isinstance(obj, self.model):
            submissionset = serialization.pop('type')
            if submissionset.endswith('s'):
                submissiontype = submissionset[:-1]
            else:
                submissiontype = submissionset

            place = serialization.pop('place')
            serialization['place_id'] = place['id']

            for fieldname in ['id', 'submitter_name', 'created_datetime', 'visible']:
                fieldvalue = serialization.pop(fieldname)
                serialization['_'.join([submissiontype, fieldname])] = fieldvalue

        return serialization
