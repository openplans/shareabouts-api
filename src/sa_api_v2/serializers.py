"""
DjangoRestFramework resources for the Shareabouts REST API.
"""
import ujson as json
import re
from collections import defaultdict
from itertools import chain
from django.contrib.gis.geos import GEOSGeometry
from django.core.exceptions import ValidationError
from django.utils.http import urlquote_plus
from rest_framework import pagination
from rest_framework import serializers
# from rest_framework.reverse import reverse

from . import apikey
from . import cors
from . import models
from .models import check_data_permission
from .params import (INCLUDE_INVISIBLE_PARAM, INCLUDE_PRIVATE_PARAM,
    INCLUDE_SUBMISSIONS_PARAM, FORMAT_PARAM)

import logging
log = logging.getLogger(__name__)


###############################################################################
#
# Geo-related fields
# ------------------
#

class GeometryField(serializers.WritableField):
    def __init__(self, format='dict', *args, **kwargs):
        self.format = format

        if self.format not in ('json', 'wkt', 'dict'):
            raise ValueError('Invalid format: %s' % self.format)

        super(GeometryField, self).__init__(*args, **kwargs)

    def to_native(self, obj):
        if self.format == 'json':
            return obj.json
        elif self.format == 'wkt':
            return obj.wkt
        elif self.format == 'dict':
            return json.loads(obj.json)
        else:
            raise ValueError('Cannot output as %s' % self.format)

    def from_native(self, data):
        if not isinstance(data, basestring):
            data = json.dumps(data)

        try:
            return GEOSGeometry(data)
        except Exception as exc:
            raise ValidationError('Problem converting native data to Geometry: %s' % (exc,))

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
        if isinstance(obj, models.User):
            instance_kwargs = {'owner_username': obj.username}
        else:
            instance_kwargs = obj.cache.get_cached_instance_params(obj.pk, lambda: obj)

        url_kwargs = {}
        for arg_name in self.url_arg_names:
            arg_value = instance_kwargs.get(arg_name, None)
            if arg_value is None:
                try:
                    arg_value = getattr(obj, arg_name)
                except AttributeError:
                    raise KeyError('No arg named %r in %r' % (arg_name, instance_kwargs))
            url_kwargs[arg_name] = arg_value
        return url_kwargs


def api_reverse(view_name, kwargs={}, request=None, format=None):
    """
    A special case of URL reversal where we know we're getting an API URL. This
    can be much faster than Django's built-in general purpose regex resolver.

    """
    if request:
        url = '{}://{}/api/v2'.format(request.scheme, request.get_host())
    else:
        url = '/api/v2'

    route_template_strings = {
        'submission-detail': '/{owner_username}/datasets/{dataset_slug}/places/{place_id}/{submission_set_name}/{submission_id}',
        'submission-list': '/{owner_username}/datasets/{dataset_slug}/places/{place_id}/{submission_set_name}',

        'place-detail': '/{owner_username}/datasets/{dataset_slug}/places/{place_id}',
        'place-list': '/{owner_username}/datasets/{dataset_slug}/places',

        'dataset-detail': '/{owner_username}/datasets/{dataset_slug}',
        'user-detail': '/{owner_username}',
        'dataset-submission-list': '/{owner_username}/datasets/{dataset_slug}/{submission_set_name}',
    }

    try:
        route_template_string = route_template_strings[view_name]
    except KeyError:
        raise ValueError('No API route named {} formatted.'.format(view_name))

    url_params = dict([(key, urlquote_plus(val)) for key,val in kwargs.iteritems()])
    url += route_template_string.format(**url_params)

    if format is not None:
        url += '.' + format

    return url

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
        return api_reverse(view_name, kwargs=kwargs, request=request, format=format)


class DataSetRelatedField (ShareaboutsRelatedField):
    view_name = 'dataset-detail'
    url_arg_names = ('owner_username', 'dataset_slug')


