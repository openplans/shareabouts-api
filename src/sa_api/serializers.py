"""
DjangoRestFramework resources for the Shareabouts REST API.
"""
import ujson as json
from itertools import groupby
from django.contrib.gis.geos import GEOSGeometry
from django.db.models import Count
from rest_framework import pagination
from rest_framework import serializers
from rest_framework.reverse import reverse

from . import models
from . import utils
from . import cache


###############################################################################
#
# Geo-related fields
# ------------------
#

class GeometryField(serializers.WritableField):
    def __init__(self, format='dict', *args, **kwargs):
        self.format = format
        
        if self.format not in ('json', 'wkt'):
            raise ValueError('Invalid format: %s' % self.format)
        
        super(GeometryField, self).__init__(*args, **kwargs)
    
    def to_native(self, obj):
        if self.format == 'json':
            return obj.json
        elif self.format == 'wkt':
            return obj.wkt
        else:
            raise ValueError('Cannot output as %s' % self.format)

    def from_native(self, data):
        if not isinstance(data, basestring):
            data = json.dumps(data)
        return GEOSGeometry(data)


###############################################################################
#
# Shareabouts-specific fields
# ---------------------------
#

class ShareaboutsFieldMixin (object):

    # These names should match the names of the cache parameters, and should be
    # in the same order as the corresponding URL arguments.
    url_arg_names = ()

    def get_url_kwargs(self, obj):
        """
        Pull the appropriate arguments off of the cache to construct the URL.
        """
        instance_kwargs = obj.cache.get_cached_instance_params(obj.pk, lambda: obj)
        url_kwargs = dict([(arg_name, instance_kwargs[arg_name])
                           for arg_name in self.url_arg_names])
        return url_kwargs


class ShareaboutsRelatedField (ShareaboutsFieldMixin, serializers.HyperlinkedRelatedField):
    """
    Represents a Shareabouts relationship using hyperlinking.
    """
    read_only = True
    view_name = None

    def __init__(self, *args, **kwargs):
        if self.view_name is not None:
            kwargs['view_name'] = self.view_name
        super(ShareaboutsRelatedField, self).__init__(*args, **kwargs)

    def to_native(self, obj):
        view_name = self.view_name
        request = self.context.get('request', None)
        format = self.format or self.context.get('format', None)

        pk = getattr(obj, 'pk', None)
        if pk is None:
            return

        kwargs = self.get_url_kwargs(obj)
        return reverse(view_name, kwargs=kwargs, request=request, format=format)


class DataSetRelatedField (ShareaboutsRelatedField):
    view_name = 'dataset-detail'
    url_arg_names = ('owner_username', 'dataset_slug')


class PlaceRelatedField (ShareaboutsRelatedField):
    view_name = 'place-detail'
    url_arg_names = ('owner_username', 'dataset_slug', 'place_id')


class SubmissionSetRelatedField (ShareaboutsRelatedField):
    view_name = 'submission-list'
    url_arg_names = ('owner_username', 'dataset_slug', 'place_id', 'submission_set_name')


class ShareaboutsIdentityField (ShareaboutsFieldMixin, serializers.HyperlinkedIdentityField):
    read_only = True

    def field_to_native(self, obj, field_name):
        request = self.context.get('request', None)
        format = self.context.get('format', None)
        view_name = self.view_name or self.parent.opts.view_name

        kwargs = self.get_url_kwargs(obj)

        if format and self.format and self.format != format:
            format = self.format

        return reverse(view_name, kwargs=kwargs, request=request, format=format)


class PlaceIdentityField (ShareaboutsIdentityField):
    url_arg_names = ('owner_username', 'dataset_slug', 'place_id')


class SubmissionSetIdentityField (ShareaboutsIdentityField):
    url_arg_names = ('owner_username', 'dataset_slug', 'place_id', 'submission_set_name')

    def __init__(self, *args, **kwargs):
        super(SubmissionSetIdentityField, self).__init__(
            view_name=kwargs.pop('view_name', 'submission-list'),
            *args, **kwargs)


class SubmissionIdentityField (ShareaboutsIdentityField):
    url_arg_names = ('owner_username', 'dataset_slug', 'place_id', 'submission_set_name', 'submission_id')


class AttachmentSerializer (serializers.ModelSerializer):
    class Meta:
        model = models.Attachment


###############################################################################
#
# Serializer Mixins
# -----------------
#

class DataBlobProcessor (object):
    """
    Like ModelSerializer, but automatically serializes/deserializes a
    'data' JSON blob of arbitrary key/value pairs.
    """

    def convert_object(self, obj):
        attrs = super(DataBlobProcessor, self).convert_object(obj)

        data = json.loads(obj.data)
        del attrs['data']
        attrs.update(data)

        return attrs

    def restore_fields(self, data, files):
        """
        Converts a dictionary of data into a dictionary of deserialized fields.
        """
        model = self.opts.model
        blob = {}
        data_copy = {}

        # Pull off any fields that the model doesn't know about directly
        # and put them into the data blob.
        known_fields = set(model._meta.get_all_field_names())

        # Also ignore the following field names (treat them like reserved
        # words).
        known_fields.update(self.fields.keys())

        # And allow an arbitrary value field named 'data' (don't let the
        # data blob get in the way).
        known_fields.remove('data')

        for key in data:
            if key in known_fields:
                data_copy[key] = data[key]
            else:
                blob[key] = data[key]

        data_copy['data'] = json.dumps(blob)

        if not self.partial:
            for field_name, field in self.fields.items():
                if (not field.read_only and field_name not in data_copy):
                    data_copy[field_name] = field.default

        return super(DataBlobProcessor, self).restore_fields(data_copy, files)

    def to_native(self, obj):
        data = super(DataBlobProcessor, self).to_native(obj)
        blob = data.pop('data')

        blob_data = json.loads(blob)
        request = self.context['request']

        # Did the user not ask for private data? Remove it!
        if 'include_private' not in request.GET:
            for key in blob_data.keys():
                if key.startswith('private'):
                    del blob_data[key]

        data.update(blob_data)
        return data


