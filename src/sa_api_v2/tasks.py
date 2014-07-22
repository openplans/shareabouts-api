from __future__ import unicode_literals

from celery import shared_task
from django.test.client import RequestFactory
from django.utils.timezone import now
from .models import BulkDataRequest, BulkData
from .serializers import PlaceSerializer, SubmissionSerializer
from .renderers import CSVRenderer, JSONRenderer, GeoJSONRenderer


def feature_collection_wrapper(features):
    return {
        'type': 'FeatureCollection',
        'features': features
    }

def identity(results):
    return results

def generate_bulk_content(dataset, submission_set_name, format, **flags):
    renderer_classes = {
        'csv': CSVRenderer,
        'json': JSONRenderer,
        'geojson': GeoJSONRenderer
    }

    if submission_set_name == 'places':
        submissions = dataset.places.all()
        serializer = PlaceSerializer(submissions)
        finalize = feature_collection_wrapper
        if format == 'json': format = 'geojson'
    else:
        submissions = dataset.submissions.filter(parent__name=submission_set_name)
        serializer = SubmissionSerializer(submissions)
        finalize = identity

    r = RequestFactory().get('')
    for flag_attr, flag_val in flags.iteritems:
        if flag_val: r.GET[flag_attr] = 'true'

    serializer.context['request'] = r
    data = serializer.data
    data = finalize(data)
    renderer = renderer_classes.get(format)()
    content = renderer.render(data)
    return content

@shared_task
def get_bulk_data(request_id):
    request = BulkDataRequest(pk=request_id)

    # Generate the content
    content = generate_bulk_content(
        request.dataset,
        request.submission_set,
        request.format,
        include_submissions=request.include_submissions,
        include_private=request.include_private,
        include_invisible=request.include_invisible)

    # Store the information
    bulk_data = BulkData(
        request=request,
        content=content)
    bulk_data.save()

    request.fulfilled_at = now()
    request.save()