class DataSetKeysRelatedField (ShareaboutsRelatedField):
    view_name = 'apikey-list'
    url_arg_names = ('owner_username', 'dataset_slug')


class UserRelatedField (ShareaboutsRelatedField):
    view_name = 'user-detail'
    url_arg_names = ('owner_username',)


class PlaceRelatedField (ShareaboutsRelatedField):
    view_name = 'place-detail'
    url_arg_names = ('owner_username', 'dataset_slug', 'place_id')


class SubmissionSetRelatedField (ShareaboutsRelatedField):
    view_name = 'submission-list'
    url_arg_names = ('owner_username', 'dataset_slug', 'place_id', 'submission_set_name')


class ShareaboutsIdentityField (ShareaboutsFieldMixin, serializers.HyperlinkedIdentityField):
    read_only = True

    def __init__(self, *args, **kwargs):
        view_name = kwargs.pop('view_name', None) or getattr(self, 'view_name', None)
        super(ShareaboutsIdentityField, self).__init__(view_name=view_name, *args, **kwargs)

    def field_to_native(self, obj, field_name):
        if obj.pk is None: return None

        request = self.context.get('request', None)
        format = self.context.get('format', None)
        view_name = self.view_name or self.parent.opts.view_name

        kwargs = self.get_url_kwargs(obj)

        if format and self.format and self.format != format:
            format = self.format

        return api_reverse(view_name, kwargs=kwargs, request=request, format=format)


class PlaceIdentityField (ShareaboutsIdentityField):
    url_arg_names = ('owner_username', 'dataset_slug', 'place_id')


class SubmissionSetIdentityField (ShareaboutsIdentityField):
    url_arg_names = ('owner_username', 'dataset_slug', 'place_id', 'submission_set_name')
    view_name = 'submission-list'


class DataSetPlaceSetIdentityField (ShareaboutsIdentityField):
    url_arg_names = ('owner_username', 'dataset_slug')
    view_name = 'place-list'


class DataSetSubmissionSetIdentityField (ShareaboutsIdentityField):
    url_arg_names = ('owner_username', 'dataset_slug', 'submission_set_name')
    view_name = 'dataset-submission-list'


class SubmissionIdentityField (ShareaboutsIdentityField):
    url_arg_names = ('owner_username', 'dataset_slug', 'place_id', 'submission_set_name', 'submission_id')


class DataSetIdentityField (ShareaboutsIdentityField):
    url_arg_names = ('owner_username', 'dataset_slug')


class AttachmentFileField (serializers.FileField):
    def to_native(self, obj):
        return obj.storage.url(obj.name)


###############################################################################
#
# Serializer Mixins
# -----------------
#


class ActivityGenerator (object):
    def save(self, **kwargs):
        request = self.context['request']
        silent_header = request.META.get('HTTP_X_SHAREABOUTS_SILENT', 'False')
        is_silent = silent_header.lower() in ('true', 't', 'yes', 'y')
        request_source = request.META.get('HTTP_REFERER', '')
        return super(ActivityGenerator, self).save(silent=is_silent, source=request_source, **kwargs)


class EmptyModelSerializer (object):
    """
    A simple mixin that constructs an in-memory model when None is passed in
    as the object to to_native.
    """
    def ensure_obj(self, obj):
        if obj is None: obj = self.opts.model()
        return obj