###############################################################################
#
# Serializers
# -----------
#

class SubmissionSetSerializer (serializers.Serializer):
    length = serializers.IntegerField
    url = SubmissionSetIdentityField()


class SubmissionSetSummarySerializer (serializers.HyperlinkedModelSerializer):
    length = serializers.IntegerField()
    url = SubmissionSetIdentityField()

    class Meta:
        model = models.SubmissionSet
        fields = ('length', 'url')


class PlaceSerializer (DataBlobProcessor, serializers.HyperlinkedModelSerializer):
    url = PlaceIdentityField()
    geometry = GeometryField(format='wkt')
    dataset = DataSetRelatedField()
    attachments = AttachmentSerializer(read_only=True)

    def get_submission_set_summaries(self, dataset_id):
        """
        Get a mapping from place id to a submission set summary dictionary.
        Get this for the entire dataset at once.
        """
        all_sets = models.SubmissionSet.objects.filter(place__dataset_id=dataset_id)
        
        request = self.context['request']
        if 'include_invisible' not in request.GET:
            all_sets = all_sets.filter(children__visible=True)
        
        all_sets = all_sets.annotate(length=Count('children')).filter(length__gt=0)
        all_sets = groupby(all_sets, lambda s: s.place_id)
        
        summaries = {}
        for place_id, submission_sets in all_sets:
            summaries[place_id] = {}
            for submission_set in submission_sets:
                serializer = SubmissionSetSummarySerializer(submission_set, context=self.context)
                summaries[place_id][submission_set.name] = serializer.data
        return summaries

    def get_detailed_submission_sets(self, dataset_id):
        """
        Get a mapping from place id to a detiled submission set dictionary.
        Get this for the entire dataset at once.
        """
        all_submissions = models.Submission.objects\
            .filter(dataset_id=dataset_id).select_related('parent')

        request = self.context['request']
        if 'include_invisible' not in request.GET:
            all_submissions = all_submissions.filter(visible=True)

        sets = groupby(all_submissions, lambda s: (s.place_id, s.set_name))

        details = {}
        for (place_id, set_name), submissions in sets:
            serializer = SubmissionSerializer(submissions, context=self.context)
            if place_id not in details: details[place_id] = {}
            details[place_id][set_name] = serializer.data
        return details

    def get_submission_set_flags(self):
        """
        Get a dictionary of flags that determine the contents of the place's
        submission sets. These flags are used primarily to determine the cache
        key for the submission sets structure.
        """
        request = self.context['request']
        return {
            'include_submissions': 'include_submissions' in request.GET,
            'include_private': 'include_private' in request.GET,
            'include_invisible': 'include_invisible' in request.GET,
        }
    
    def to_native(self, obj):
        data = super(PlaceSerializer, self).to_native(obj)
        request = self.context['request']

        if 'include_submissions' not in request.GET:
            submission_sets_getter = self.get_submission_set_summaries
        else:
            submission_sets_getter = self.get_detailed_submission_sets

        # Get the submission sets related to this dataset, mapped by place id.
        # This is done to decrease the number of queries we have to run, 
        # especially when getting the list of places in the dataset.
        submission_sets_map = models.Place.cache.get_submission_sets(
            obj.dataset_id,
            submission_sets_getter,
            **self.get_submission_set_flags()
        )
        data['submission_sets'] = submission_sets_map.get(obj.id, {})
        
        if hasattr(obj, 'distance'):
            data['distance'] = str(obj.distance)

        return data

    class Meta:
        model = models.Place


class SubmissionSerializer (DataBlobProcessor, serializers.HyperlinkedModelSerializer):
    url = SubmissionIdentityField()
    dataset = DataSetRelatedField()
    set = SubmissionSetRelatedField(source='parent')
    place = PlaceRelatedField(source='parent.place')
    attachments = AttachmentSerializer(read_only=True)

    class Meta:
        model = models.Submission
        exclude = ('parent',)


###############################################################################
#
# Pagination Serializers
# ----------------------
#

class PaginationMetadataSerializer (serializers.Serializer):
    length = serializers.Field(source='paginator.count')
    next = pagination.NextPageField(source='*')
    previous = pagination.PreviousPageField(source='*')
    page = serializers.Field(source='number')


class PaginatedResultsSerializer (pagination.BasePaginationSerializer):
    metadata = PaginationMetadataSerializer(source='*')


class FeatureCollectionSerializer (PaginatedResultsSerializer):
    results_field = 'features'

    def to_native(self, obj):
        data = super(FeatureCollectionSerializer, self).to_native(obj)
        data['type'] = 'FeatureCollection'
        return data

