from __future__ import unicode_literals

from celery import shared_task
from django.utils.timezone import now
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.base import ContentFile
from django.core.files.storage import DefaultStorage
from .models import DataSet
from .serializers import PlaceSerializer, SubmissionSerializer
from .renderers import CSVRenderer, JSONRenderer, GeoJSONRenderer
from .cache import DataSetCache


def feature_collection_wrapper(features):
    return {
        'type': 'FeatureCollection',
        'features': features
    }

def identity(results):
    return results

def generate_bulk_content(dataset_id, submission_set_name, format, **flags):
    renderer_classes = {
        'csv': CSVRenderer,
        'json': JSONRenderer,
        'geojson': GeoJSONRenderer
    }

    dataset = DataSet.objects.get(pk=dataset_id)

    if submission_set_name == 'places':
        submissions = dataset.places.all()
        serializer = PlaceSerializer(submissions)
        finalize = feature_collection_wrapper
        if format == 'json': format = 'geojson'
    else:
        submissions = dataset.submissions.filter(parent__name=submission_set_name)
        serializer = SubmissionSerializer()
        finalize = identity

    data = serializer.data
    data = finalize(data)
    renderer = renderer_classes.get(format)()
    content = renderer.render(data)
    return content

@shared_task
def get_bulk_data(dataset_id, submission_set_name, format, **flags):
    # Generate the content
    content = generate_bulk_content(dataset_id, submission_set_name, format, **flags)

    # Cache the information
    ds_cache = DataSetCache()
    cache_key = ds_cache.get_cache_key(dataset_id, submission_set_name, format, **flags)
    cache.set(cache_key, {
        'content': content,
        'generated': })