class DataBlobProcessor (EmptyModelSerializer):
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
        blob = json.loads(self.object.data) if self.partial else {}
        data_copy = {}

        # Pull off any fields that the model doesn't know about directly
        # and put them into the data blob.
        known_fields = set(model._meta.get_all_field_names())

        # Also ignore the following field names (treat them like reserved
        # words).
        known_fields.update(self.base_fields.keys())

        # And allow an arbitrary value field named 'data' (don't let the
        # data blob get in the way).
        known_fields.remove('data')

        # Split the incoming data into stuff that will be set straight onto
        # preexisting fields, and stuff that will go into the data blob.
        for key in data:
            if key in known_fields:
                data_copy[key] = data[key]
            else:
                blob[key] = data[key]

        data_copy['data'] = json.dumps(blob)

        if not self.partial:
            for field_name, field in self.base_fields.items():
                if (not field.read_only and field_name not in data_copy):
                    data_copy[field_name] = field.default

        return super(DataBlobProcessor, self).restore_fields(data_copy, files)

    def explode_data_blob(self, data):
        blob = data.pop('data')

        blob_data = json.loads(blob)
        request = self.context['request']

        # Did the user not ask for private data? Remove it!
        if not self.is_flag_on(INCLUDE_PRIVATE_PARAM):
            for key in blob_data.keys():
                if key.startswith('private'):
                    del blob_data[key]

        data.update(blob_data)
        return data

    def to_native(self, obj):
        obj = self.ensure_obj(obj)
        data = super(DataBlobProcessor, self).to_native(obj)
        self.explode_data_blob(data)
        return data


###############################################################################
#
# User Data Strategies
# --------------------
# Shims for reading user data from various social authentication provider
# objects.
#

class DefaultUserDataStrategy (object):
    def extract_avatar_url(self, user_info):
        return ''

    def extract_full_name(self, user_info):
        return ''

    def extract_bio(self, user_info):
        return ''


class TwitterUserDataStrategy (object):
    def extract_avatar_url(self, user_info):
        url = user_info['profile_image_url']

        url_pattern = '^(?P<path>.*?)(?:_normal|_mini|_bigger|)(?P<ext>\.[^\.]*)$'
        match = re.match(url_pattern, url)
        if match:
            return match.group('path') + '_bigger' + match.group('ext')
        else:
            return url

    def extract_full_name(self, user_info):
        return user_info['name']

    def extract_bio(self, user_info):
        return user_info['description']


class FacebookUserDataStrategy (object):
    def extract_avatar_url(self, user_info):
        url = user_info['picture']['data']['url']
        return url

    def extract_full_name(self, user_info):
        return user_info['name']

    def extract_bio(self, user_info):
        return user_info['about']


class ShareaboutsUserDataStrategy (object):
    """
    This strategy exists so that we can add avatars and full names to users
    that already exist in the system without them creating a Twitter or
    Facebook account.
    """
    def extract_avatar_url(self, user_info):
        return user_info.get('avatar_url', None)

    def extract_full_name(self, user_info):
        return user_info.get('full_name', None)

    def extract_bio(self, user_info):
        return user_info.get('bio', None)


###############################################################################
#
# Serializers
# -----------
#
# Many of the serializers below come in two forms:
#
# 1) A hyperlinked serializer -- this form includes URLs to the object's
#    related fields, as well as the object's own URL. This is useful for the
#    self-describing nature of the web API.
#
# 2) A simple serializer -- this form does not include any of the URLs in the
#    hyperlinked serializer. This is more useful for bulk data dumps where all
#    of the related data is included in a package.
#


class AttachmentSerializer (EmptyModelSerializer, serializers.ModelSerializer):
    file = AttachmentFileField()

    class Meta:
        model = models.Attachment
        exclude = ('id', 'thing',)

    def to_native(self, obj):
        obj = self.ensure_obj(obj)
        data = {
            'created_datetime': obj.created_datetime,
            'updated_datetime': obj.updated_datetime,
            'file': obj.file.storage.url(obj.file.name),
            'name': obj.name
        }
        fields = self.get_fields()

        # Construct a SortedDictWithMetaData to get the brosable API form
        ret = self._dict_class(data)
        ret.fields = self._dict_class()
        for field_name, field in fields.iteritems():
            value = data[field_name]
            ret.fields[field_name] = self.augment_field(field, field_name, field_name, value)
        return ret


