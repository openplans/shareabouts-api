from __future__ import unicode_literals

from celery import shared_task
from celery.result import AsyncResult
from django.db import transaction
from django.test.client import RequestFactory
from django.utils.timezone import now
from .models import DataSnapshotRequest, DataSnapshot, DataSet
from .serializers import PlaceSerializer, SubmissionSerializer
from .renderers import CSVRenderer, JSONRenderer, GeoJSONRenderer

import logging
log = logging.getLogger(__name__)


def generate_bulk_content(dataset, submission_set_name, **flags):
    renderer_classes = {
        'csv': CSVRenderer,
        'json': GeoJSONRenderer if submission_set_name == 'places' else JSONRenderer
    }

    if submission_set_name == 'places':
        submissions = dataset.places.all()
        serializer = PlaceSerializer(submissions)
    else:
        submissions = dataset.submissions.filter(set_name=submission_set_name)
        serializer = SubmissionSerializer(submissions)

    # Construct a request for the serializer context
    r_data = {}
    for flag_attr, flag_val in flags.iteritems():
        if flag_val: r_data[flag_attr] = 'true'
    r = RequestFactory().get('', data=r_data)
    r.get_dataset = lambda: dataset

    # Render the data in each format
    serializer.context['request'] = r
    data = serializer.data
    content = {}
    for format, renderer_class in renderer_classes.items():
        renderer = renderer_class()
        content[format] = renderer.render(data)
    return content

@shared_task
def store_bulk_data(request_id):
    task_id = store_bulk_data.request.id
    log.info('Creating a snapshot request with task id %s' % (task_id,))

    datarequest = DataSnapshotRequest.objects.get(pk=request_id)
    datarequest.guid = task_id
    datarequest.save()

    # Generate the content
    content = generate_bulk_content(
        datarequest.dataset,
        datarequest.submission_set,
        include_submissions=datarequest.include_submissions,
        include_private=datarequest.include_private,
        include_invisible=datarequest.include_invisible)

    # Store the information
    bulk_data = DataSnapshot(
        request=datarequest,
        csv=content['csv'],
        json=content['json'])
    bulk_data.save()

    datarequest.fulfilled_at = now()
    datarequest.save()

    return task_id

@shared_task
def bulk_data_status_update(uuid):
    """
    A callback task that updates the status of a data snapshot request, whether
    successful or not.
    """
    taskresult = AsyncResult(uuid)
    datarequest = DataSnapshotRequest.objects.get(guid=uuid)
    datarequest.status = taskresult.status.lower()
    datarequest.save()

@shared_task
def clone_related_dataset_data(orig_dataset_id, new_dataset_id):
    qs = DataSet.objects.select_related('owner')\
        .filter(id__in=(orig_dataset_id, new_dataset_id))\
        .prefetch_related('things',
                          'things__place',
                          'things__place__dataset',
                          'things__place__submitter',
                          'things__place__submissions',
                          'things__place__submissions__dataset',
                          'things__place__submissions__submitter',
                          'permissions',
                          'groups',
                          'groups__submitters',
                          'groups__permissions',
                          'keys',
                          'keys__permissions',
                          'origins',
                          'origins__permissions',
                          )
    datasets = list(qs)
    if datasets[0].id == orig_dataset_id:
        orig_dataset, new_dataset = datasets
    else:
        new_dataset, orig_dataset = datasets

    with transaction.atomic():
        orig_dataset.clone_related(onto=new_dataset)