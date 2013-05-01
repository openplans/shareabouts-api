"""
DjangoRestFramework resources for the Shareabouts REST API.
"""
import ujson as json
from rest_framework import serializers

from . import models
from . import utils
from . import cache

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
        known_fields.update(['submissions'])

        # And allow an arbitrary value field named 'data' (don't let the
        # data blob get in the way).
        known_fields.remove('data')

        for key in data:
            if key in known_fields:
                data_copy[key] = data[key]
            else:
                blob[key] = data[key]

        data_copy['data'] = json.dumps(blob)

        return super(DataBlobProcessor, self).restore_fields(data_copy, files)

    def to_native(self, obj):
        data = super(DataBlobProcessor, self).to_native(obj)
        blob = data.pop('data')
        data.update(json.loads(blob))
        return data


class PlaceSerializer (DataBlobProcessor, serializers.ModelSerializer):
    class Meta:
        model = models.Place