class DataSetPermissionSerializer (serializers.ModelSerializer):
    class Meta:
        model = models.DataSetPermission
        exclude = ('id', 'dataset')

class GroupPermissionSerializer (serializers.ModelSerializer):
    class Meta:
        model = models.GroupPermission
        exclude = ('id', 'group')

class KeyPermissionSerializer (serializers.ModelSerializer):
    class Meta:
        model = models.KeyPermission
        exclude = ('id', 'key')

class OriginPermissionSerializer (serializers.ModelSerializer):
    class Meta:
        model = models.OriginPermission
        exclude = ('id', 'origin')

class ApiKeySerializer (serializers.ModelSerializer):
    permissions = KeyPermissionSerializer(many=True)

    class Meta:
        model = apikey.models.ApiKey
        exclude = ('id', 'dataset', 'logged_ip', 'last_used')

class OriginSerializer (serializers.ModelSerializer):
    permissions = OriginPermissionSerializer(many=True)

    class Meta:
        model = cors.models.Origin
        exclude = ('id', 'dataset', 'logged_ip', 'last_used')


# Group serializers
class BaseGroupSerializer (serializers.ModelSerializer):
    class Meta:
        model = models.Group
        exclude = ('submitters', 'id')

class SimpleGroupSerializer (BaseGroupSerializer):
    permissions = GroupPermissionSerializer(many=True)

    class Meta (BaseGroupSerializer.Meta):
        exclude = ('id', 'dataset', 'submitters')

class GroupSerializer (BaseGroupSerializer):
    dataset = DataSetRelatedField()

    class Meta (BaseGroupSerializer.Meta):
        pass


# User serializers
class BaseUserSerializer (serializers.ModelSerializer):
    name = serializers.SerializerMethodField('get_name')
    avatar_url = serializers.SerializerMethodField('get_avatar_url')
    provider_type = serializers.SerializerMethodField('get_provider_type')
    provider_id = serializers.SerializerMethodField('get_provider_id')

    strategies = {
        'twitter': TwitterUserDataStrategy(),
        'facebook': FacebookUserDataStrategy(),
        'shareabouts': ShareaboutsUserDataStrategy()
    }
    default_strategy = DefaultUserDataStrategy()

    class Meta:
        model = models.User
        exclude = ('first_name', 'last_name', 'email', 'password', 'is_staff', 'is_active', 'is_superuser', 'last_login', 'date_joined', 'user_permissions')

    def get_strategy(self, obj):
        for social_auth in obj.social_auth.all():
            provider = social_auth.provider
            if provider in self.strategies:
                return social_auth.extra_data, self.strategies[provider]

        return None, self.default_strategy

    def get_name(self, obj):
        user_data, strategy = self.get_strategy(obj)
        return strategy.extract_full_name(user_data)

    def get_avatar_url(self, obj):
        user_data, strategy = self.get_strategy(obj)
        return strategy.extract_avatar_url(user_data)

    def get_provider_type(self, obj):
        for social_auth in obj.social_auth.all():
            return social_auth.provider
        else:
            return ''

    def get_provider_id(self, obj):
        for social_auth in obj.social_auth.all():
            return social_auth.uid
        else:
            return None

    def to_native(self, obj):
        return {
            "name": self.get_name(obj),
            "avatar_url": self.get_avatar_url(obj),
            "provider_type": self.get_provider_type(obj),
            "provider_id": self.get_provider_id(obj),
            "id": obj.id,
            "username": obj.username
        } if obj else {}


class SimpleUserSerializer (BaseUserSerializer):
    """
    Generates a partial user representation, for use as submitter data in bulk
    data calls.
    """
    class Meta (BaseUserSerializer.Meta):
        exclude = BaseUserSerializer.Meta.exclude + ('groups',)

class UserSerializer (BaseUserSerializer):
    """
    Generates a partial user representation, for use as submitter data in API
    calls.
    """
    class Meta (BaseUserSerializer.Meta):
        exclude = BaseUserSerializer.Meta.exclude + ('groups',)

