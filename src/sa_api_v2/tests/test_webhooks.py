from django.test import TestCase
from django.test.client import RequestFactory
from django.core.urlresolvers import reverse
from django.core.cache import cache as django_cache
from django.core.files import File
from django.contrib.auth.models import AnonymousUser
import base64
import json
import mock
import responses
from io import StringIO
from ..models import User, DataSet, Place, Submission, Attachment, Group, Webhook
from ..cache import cache_buffer
from ..apikey.models import ApiKey
from ..apikey.auth import KEY_HEADER
from ..cors.models import Origin
from ..views import (PlaceInstanceView, PlaceListView, SubmissionInstanceView,
    SubmissionListView, DataSetSubmissionListView, DataSetInstanceView,
    DataSetListView, AttachmentListView, ActionListView, requests)


class APITestMixin (object):
    def assertStatusCode(self, response, *expected):
        self.assertIn(response.status_code, expected,
            'Status code not in %s response: (%s) %s' %
            (expected, response.status_code, response.rendered_content))


class TestPlaceListView (APITestMixin, TestCase):
    def setUp(self):
        cache_buffer.reset()
        django_cache.clear()

        self.owner = User.objects.create_user(username='aaron', password='123', email='abc@example.com')
        self.submitter = User.objects.create_user(username='mjumbe', password='456', email='123@example.com')
        self.dataset = DataSet.objects.create(slug='ds', owner=self.owner)
        self.place = Place.objects.create(
          dataset=self.dataset,
          geometry='POINT(2 3)',
          submitter=self.submitter,
          data=json.dumps({
            'type': 'ATM',
            'name': 'K-Mart',
            'private-secrets': 42
          }),
        )
        self.invisible_place = Place.objects.create(
          dataset=self.dataset,
          geometry='POINT(3 4)',
          submitter=self.submitter,
          visible=False,
          data=json.dumps({
            'type': 'ATM',
            'name': 'Walmart',
          }),
        )
        self.submissions = [
          Submission.objects.create(place=self.place, set_name='comments', dataset=self.dataset, data='{}'),
          Submission.objects.create(place=self.place, set_name='comments', dataset=self.dataset, data='{}'),
          Submission.objects.create(place=self.place, set_name='likes', dataset=self.dataset, data='{}'),
          Submission.objects.create(place=self.place, set_name='likes', dataset=self.dataset, data='{}'),
          Submission.objects.create(place=self.place, set_name='likes', dataset=self.dataset, data='{}'),
        ]

        self.ds_origin = Origin.objects.create(pattern='http://openplans.github.com', dataset=self.dataset)

        dataset2 = DataSet.objects.create(slug='ds2', owner=self.owner)
        place2 = Place.objects.create(
          dataset=dataset2,
          geometry='POINT(3 4)',
        )

        self.apikey = ApiKey.objects.create(key='abc', dataset=self.dataset)

        self.request_kwargs = {
          'owner_username': self.owner.username,
          'dataset_slug': self.dataset.slug
        }

        self.factory = RequestFactory()
        self.path = reverse('place-list', kwargs=self.request_kwargs)
        self.view = PlaceListView.as_view()

    def tearDown(self):
        User.objects.all().delete()
        DataSet.objects.all().delete()
        Place.objects.all().delete()
        Submission.objects.all().delete()
        ApiKey.objects.all().delete()

        cache_buffer.reset()
        django_cache.clear()

    @responses.activate
    def test_POST_response(self):
        Webhook.objects.create(
            dataset=self.dataset,
            submission_set='places',
            url='http://www.example.com/')

        responses.add(responses.POST, "http://www.example.com/",
                      body='{}', content_type="application/json")

        place_data = json.dumps({
            'properties': {
                'submitter_name': 'Andy',
                'type': 'Park Bench',
                'private-secrets': 'The mayor loves this bench',
            },
            'type': 'Feature',
            'geometry': {"type": "Point", "coordinates": [-73.99, 40.75]}
        })

        #
        # View should create the place when owner is authenticated
        #
        request = self.factory.post(self.path, data=place_data, content_type='application/json')
        request.META[KEY_HEADER] = self.apikey.key

        response = self.view(request, **self.request_kwargs)

        # Check that the request was successful
        self.assertStatusCode(response, 201)
        self.assertEqual(len(responses.calls), 1)
