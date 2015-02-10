from __future__ import unicode_literals

import requests
import ujson as json
from celery import shared_task
from celery.result import AsyncResult
from django.db import transaction
from django.test.client import RequestFactory
from django.utils.timezone import now
from itertools import chain
from social.apps.django_app.default.models import UserSocialAuth
from .models import DataSnapshotRequest, DataSnapshot, DataSet, User
from .serializers import SimplePlaceSerializer, SimpleSubmissionSerializer, SimpleDataSetSerializer
from .renderers import CSVRenderer, JSONRenderer, GeoJSONRenderer

import logging
log = logging.getLogger(__name__)


# =========================================================
# Generating snapshots
#

def generate_bulk_content(dataset, submission_set_name, **flags):
    renderer_classes = {
        'csv': CSVRenderer,
        'json': GeoJSONRenderer if submission_set_name == 'places' else JSONRenderer
    }

    if submission_set_name == 'places':
        submissions = dataset.places.all()
        serializer = SimplePlaceSerializer(submissions, many=True)
    else:
        submissions = dataset.submissions.filter(set_name=submission_set_name)
        serializer = SimpleSubmissionSerializer(submissions, many=True)

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


# =========================================================
# Loading a dataset
#

def get_twitter_extra_data(user_data):
    return {
        'id': user_data.get('provider_id'),
        'profile_image_url': user_data.get('avatar_url'),
        'access_token': {
            'screen_name': user_data.get('username'),
            'oauth_token_secret': 'abc',
            'oauth_token': '123',
            'user_id': user_data.get('provider_id')
        },
        'name': user_data.get('name')
    }

def get_facebook_extra_data(user_data):
    return {
        'access_token': 'abc123',
        'picture': {
            "data": {
                "url": user_data.get('avatar_url'),
            }
        },
        "id": user_data.get('provider_id'),
        "name": user_data.get('name'),
    }

def get_or_create_user(user_data, users_map):
    if user_data is None:
        return

    # Check whether the user is already cached
    username = user_data.get('username')
    user = users_map.get(username)
    if user:
        return user

    # Create and cache the user
    user = User.objects.create(username=username, password='!')
    users_map[username] = user

    # Create a social auth entry for the user, if appropriate
    if 'provider_type' in user_data and 'provider_id' in user_data:
        UserSocialAuth.objects.create(
            user=user,
            provider=user_data.get('provider_type'),
            uid=user_data.get('provider_id'),
            extra_data=
                get_twitter_extra_data(user_data)
                if user_data.get('provider_type') == 'twitter' else
                get_facebook_extra_data(user_data)
        )

def preload_users(data):
    """
    Construct a mapping from usernames to users for Users that already exist
    in the API.
    """
    usernames = set()

    def collect_username(data):
        submitter_data = data.get('submitter')
        if submitter_data:
            usernames.add(submitter_data.get('username'))

    for place_data in data.get('features', []):
        collect_username(place_data['properties'])
        for _, submissions_data in place_data['properties'].get('submission_sets', {}).iteritems():
            for submission_data in submissions_data:
                collect_username(submission_data)

    users = User.objects.filter(username__in=usernames)
    users_map = dict([(user.username, user) for user in users])
    return users_map

def list_errors(errors):
    errors_list = []
    for key, l in errors.items():
        if isinstance(l, list):
            for msg in l:
                errors_list.append('%s: %s' % (key, unicode(msg)))
        else:
            msg = l
            errors_list.append('%s: %s' % (key, unicode(msg)))
    return errors_list


@shared_task
def load_dataset_archive(dataset_id, archive_url):
    dataset = DataSet.objects.get(id=dataset_id)

    try:
        archive_response = requests.get(archive_url)
    except:
        pass

    if archive_response.status_code == 200:
        data = archive_response.json()

        # Preload users
        users_map = preload_users(data)

        with transaction.atomic():
            # Construct the dataset from metadata
            metadata = data.get('metadata')
            if metadata:
                metadata.pop('id', None)
                metadata.pop('owner', None)
                serializer = SimpleDataSetSerializer(dataset, data=data.get('metadata'))
                assert serializer.is_valid, list_errors(serializer.errors)
                serializer.save()

            # Construct each place and submission individually
            for place_data in data.get('features'):
                place_data.pop('id', None)
                place_data['properties'].pop('dataset', None)
                place_data['properties'].pop('created_datetime', None)
                place_data['properties'].pop('updated_datetime', None)
                submission_sets_data = place_data['properties'].pop('submission_sets', None)
                submitter_data = place_data['properties'].pop('submitter', None)

                serializer = SimplePlaceSerializer(data=place_data)
                assert serializer.is_valid(), list_errors(serializer.errors)
                place = serializer.object
                place.dataset = dataset
                place.submitter = get_or_create_user(submitter_data, users_map)
                place.save(silent=True, reindex=False)

                for set_name, submissions_data in submission_sets_data.iteritems():
                    for submission_data in submissions_data:
                        submission_data.pop('id', None)
                        submission_data.pop('place', None)
                        submission_data.pop('dataset', None)
                        submission_data.pop('attachments', None)
                        submission_data.pop('created_datetime', None)
                        submission_data.pop('updated_datetime', None)
                        submitter_data = submission_data.pop('submitter', None)

                        serializer = SimpleSubmissionSerializer(data=submission_data)
                        assert serializer.is_valid(), list_errors(serializer.errors)
                        submission = serializer.object
                        submission.set_name = set_name
                        submission.place = place
                        submission.dataset = dataset
                        submission.submitter = get_or_create_user(submitter_data, users_map)
                        submission.save(silent=True, reindex=False)

            dataset.reindex()

            # Load meta-data like permissions and such
            # metadata = data.get('metadata')
            # for permission_data in metadata.get('permissions'):