class FullUserSerializer (BaseUserSerializer):
    """
    Generates a representation of the current user. Since it's only for the
    current user, it should have all the user's information on it (all that
    the user would need).
    """
    groups = GroupSerializer(many=True, source='_groups', read_only=True)

    class Meta (BaseUserSerializer.Meta):
        pass

    def to_native(self, obj):
        data = super(FullUserSerializer, self).to_native(obj)
        if obj:
            group_field = self.base_fields['groups']
            group_field.initialize(parent=self, field_name='groups')
            data['groups'] = group_field.field_to_native(obj, 'groups')
        return data


# DataSet place set serializer
class DataSetPlaceSetSummarySerializer (serializers.HyperlinkedModelSerializer):
    length = serializers.IntegerField(source='places_length')
    url = DataSetPlaceSetIdentityField()

    class Meta:
        model = models.DataSet
        fields = ('length', 'url')

    def get_place_counts(self, obj):
        """
        Return a dictionary whose keys are dataset ids and values are the
        corresponding count of places in that dataset.
        """
        # This will currently do a query for every dataset, not a single query
        # for all datasets. Generally a bad idea, but not a huge problem
        # considering the number of datasets at the moment. In the future,
        # we should perhaps use some kind of many_to_native function.

        # if self.many:
        #     include_invisible = INCLUDE_INVISIBLE_PARAM in self.context['request'].GET
        #     places = models.Place.objects.filter(dataset__in=obj)
        #     if not include_invisible:
        #         places = places.filter(visible=True)

        #     # Unset any default ordering
        #     places = places.order_by()

        #     places = places.values('dataset').annotate(length=Count('dataset'))
        #     return dict([(place['dataset'], place['length']) for place in places])

        # else:
        include_invisible = INCLUDE_INVISIBLE_PARAM in self.context['request'].GET
        places = obj.places
        if not include_invisible:
            places = places.filter(visible=True)
        return {obj.pk: places.count()}

    def to_native(self, obj):
        place_count_map = self.get_place_counts(obj)
        obj.places_length = place_count_map.get(obj.pk, 0)
        data = super(DataSetPlaceSetSummarySerializer, self).to_native(obj)
        return data


# DataSet submission set serializer
class DataSetSubmissionSetSummarySerializer (serializers.HyperlinkedModelSerializer):
    length = serializers.IntegerField(source='submission_set_length')
    url = DataSetSubmissionSetIdentityField()

    class Meta:
        model = models.DataSet
        fields = ('length', 'url')

    def is_flag_on(self, flagname):
        request = self.context['request']
        param = request.GET.get(flagname, 'false')
        return param.lower() not in ('false', 'no', 'off')

    def get_submission_sets(self, dataset):
        include_invisible = self.is_flag_on(INCLUDE_INVISIBLE_PARAM)
        submission_sets = defaultdict(list)
        for submission in dataset.submissions.all():
            if include_invisible or submission.visible:
                set_name = submission.set_name
                submission_sets[set_name].append(submission)
        return {dataset.id: submission_sets}

    def to_native(self, obj):
        request = self.context['request']
        submission_sets_map = self.get_submission_sets(obj)
        sets = submission_sets_map.get(obj.id, {})
        summaries = {}
        for set_name, submission_set in sets.iteritems():
            # Ensure the user has read permission on the submission set.
            user = getattr(request, 'user', None)
            client = getattr(request, 'client', None)
            dataset = obj
            if not check_data_permission(user, client, 'retrieve', dataset, set_name):
                continue

            obj.submission_set_name = set_name
            obj.submission_set_length = len(submission_set)
            summaries[set_name] = super(DataSetSubmissionSetSummarySerializer, self).to_native(obj)
        return summaries


class SubmittedThingSerializer (ActivityGenerator, DataBlobProcessor):
    def is_flag_on(self, flagname):
        request = self.context['request']
        param = request.GET.get(flagname, 'false')
        return param.lower() not in ('false', 'no', 'off')

    def restore_fields(self, data, files):
        """
        Converts a dictionary of data into a dictionary of deserialized fields.
        """
        result = super(SubmittedThingSerializer, self).restore_fields(data, files)

        if 'submitter' not in data:
            # If the thing exists already, use the existing submitter
            if hasattr(self, 'object') and self.object is not None:
                result['submitter'] = self.object.submitter

            # Otherwise, set the submitter to the current user
            else:
                request = self.context.get('request')
                if request and request.user.is_authenticated():
                    result['submitter'] = request.user

        return result


# Place serializers
class BasePlaceSerializer (SubmittedThingSerializer, serializers.ModelSerializer):
    geometry = GeometryField(format='wkt')
    attachments = AttachmentSerializer(read_only=True, many=True)
    submitter = SimpleUserSerializer(read_only=False)

    class Meta:
        model = models.Place

    def get_submission_sets(self, place):
        include_invisible = self.is_flag_on(INCLUDE_INVISIBLE_PARAM)
        submission_sets = defaultdict(list)
        for submission in place.submissions.all():
            if include_invisible or submission.visible:
                set_name = submission.set_name
                submission_sets[set_name].append(submission)
        return submission_sets

    def summary_to_native(self, set_name, submissions):
        return {
            'name': set_name,
            'length': len(submissions)
        }

    def get_submission_set_summaries(self, place):
        """
        Get a mapping from place id to a submission set summary dictionary.
        Get this for the entire dataset at once.
        """
        request = self.context['request']

        submission_sets = self.get_submission_sets(place)
        summaries = {}
        for set_name, submissions in submission_sets.iteritems():
            # Ensure the user has read permission on the submission set.
            user = getattr(request, 'user', None)
            client = getattr(request, 'client', None)
            dataset = getattr(request, 'get_dataset', lambda: None)()
            if not check_data_permission(user, client, 'retrieve', dataset, set_name):
                continue

            summaries[set_name] = self.summary_to_native(set_name, submissions)

        return summaries

    def set_to_native(self, set_name, submissions):
        serializer = SimpleSubmissionSerializer(submissions, many=True)
        serializer.initialize(parent=self, field_name=None)
        return serializer.data

    def get_detailed_submission_sets(self, place):
        """
        Get a mapping from place id to a detiled submission set dictionary.
        Get this for the entire dataset at once.
        """
        request = self.context['request']

        submission_sets = self.get_submission_sets(place)
        details = {}
        for set_name, submissions in submission_sets.iteritems():
            # Ensure the user has read permission on the submission set.
            user = getattr(request, 'user', None)
            client = getattr(request, 'client', None)
            dataset = getattr(request, 'get_dataset', lambda: None)()
            if not check_data_permission(user, client, 'retrieve', dataset, set_name):
                continue

            # We know that the submission datasets will be the same as the place
            # dataset, so say so and avoid an extra query for each.
            for submission in submissions:
                submission.dataset = place.dataset

            details[set_name] = self.set_to_native(set_name, submissions)

        return details

    def attachments_to_native(self, obj):
        return [AttachmentSerializer(a).data for a in obj.attachments.all()]

    def submitter_to_native(self, obj):
        return SimpleUserSerializer(obj.submitter).data if obj.submitter else None

    def to_native(self, obj):
        obj = self.ensure_obj(obj)
        fields = self.get_fields()

        data = {
            'id': obj.pk,  # = serializers.PrimaryKeyRelatedField(read_only=True)
            'geometry': str(obj.geometry or 'POINT(0 0)'),  # = GeometryField(format='wkt')
            'dataset': obj.dataset_id,  # = DataSetRelatedField()
            'attachments': self.attachments_to_native(obj),  # = AttachmentSerializer(read_only=True)
            'submitter': self.submitter_to_native(obj),
            'data': obj.data,
            'visible': obj.visible,
            'created_datetime': obj.created_datetime.isoformat() if obj.created_datetime else None,
            'updated_datetime': obj.updated_datetime.isoformat() if obj.updated_datetime else None,
        }

        if 'url' in fields:
            data['url'] = fields['url'].field_to_native(obj, 'pk')

        data = self.explode_data_blob(data)

        # data = super(PlaceSerializer, self).to_native(obj)

        # TODO: Put this flag value directly in to the serializer context,
        #       instead of relying on the request query parameters.
        if not self.is_flag_on(INCLUDE_SUBMISSIONS_PARAM):
            submission_sets_getter = self.get_submission_set_summaries
        else:
            submission_sets_getter = self.get_detailed_submission_sets

        data['submission_sets'] = submission_sets_getter(obj)

        if hasattr(obj, 'distance'):
            data['distance'] = str(obj.distance)

        return data

class SimplePlaceSerializer (BasePlaceSerializer):
    class Meta (BasePlaceSerializer.Meta):
        read_only_fields = ('dataset',)

class PlaceSerializer (BasePlaceSerializer, serializers.HyperlinkedModelSerializer):
    url = PlaceIdentityField()
    dataset = DataSetRelatedField()
    submitter = UserSerializer(read_only=False)

    class Meta (BasePlaceSerializer.Meta):
        pass

    def summary_to_native(self, set_name, submissions):
        url_field = SubmissionSetIdentityField()
        url_field.initialize(parent=self, field_name=None)
        set_url = url_field.field_to_native(submissions[0], None)

        return {
            'name': set_name,
            'length': len(submissions),
            'url': set_url,
        }

    def set_to_native(self, set_name, submissions):
        serializer = SubmissionSerializer(submissions, many=True)
        serializer.initialize(parent=self, field_name=None)
        return serializer.data

    def submitter_to_native(self, obj):
        return UserSerializer(obj.submitter).data if obj.submitter else None


# Submission serializers
class BaseSubmissionSerializer (SubmittedThingSerializer, serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    attachments = AttachmentSerializer(read_only=True, many=True)
    submitter = SimpleUserSerializer()

    class Meta:
        model = models.Submission
        exclude = ('set_name',)

class SimpleSubmissionSerializer (BaseSubmissionSerializer):
    class Meta (BaseSubmissionSerializer.Meta):
        read_only_fields = ('dataset', 'place')

class SubmissionSerializer (BaseSubmissionSerializer, serializers.HyperlinkedModelSerializer):
    url = SubmissionIdentityField()
    dataset = DataSetRelatedField()
    set = SubmissionSetRelatedField(source='*')
    place = PlaceRelatedField()
    submitter = UserSerializer()

    class Meta (BaseSubmissionSerializer.Meta):
        pass


# DataSet serializers
class BaseDataSetSerializer (EmptyModelSerializer, serializers.ModelSerializer):
    class Meta:
        model = models.DataSet

    def to_native(self, obj):
        obj = self.ensure_obj(obj)
        fields = self.get_fields()

        data = {
            'id': obj.pk,
            'slug': obj.slug,
            'display_name': obj.display_name,
            'owner': fields['owner'].field_to_native(obj, 'owner') if obj.owner_id else None,
        }

        if 'places' in fields:
            fields['places'].context = self.context
            data['places'] = fields['places'].field_to_native(obj, 'places')

        if 'submission_sets' in fields:
            fields['submission_sets'].context = self.context
            data['submission_sets'] = fields['submission_sets'].field_to_native(obj, 'submission_sets')

        if 'url' in fields:
            data['url'] = fields['url'].field_to_native(obj, 'url')

        if 'keys' in fields: data['keys'] = fields['keys'].field_to_native(obj, 'keys')
        if 'origins' in fields: data['origins'] = fields['origins'].field_to_native(obj, 'origins')
        if 'groups' in fields: data['groups'] = fields['groups'].field_to_native(obj, 'groups')
        if 'permissions' in fields: data['permissions'] = fields['permissions'].field_to_native(obj, 'permissions')

        # Construct a SortedDictWithMetaData to get the brosable API form
        ret = self._dict_class(data)
        ret.fields = self._dict_class()
        for field_name, field in fields.iteritems():
            default = getattr(field, 'get_default_value', lambda: None)()
            value = data.get(field_name, default)
            ret.fields[field_name] = self.augment_field(field, field_name, field_name, value)
        return ret

class SimpleDataSetSerializer (BaseDataSetSerializer, serializers.ModelSerializer):
    keys = ApiKeySerializer(many=True, read_only=False)
    origins = OriginSerializer(many=True, read_only=False)
    groups = SimpleGroupSerializer(many=True, read_only=False)
    permissions = DataSetPermissionSerializer(many=True, read_only=False)

    class Meta (BaseDataSetSerializer.Meta):
        pass

class DataSetSerializer (BaseDataSetSerializer, serializers.HyperlinkedModelSerializer):
    url = DataSetIdentityField()
    owner = UserRelatedField()

    places = DataSetPlaceSetSummarySerializer(source='*', read_only=True, many=True)
    submission_sets = DataSetSubmissionSetSummarySerializer(source='*', read_only=True, many=True)

    load_from_url = serializers.URLField(write_only=True, required=False)

    class Meta (BaseDataSetSerializer.Meta):
        pass

    def validate_load_from_url(self, attrs, source):
        url = attrs.get(source)
        if url:
            # Verify that at least a head request on the given URL is valid.
            import requests
            head_response = requests.head(url)
            if head_response.status_code != 200:
                raise ValidationError('There was an error reading from the URL: %s' % head_response.content)
        return attrs

    def save_object(self, obj, **kwargs):
        obj.save(**kwargs)

        # Load any bulk dataset definition supplied
        if hasattr(self, 'load_url') and self.load_url:
            # Somehow, make sure there's not already some loading going on.
            # Then, do:
            from .tasks import load_dataset_archive
            load_dataset_archive.apply_async(args=(obj.id, self.load_url,))


    def from_native(self, data, files=None):
        if data and 'load_from_url' in data:
            self.load_url = data.pop('load_from_url')
            if self.load_url and isinstance(self.load_url, list):
                self.load_url = unicode(self.load_url[0])
        return super(DataSetSerializer, self).from_native(data, files)


# Action serializer
class ActionSerializer (EmptyModelSerializer, serializers.ModelSerializer):
    target_type = serializers.SerializerMethodField('get_target_type')
    target = serializers.SerializerMethodField('get_target')

    class Meta:
        model = models.Action
        exclude = ('thing', 'source')

    def get_target_type(self, obj):
        try:
            if obj.thing.place is not None:
                return u'place'
        except models.Place.DoesNotExist:
            pass

        return obj.thing.submission.set_name

    def get_target(self, obj):
        try:
            if obj.thing.place is not None:
                serializer = PlaceSerializer(obj.thing.place)
            else:
                serializer = SubmissionSerializer(obj.thing.submission)
        except models.Place.DoesNotExist:
            serializer = SubmissionSerializer(obj.thing.submission)

        serializer.context = self.context
        return serializer.data


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
    num_pages = serializers.Field(source='paginator.num_pages')


class PaginatedResultsSerializer (pagination.BasePaginationSerializer):
    metadata = PaginationMetadataSerializer(source='*')
    many = True


class FeatureCollectionSerializer (PaginatedResultsSerializer):
    results_field = 'features'

    def to_native(self, obj):
        data = super(FeatureCollectionSerializer, self).to_native(obj)
        data['type'] = 'FeatureCollection'
        return data

