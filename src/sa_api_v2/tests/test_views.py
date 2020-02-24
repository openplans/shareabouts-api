from django.test import TestCase
from django.test.client import RequestFactory
from django.core.urlresolvers import reverse
from django.core.cache import cache as django_cache
from django.core.files import File
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.contrib.gis import geos
import base64
import csv
import json
import mock
import unittest
from io import StringIO
from ..models import User, DataSet, Place, Submission, Attachment, Action, Group, DataIndex
from ..cache import cache_buffer
from ..apikey.models import ApiKey
from ..apikey.auth import KEY_HEADER
from ..cors.models import Origin
from ..views import (PlaceInstanceView, PlaceListView, SubmissionInstanceView,
    SubmissionListView, DataSetSubmissionListView, DataSetInstanceView,
    DataSetListView, AttachmentListView, ActionListView)
from ..serializers import FeatureCollectionPagination


class APITestMixin (object):
    def assertStatusCode(self, response, *expected):
        self.assertIn(response.status_code, expected,
            'Status code not in %s response: (%s) %s' %
            (expected, response.status_code, response.rendered_content))


class TestPlaceInstanceView (APITestMixin, TestCase):
    def setUp(self):
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
        f = StringIO(u'This is test content in a "file"')
        f.name = 'myfile.txt'
        f.size = 20
        self.attachments = Attachment.objects.create(
            file=File(f, 'myfile.txt'), name='my_file_name', thing=self.place)
        self.submissions = [
          Submission.objects.create(place=self.place, set_name='comments', dataset=self.dataset, data='{"foo": 3}'),
          Submission.objects.create(place=self.place, set_name='comments', dataset=self.dataset, data='{"foo": 3}'),
          Submission.objects.create(place=self.place, set_name='comments', dataset=self.dataset, data='{"foo": 3}', visible=False),
          Submission.objects.create(place=self.place, set_name='likes', dataset=self.dataset, data='{"bar": 3}'),
          Submission.objects.create(place=self.place, set_name='likes', dataset=self.dataset, data='{"bar": 3}'),
          Submission.objects.create(place=self.place, set_name='likes', dataset=self.dataset, data='{"bar": 3}'),
          Submission.objects.create(place=self.place, set_name='likes', dataset=self.dataset, data='{"bar": 3}', visible=False),
        ]

        self.invisible_place = Place.objects.create(
          dataset=self.dataset,
          geometry='POINT(3 4)',
          submitter=self.submitter,
          visible=False,
          data=json.dumps({
            'type': 'ATM',
            'name': 'K-Mart',
          }),
        )

        self.apikey = ApiKey.objects.create(key='abc', dataset=self.dataset)
        self.ds_origin = Origin.objects.create(pattern='http://openplans.github.com', dataset=self.dataset)

        self.request_kwargs = {
          'owner_username': self.owner.username,
          'dataset_slug': self.dataset.slug,
          'place_id': str(self.place.id)
        }

        self.invisible_request_kwargs = {
          'owner_username': self.owner.username,
          'dataset_slug': self.dataset.slug,
          'place_id': str(self.invisible_place.id)
        }

        self.factory = RequestFactory()
        self.path = reverse('place-detail', kwargs=self.request_kwargs)
        self.invisible_path = reverse('place-detail', kwargs=self.invisible_request_kwargs)
        self.view = PlaceInstanceView.as_view()

        cache_buffer.reset()
        django_cache.clear()

    def tearDown(self):
        User.objects.all().delete()
        DataSet.objects.all().delete()
        Place.objects.all().delete()
        Submission.objects.all().delete()
        ApiKey.objects.all().delete()
        Action.objects.all().delete()

        cache_buffer.reset()
        django_cache.clear()

    def test_OPTIONS_response(self):
        request = self.factory.options(self.path)
        response = self.view(request, **self.request_kwargs)

        # Check that the request was successful
        self.assertStatusCode(response, 200)

    def test_GET_response(self):
        request = self.factory.get(self.path)
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 200)

        # Check that it's a feature
        self.assertIn('type', data)
        self.assertIn('geometry', data)
        self.assertIn('properties', data)
        self.assertIn('id', data)

        # Check that data attribute is not present
        self.assertNotIn('data', data['properties'])

        # Check that the data attributes have been incorporated into the
        # properties
        self.assertEqual(data['properties'].get('type'), 'ATM')
        self.assertEqual(data['properties'].get('name'), 'K-Mart')

        # Check that the geometry attribute looks right
        self.assertIsInstance(data['geometry'], dict)
        self.assertIn('type', data['geometry'])
        self.assertIn('coordinates', data['geometry'])

        # Check that the appropriate attributes are in the properties
        self.assertIn('url', data['properties'])
        self.assertIn('dataset', data['properties'])
        self.assertIn('attachments', data['properties'])
        self.assertIn('submission_sets', data['properties'])
        self.assertIn('submitter', data['properties'])

        # Check that the URL is right
        self.assertEqual(data['properties']['url'],
            'http://testserver' + reverse('place-detail', args=[
                self.owner.username, self.dataset.slug, self.place.id]))

        # Check that the submission sets look right
        self.assertEqual(len(data['properties']['submission_sets']), 2)
        self.assertIn('comments', list(data['properties']['submission_sets'].keys()))
        self.assertIn('likes', list(data['properties']['submission_sets'].keys()))
        self.assertNotIn('applause', list(data['properties']['submission_sets'].keys()))

        # Check that the submitter looks right
        self.assertIsNotNone(data['properties']['submitter'])
        self.assertIn('id', data['properties']['submitter'])
        self.assertIn('name', data['properties']['submitter'])
        self.assertIn('avatar_url', data['properties']['submitter'])

        # Check that only the visible comments were counted
        self.assertEqual(data['properties']['submission_sets']['comments']['length'], 2)

        # --------------------------------------------------

        #
        # View should include submissions when requested
        #
        request = self.factory.get(self.path + '?include_submissions')
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the submission_sets are in the properties
        self.assertIn('submission_sets', data['properties'])

        # Check that the submission sets look right
        comments_set = data['properties']['submission_sets'].get('comments')
        self.assertIsInstance(comments_set, list)
        self.assertEqual(len(comments_set), 2)
        self.assertIn('foo', comments_set[0])
        self.assertTrue(all([comment['visible'] for comment in comments_set]))

        # --------------------------------------------------

        #
        # View should not include submissions when explicitly false
        #
        request = self.factory.get(self.path + '?include_submissions=false')
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the submission_sets are in the properties
        self.assertIn('submission_sets', data['properties'])

        # Check that the submission sets look right
        comments_set = data['properties']['submission_sets'].get('comments')
        self.assertIsInstance(comments_set, dict)
        self.assertIn('length', comments_set)
        self.assertEqual(comments_set['length'], 2)

        # --------------------------------------------------

        #
        # View should include invisible submissions when requested and allowed
        #

        # - - - - - Not logged in  - - - - - - - - - - - - -
        request = self.factory.get(self.path + '?include_submissions&include_invisible')
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        self.assertStatusCode(response, 401)

        # - - - - - Authenticated as owner - - - - - - - - -
        request = self.factory.get(self.path + '?include_submissions&include_invisible')
        request.user = self.owner
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the submission_sets are in the properties
        self.assertIn('submission_sets', data['properties'])

        # Check that the invisible submissions are included
        comments_set = data['properties']['submission_sets'].get('comments')
        self.assertEqual(len(comments_set), 3)
        self.assertTrue(not all([comment['visible'] for comment in comments_set]))

    def test_GET_response_with_attachment(self):
        request = self.factory.get(self.path)
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the attachment looks right
        self.assertIn('file', data['properties']['attachments'][0])
        self.assertIn('name', data['properties']['attachments'][0])

        self.assertEqual(len(data['properties']['attachments']), 1)
        self.assertEqual(data['properties']['attachments'][0]['name'], 'my_file_name')

        a = self.place.attachments.all()[0]
        self.assertEqual(a.file.read(), b'This is test content in a "file"')

    def test_new_attachment_clears_GET_cache(self):
        request = self.factory.get(self.path)
        response = self.view(request, **self.request_kwargs)
        initial_data = json.loads(response.rendered_content)

        # Create a dummy view instance so that we can call get_cache_key
        temp_view = PlaceInstanceView()
        temp_view.request = request

        # Check that the response is cached
        cache_key = temp_view.get_cache_key(request)
        self.assertIsNotNone(django_cache.get(cache_key))

        # Save another attachment
        Attachment.objects.create(file=None, name='my_new_file_name', thing=self.place)
        cache_buffer.flush()

        # Check that the response cache was cleared
        cache_key = temp_view.get_cache_key(request)
        self.assertIsNone(django_cache.get(cache_key))

        # Check that the we get a different response
        response = self.view(request, **self.request_kwargs)
        new_data = json.loads(response.rendered_content)
        self.assertNotEqual(initial_data, new_data)

    def test_GET_response_with_private_data(self):
        #
        # View should not return private data normally
        #
        request = self.factory.get(self.path)
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 200)

        # Check that the private data is not in the properties
        self.assertNotIn('private-secrets', data['properties'])

        # --------------------------------------------------

        #
        # View should 401 when not allowed to request private data (not authenticated)
        #
        request = self.factory.get(self.path + '?include_private')
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was restricted
        self.assertStatusCode(response, 401)

        # --------------------------------------------------

        #
        # View should 403 when not allowed to request private data (api key)
        #
        request = self.factory.get(self.path + '?include_private')
        request.META[KEY_HEADER] = self.apikey.key
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was restricted
        self.assertStatusCode(response, 403)

        # --------------------------------------------------

        #
        # View should 403 when not allowed to request private data (origin)
        #
        request = self.factory.get(self.path + '?include_private')
        request.META['HTTP_ORIGIN'] = self.ds_origin.pattern
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was restricted
        self.assertStatusCode(response, 403)

        # --------------------------------------------------

        #
        # View should 403 when not allowed to request private data (not owner)
        #
        request = self.factory.get(self.path + '?include_private')
        request.user = User.objects.create(username='new_user', password='password')
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was restricted
        self.assertStatusCode(response, 403)

        # --------------------------------------------------

        #
        # View should return private data when owner is logged in (Session Auth)
        #
        request = self.factory.get(self.path + '?include_private')
        request.user = self.owner
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 200)

        # Check that the private data is in the properties
        self.assertIn('private-secrets', data['properties'])

        # --------------------------------------------------

        #
        # View should return private data when owner is logged in (Basic Auth)
        #
        request = self.factory.get(self.path + '?include_private')
        credentials = ':'.join([self.owner.username, '123']).encode()
        request.META['HTTP_AUTHORIZATION'] = 'Basic ' + base64.b64encode(credentials).decode()
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 200)

        # Check that the private data is in the properties
        self.assertIn('private-secrets', data['properties'])

    def test_GET_response_with_invisible_data(self):
        #
        # View should not return invisible data normally
        #
        request = self.factory.get(self.invisible_path)
        response = self.view(request, **self.invisible_request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 400)

        # --------------------------------------------------

        #
        # View should 401 when not allowed to request private data (not authenticated)
        #
        request = self.factory.get(self.invisible_path + '?include_invisible')
        response = self.view(request, **self.invisible_request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was restricted
        self.assertStatusCode(response, 401)

        # --------------------------------------------------

        #
        # View should 403 when not allowed to request private data (api key)
        #
        request = self.factory.get(self.invisible_path + '?include_invisible')
        request.META[KEY_HEADER] = self.apikey.key
        response = self.view(request, **self.invisible_request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was restricted
        self.assertStatusCode(response, 403)

        # --------------------------------------------------

        #
        # View should 403 when not allowed to request private data (api key)
        #
        request = self.factory.get(self.invisible_path + '?include_invisible')
        request.META['HTTP_ORIGIN'] = self.ds_origin.pattern
        response = self.view(request, **self.invisible_request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was restricted
        self.assertStatusCode(response, 403)

        # --------------------------------------------------

        #
        # View should 403 when not allowed to request private data (not owner)
        #
        request = self.factory.get(self.invisible_path + '?include_invisible')
        request.user = User.objects.create(username='new_user', password='password')
        response = self.view(request, **self.invisible_request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was restricted
        self.assertStatusCode(response, 403)

        # --------------------------------------------------

        #
        # View should return private data when owner is logged in (Session Auth)
        #
        request = self.factory.get(self.invisible_path + '?include_invisible')
        request.user = self.owner
        response = self.view(request, **self.invisible_request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 200)

        # --------------------------------------------------

        #
        # View should return private data when owner is logged in (Basic Auth)
        #
        request = self.factory.get(self.invisible_path + '?include_invisible')
        credentials = ':'.join([self.owner.username, '123']).encode()
        request.META['HTTP_AUTHORIZATION'] = 'Basic ' + base64.b64encode(credentials).decode()
        response = self.view(request, **self.invisible_request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 200)

        # --------------------------------------------------

        #
        # View should 400 when owner is logged in but doesn't request invisible
        #
        request = self.factory.get(self.invisible_path)
        request.user = self.owner
        response = self.view(request, **self.invisible_request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 400)

    def test_GET_invalid_url(self):
        # Make sure that we respond with 404 if a place_id is supplied, but for
        # the wrong dataset or owner.
        request_kwargs = {
          'owner_username': 'mischevious_owner',
          'dataset_slug': self.dataset.slug,
          'place_id': self.place.id
        }

        path = reverse('place-detail', kwargs=request_kwargs)
        request = self.factory.get(path)
        response = self.view(request, **request_kwargs)

        self.assertStatusCode(response, 404)

    def test_GET_from_cache(self):
        path = reverse('place-detail', kwargs=self.request_kwargs)
        request = self.factory.get(path)

        # Check that we make a finite number of queries
        #
        # ---- Checking data access permissions:
        #
        # - SELECT requested dataset and owner
        # - SELECT dataset permissions
        # - SELECT keys
        # - SELECT key permissions
        # - SELECT origins
        # - SELECT origin permissions
        #
        # ---- Building the data
        #
        # - SELECT * FROM sa_api_place AS p
        #     JOIN sa_api_submittedthing AS t ON (p.submittedthing_ptr_id = t.id)
        #     JOIN sa_api_dataset AS ds ON (t.dataset_id = ds.id)
        #     JOIN auth_user as u1 ON (t.submitter_id = u1.id)
        #     JOIN auth_user as u2 ON (ds.owner_id = u2.id)
        #    WHERE t.id = <self.place.id>;
        #
        # - SELECT * FROM social_auth_usersocialauth
        #    WHERE user_id IN (<self.owner.id>)
        #
        # - SELECT * FROM sa_api_submission AS s
        #     JOIN sa_api_submittedthing AS t ON (s.submittedthing_ptr_id = t.id)
        #    WHERE s.parent_id IN (<self.comments.id>, <self.likes.id>, <self.applause.id>);
        #
        # - SELECT * FROM sa_api_attachment AS a
        #    WHERE a.thing_id IN (<[each submission id]>);
        #
        # - SELECT * FROM sa_api_attachment AS a
        #    WHERE a.thing_id IN (<self.place.id>);
        #
        with self.assertNumQueries(11):
            response = self.view(request, **self.request_kwargs)
            self.assertStatusCode(response, 200)

        path = reverse('place-detail', kwargs=self.request_kwargs)
        request = self.factory.get(path)

        # Check that this performs no more queries, since it's all cached
        with self.assertNumQueries(0):
            response = self.view(request, **self.request_kwargs)
            self.assertStatusCode(response, 200)

    def test_GET_from_cache_with_api_key(self):
        # Modify the dataset permissions
        ds_perm = self.dataset.permissions.all()[0]
        ds_perm.can_retrieve = False
        ds_perm.save()

        key_perm = self.apikey.permissions.all()[0]
        key_perm.can_retrieve = True
        key_perm.save()

        # Set up the initial request
        path = reverse('place-detail', kwargs=self.request_kwargs)
        request = self.factory.get(path)
        request.META[KEY_HEADER] = self.apikey.key

        # Check that we make a finite number of queries
        #
        # ---- Checking data access permissions:
        #
        # - SELECT requested dataset and owner
        # - SELECT dataset permissions
        # - SELECT keys
        # - SELECT key permissions
        # - SELECT origins
        # - SELECT origin permissions
        #
        # ---- Building the data
        #
        # - SELECT * FROM sa_api_place AS p
        #     JOIN sa_api_submittedthing AS t ON (p.submittedthing_ptr_id = t.id)
        #     JOIN sa_api_dataset AS ds ON (t.dataset_id = ds.id)
        #     JOIN auth_user as u1 ON (t.submitter_id = u1.id)
        #     JOIN auth_user as u2 ON (ds.owner_id = u2.id)
        #    WHERE t.id = <self.place.id>;
        #
        # - SELECT * FROM social_auth_usersocialauth
        #    WHERE user_id IN (<self.owner.id>)
        #
        # - SELECT * FROM sa_api_submission AS s
        #     JOIN sa_api_submittedthing AS t ON (s.submittedthing_ptr_id = t.id)
        #    WHERE s.parent_id IN (<self.comments.id>, <self.likes.id>, <self.applause.id>);
        #
        # - SELECT * FROM sa_api_attachment AS a
        #    WHERE a.thing_id IN (<[each submission id]>);
        #
        # - SELECT * FROM sa_api_attachment AS a
        #    WHERE a.thing_id IN (<self.place.id>);
        #
        with self.assertNumQueries(11):
            response = self.view(request, **self.request_kwargs)
            self.assertStatusCode(response, 200)

        path = reverse('place-detail', kwargs=self.request_kwargs)
        request = self.factory.get(path)
        request.META[KEY_HEADER] = self.apikey.key

        # Check that this performs no more queries, since it's all cached
        with self.assertNumQueries(0):
            response = self.view(request, **self.request_kwargs)
            self.assertStatusCode(response, 200)

    def test_GET_differently_from_cache_by_user_group(self):
        user = User.objects.create_user(username='temp_user', password='lkjasdf')
        group = Group.objects.create(dataset=self.dataset, name='mygroup')
        group.submitters.add(user)

        path = reverse('place-detail', kwargs=self.request_kwargs)
        anon_request = self.factory.get(path)
        anon_request.user = AnonymousUser()
        auth_request = self.factory.get(path)
        auth_request.user = User.objects.get(username=user.username)

        # Check that we make a finite number of queries
        #
        # ---- Checking data access permissions (only when authed):
        #
        # - SELECT requested dataset
        # - SELECT dataset permissions
        # - SELECT keys
        # - SELECT key permissions
        # - SELECT origins
        # - SELECT origin permissions
        #
        # ---- Building the data (each time)
        #
        # - SELECT * FROM sa_api_place AS p
        #     JOIN sa_api_submittedthing AS t ON (p.submittedthing_ptr_id = t.id)
        #     JOIN sa_api_dataset AS ds ON (t.dataset_id = ds.id)
        #     JOIN auth_user as u1 ON (t.submitter_id = u1.id)
        #     JOIN auth_user as u2 ON (ds.owner_id = u2.id)
        #    WHERE t.id = <self.place.id>;
        #
        # - SELECT * FROM social_auth_usersocialauth
        #    WHERE user_id IN (<self.owner.id>)
        #
        # - SELECT * FROM sa_api_submission AS s
        #     JOIN sa_api_submittedthing AS t ON (s.submittedthing_ptr_id = t.id)
        #    WHERE s.parent_id IN (<self.comments.id>, <self.likes.id>, <self.applause.id>);
        #
        # - SELECT * FROM sa_api_attachment AS a
        #    WHERE a.thing_id IN (<[each submission id]>);
        #
        # - SELECT * FROM sa_api_attachment AS a
        #    WHERE a.thing_id IN (<self.place.id>);
        #
        with self.assertNumQueries(16):
            response = self.view(anon_request, **self.request_kwargs)
            self.assertStatusCode(response, 200)
            response = self.view(auth_request, **self.request_kwargs)
            self.assertStatusCode(response, 200)

        path = reverse('place-detail', kwargs=self.request_kwargs)
        anon_request = self.factory.get(path)
        anon_request.user = AnonymousUser()
        auth_request = self.factory.get(path)
        auth_request.user = User.objects.get(username=user.username)

        # Check that this performs no more queries, since it's all cached
        with self.assertNumQueries(0):
            response = self.view(anon_request, **self.request_kwargs)
            self.assertStatusCode(response, 200)
            response = self.view(auth_request, **self.request_kwargs)
            self.assertStatusCode(response, 200)

    def test_DELETE_response(self):
        #
        # View should 401 when trying to delete when not authenticated
        #
        request = self.factory.delete(self.path)
        response = self.view(request, **self.request_kwargs)
        self.assertStatusCode(response, 401)

    def test_DELETE_response_with_apikey(self):
        #
        # View should delete the place when owner is authenticated
        #
        request = self.factory.delete(self.path)
        request.META[KEY_HEADER] = self.apikey.key
        response = self.view(request, **self.request_kwargs)

        # Check that the request was successful
        self.assertStatusCode(response, 204)

        # Check that no data was returned
        self.assertIsNone(response.data)

    def test_DELETE_response_with_origin(self):
        #
        # View should delete the place when owner is authenticated
        #
        request = self.factory.delete(self.path)
        request.META['HTTP_ORIGIN'] = self.ds_origin.pattern
        response = self.view(request, **self.request_kwargs)

        # Check that the request was successful
        self.assertStatusCode(response, 204)

        # Check that no data was returned
        self.assertIsNone(response.data)

    def test_PUT_with_silent_creates_no_activity(self):
        Action.objects.all().delete()
        assert Action.objects.all().count() == 0

        place_data = json.dumps({
          'type': 'Feature',
          'properties': {
            'type': 'Park Bench',
            'private-secrets': 'The mayor loves this bench',
            'submitter': None
          },
          'geometry': {"type": "Point", "coordinates": [-73.99, 40.75]},
        })

        request = self.factory.put(self.path, data=place_data, content_type='application/json', HTTP_X_SHAREABOUTS_SILENT='true')
        request.META[KEY_HEADER] = self.apikey.key
        response = self.view(request, **self.request_kwargs)
        self.assertStatusCode(response, 200)

        self.assertEqual(Action.objects.all().count(), 0)

    def test_PUT_response_as_owner(self):
        place_data = json.dumps({
          'type': 'Feature',
          'properties': {
            'type': 'Park Bench',
            'private-secrets': 'The mayor loves this bench',
            'submitter': None
          },
          'geometry': {"type": "Point", "coordinates": [-73.99, 40.75]},
        })

        #
        # View should 401 when trying to update when not authenticated
        #
        request = self.factory.put(self.path, data=place_data, content_type='application/json')
        response = self.view(request, **self.request_kwargs)
        self.assertStatusCode(response, 401)

        ## TODO: Use the SubmittedThingSerializer to implement the commented
        ##       out permission structure instead.
        ##

        #
        # View should update the place when client is authenticated (apikey)
        #
        request = self.factory.put(self.path, data=place_data, content_type='application/json')
        request.META[KEY_HEADER] = self.apikey.key
        response = self.view(request, **self.request_kwargs)
        self.assertStatusCode(response, 200)

        #
        # View should update the place when client is authenticated (origin)
        #
        request = self.factory.put(self.path, data=place_data, content_type='application/json')
        request.META['HTTP_ORIGIN'] = self.ds_origin.pattern
        response = self.view(request, **self.request_kwargs)
        self.assertStatusCode(response, 200)

        # #
        # # View should 401 when authenticated as client
        # #
        # request = self.factory.put(self.path, data=place_data, content_type='application/json')
        # request.META[KEY_HEADER] = self.apikey.key
        # response = self.view(request, **self.request_kwargs)
        # self.assertStatusCode(response, 401)

        # #
        # # View should update the place when owner is authenticated
        # #
        # request = self.factory.put(self.path, data=place_data, content_type='application/json')
        # request.user = self.owner
        # response = self.view(request, **self.request_kwargs)
        # self.assertStatusCode(response, 200)

        data = json.loads(response.rendered_content)

        # Check that the data attributes have been incorporated into the
        # properties
        self.assertEqual(data['properties'].get('type'), 'Park Bench')
        self.assertIsNone(data['properties']['submitter'])

        # name is not special (lives in the data blob), so should just be unset
        self.assertNotIn('name', data['properties'])

        # private-secrets is not special, but is private, so should not come
        # back down
        self.assertNotIn('private-secrets', data['properties'])

    def test_PATCH_response_as_owner(self):
        place_data = json.dumps({
          'type': 'Feature',
          'properties': {
            'type': 'Park Bench',
            'meal-preference': 'vegan',
            'private-email': 'test@example.com',
          },
          'geometry': {"type": "Point", "coordinates": [-80, 40]},
        })

        #
        # View should update the place when client is authenticated (apikey)
        #
        request = self.factory.patch(self.path, data=place_data, content_type='application/json')
        request.META[KEY_HEADER] = self.apikey.key
        response = self.view(request, **self.request_kwargs)
        self.assertStatusCode(response, 200)

        data = json.loads(response.rendered_content)

        # Check that the data attributes have been incorporated into the
        # properties
        self.assertEqual(data['properties'].get('type'), 'Park Bench')
        self.assertEqual(data['properties'].get('meal-preference'), 'vegan')
        self.assertEqual(data['geometry'], {"type": "Point", "coordinates": [-80, 40]})

        # Check that previous data is all still there
        self.assertEqual(data['properties'].get('name'), 'K-Mart')

        # private-secrets is not special, but is private, so should not come
        # back down
        self.assertNotIn('private-secrets', data['properties'])
        self.assertNotIn('private-email', data['properties'])

    def test_PUT_response_as_owner_doesnt_change_submitter(self):
        place_data = json.dumps({
          'type': 'Feature',
          'properties': {
            'type': 'Park Bench',
            'private-secrets': 'The mayor loves this bench'
          },
          'geometry': {"type": "Point", "coordinates": [-73.99, 40.75]},
        })

        request = self.factory.put(self.path, data=place_data, content_type='application/json')
        request.user = self.owner
        response = self.view(request, **self.request_kwargs)

        self.assertStatusCode(response, 200)
        data = json.loads(response.rendered_content)

        # Check that the submitter is still the original
        self.assertEqual(data['properties'].get('submitter', {}).get('id'), self.submitter.id)

    def test_PUT_to_invisible_place(self):
        place_data = json.dumps({
            'type': 'Feature',
            'properties': {
                'type': 'Park Bench',
                'private-secrets': 'The mayor loves this bench',
                'submitter': None
            },
            'geometry': {"type": "Point", "coordinates": [-73.99, 40.75]}
        })

        #
        # View should 401 when trying to update when not authenticated
        #
        request = self.factory.put(self.invisible_path + '?include_invisible', data=place_data, content_type='application/json')
        response = self.view(request, **self.invisible_request_kwargs)
        self.assertStatusCode(response, 401)

        #
        # View should 403 when owner is authenticated through api key
        #
        request = self.factory.put(self.invisible_path + '?include_invisible', data=place_data, content_type='application/json')
        request.META[KEY_HEADER] = self.apikey.key
        response = self.view(request, **self.invisible_request_kwargs)
        self.assertStatusCode(response, 403)

        #
        # View should update the place when owner is directly authenticated
        #
        request = self.factory.put(self.invisible_path + '?include_invisible', data=place_data, content_type='application/json')
        credentials = ':'.join([self.owner.username, '123']).encode()
        request.META['HTTP_AUTHORIZATION'] = 'Basic ' + base64.b64encode(credentials).decode()
        response = self.view(request, **self.invisible_request_kwargs)

        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 200)

        # Check that the data attributes have been incorporated into the
        # properties
        self.assertEqual(data['properties'].get('type'), 'Park Bench')

        # submitter is special, and so should be present and None
        self.assertIsNone(data['properties']['submitter'])

        # name is not special (lives in the data blob), so should just be unset
        self.assertNotIn('name', data['properties'])

        # private-secrets is not special, but is private, so should not come
        # back down
        self.assertNotIn('private-secrets', data['properties'])


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

    def test_OPTIONS_response(self):
        request = self.factory.options(self.path)
        response = self.view(request, **self.request_kwargs)

        # Check that the request was successful
        self.assertStatusCode(response, 200)

    def test_OPTIONS_response_as_owner(self):
        request = self.factory.options(self.path)
        request.user = self.owner
        response = self.view(request, **self.request_kwargs)

        # Check that the request was successful
        self.assertStatusCode(response, 200)

    def test_GET_response(self):
        request = self.factory.get(self.path)
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 200)

        # Check that it's a feature collection
        self.assertIn('type', data)
        self.assertIn('features', data)
        self.assertIn('metadata', data)

        # Check that the metadata looks right
        self.assertIn('length', data['metadata'])
        self.assertIn('next', data['metadata'])
        self.assertIn('previous', data['metadata'])
        self.assertIn('page', data['metadata'])

        # Check that we have the right number of features
        self.assertEqual(len(data['features']), 1)

        self.assertIn('properties', data['features'][0])
        self.assertIn('geometry', data['features'][0])
        self.assertIn('type', data['features'][0])

        self.assertEqual(data['features'][0]['properties']['url'],
            'http://testserver/api/v2/%s/datasets/%s/places/%s' %
            (self.owner.username, self.dataset.slug, self.place.id))

    def test_GET_response_for_multiple_specific_objects(self):
        places = []
        for _ in range(10):
            places.append(Place.objects.create(
              dataset=self.dataset,
              geometry='POINT(2 3)',
              submitter=self.submitter,
              data=json.dumps({
                'type': 'ATM',
                'name': 'K-Mart',
                'private-secrets': 42
              }),
            ))

        request_kwargs = {
          'owner_username': self.owner.username,
          'dataset_slug': self.dataset.slug,
          'pk_list': ','.join([str(p.pk) for p in places[::2]])
        }

        factory = RequestFactory()
        path = reverse('place-list', kwargs=request_kwargs)
        view = PlaceListView.as_view()

        request = factory.get(path)
        response = view(request, **request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 200)

        # Check that it's a feature collection
        self.assertIn('features', data)

        # Check that we have the right number of features
        self.assertEqual(len(data['features']), 5)

        # Check that the pks are correct
        self.assertEqual(
            set([f['id'] for f in data['features']]),
            set([p.pk for p in places[::2]])
        )

    def test_GET_csv_response(self):
        request = self.factory.get(self.path + '?format=csv')
        response = self.view(request, **self.request_kwargs)

        rows = list(csv.reader(StringIO(response.rendered_content.decode())))
        headers = rows[0]

        # Check that the request was successful
        self.assertStatusCode(response, 200)

        # Check that it's got good headers
        self.assertIn('dataset', headers)
        self.assertIn('geometry', headers)
        self.assertIn('name', headers)

        # Check that we have the right number of rows
        self.assertEqual(len(rows), 2)

    def test_GET_text_search_response(self):
        Place.objects.create(dataset=self.dataset, geometry='POINT(0 0)', data=json.dumps({'foo': 'bar', 'name': 1})),
        Place.objects.create(dataset=self.dataset, geometry='POINT(1 0)', data=json.dumps({'foo': 'bar', 'name': 2})),
        Place.objects.create(dataset=self.dataset, geometry='POINT(2 0)', data=json.dumps({'foo': 'baz', 'name': 3})),
        Place.objects.create(dataset=self.dataset, geometry='POINT(3 0)', data=json.dumps({'name': 4})),

        request = self.factory.get(self.path + '?search=bar')
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that there are ATM features
        self.assertStatusCode(response, 200)
        self.assertTrue(all([feature['properties'].get('foo') == 'bar' for feature in data['features']]))
        self.assertEqual(len(data['features']), 2)

        request = self.factory.get(self.path + '?search=ba')
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 200)
        self.assertTrue(all([feature['properties'].get('foo') in ('bar', 'baz') for feature in data['features']]))
        self.assertEqual(len(data['features']), 3)

        request = self.factory.get(self.path + '?search=bad')
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 200)
        self.assertEqual(len(data['features']), 0)

        request = self.factory.get(self.path + '?search=')
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 200)
        self.assertEqual(len(data['features']), self.dataset.places.filter(visible=True).count())

    def test_GET_filtered_response(self):
        Place.objects.create(dataset=self.dataset, geometry='POINT(0 0)', data=json.dumps({'foo': 'bar', 'name': 1})),
        Place.objects.create(dataset=self.dataset, geometry='POINT(1 0)', data=json.dumps({'foo': 'bar', 'name': 2})),
        Place.objects.create(dataset=self.dataset, geometry='POINT(2 0)', data=json.dumps({'foo': 'baz', 'name': 3})),
        Place.objects.create(dataset=self.dataset, geometry='POINT(3 0)', data=json.dumps({'name': 4})),

        request = self.factory.get(self.path + '?foo=bar')
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that there are ATM features
        self.assertStatusCode(response, 200)
        self.assertTrue(all([feature['properties'].get('foo') == 'bar' for feature in data['features']]))
        self.assertEqual(len(data['features']), 2)

        request = self.factory.get(self.path + '?foo=qux')
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 200)
        self.assertEqual(len(data['features']), 0)

        request = self.factory.get(self.path + '?nonexistent=foo')
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 200)
        self.assertEqual(len(data['features']), 0)

    def test_GET_indexed_response(self):
        Place.objects.create(dataset=self.dataset, geometry='POINT(0 0)', data=json.dumps({'foo': 'bar', 'name': 1})),
        Place.objects.create(dataset=self.dataset, geometry='POINT(1 0)', data=json.dumps({'foo': 'bar', 'name': 2})),
        Place.objects.create(dataset=self.dataset, geometry='POINT(2 0)', data=json.dumps({'foo': 'baz', 'name': 3})),
        Place.objects.create(dataset=self.dataset, geometry='POINT(3 0)', data=json.dumps({'name': 4})),

        self.dataset.indexes.add(DataIndex(attr_name='foo'), bulk=False)

        qs = Place.objects.all()

        from  sa_api_v2.models.core import SubmittedThingQuerySet
        with mock.patch.object(SubmittedThingQuerySet, 'filter_by_index', return_value=qs) as patched_filter:
            request = self.factory.get(self.path + '?foo=bar')
            self.view(request, **self.request_kwargs)
            self.assertEqual(patched_filter.call_count, 1)

    def test_GET_unindexed_response(self):
        Place.objects.create(dataset=self.dataset, geometry='POINT(0 0)', data=json.dumps({'foo': 'bar', 'name': 1})),
        Place.objects.create(dataset=self.dataset, geometry='POINT(1 0)', data=json.dumps({'foo': 'bar', 'name': 2})),
        Place.objects.create(dataset=self.dataset, geometry='POINT(2 0)', data=json.dumps({'foo': 'baz', 'name': 3})),
        Place.objects.create(dataset=self.dataset, geometry='POINT(3 0)', data=json.dumps({'name': 4})),

        self.dataset.indexes.add(DataIndex(attr_name='foo'), bulk=False)

        qs = Place.objects.all()

        from  sa_api_v2.models.core import SubmittedThingQuerySet
        with mock.patch.object(SubmittedThingQuerySet, 'filter_by_index', return_value=qs) as patched_filter:
            request = self.factory.get(self.path + '?name=1')
            self.view(request, **self.request_kwargs)
            self.assertEqual(patched_filter.call_count, 0)

    def test_GET_paginated_response(self):
        # Create a view with pagination configuration set, for consistency
        class OverrideFeatureCollectionPagination (FeatureCollectionPagination):
            page_size = 50
            page_size_param = 'page_size'

        class OverridePlaceListView (PlaceListView):
            pagination_class = OverrideFeatureCollectionPagination

        self.view = OverridePlaceListView.as_view()

        for _ in range(30):
            Place.objects.create(dataset=self.dataset, geometry='POINT(0 0)', data=json.dumps({'foo': 'bar', 'name': 1})),
            Place.objects.create(dataset=self.dataset, geometry='POINT(1 0)', data=json.dumps({'foo': 'bar', 'name': 2})),
            Place.objects.create(dataset=self.dataset, geometry='POINT(2 0)', data=json.dumps({'foo': 'baz', 'name': 3})),
            Place.objects.create(dataset=self.dataset, geometry='POINT(3 0)', data=json.dumps({'name': 4})),

        # There should be 121 visible places in the dataset
        self.assert_(Place.objects.filter(dataset=self.dataset, visible=True).count(), 121)

        # Check that we have items on the 2nd page
        request = self.factory.get(self.path + '?page=2')
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        self.assertStatusCode(response, 200)
        self.assertIn('features', data)
        self.assertEqual(len(data['features']), 50)  # default, in settings.py

        # Check that we can override the page size
        request = self.factory.get(self.path + '?page_size=3')
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        self.assertStatusCode(response, 200)
        self.assertIn('features', data)
        self.assertEqual(len(data['features']), 3)

    def test_GET_nearby_response(self):
        Place.objects.create(dataset=self.dataset, geometry='POINT(0 0)', data=json.dumps({'new_place': 'yes', 'name': 1})),
        Place.objects.create(dataset=self.dataset, geometry='POINT(10 0)', data=json.dumps({'new_place': 'yes', 'name': 2})),
        Place.objects.create(dataset=self.dataset, geometry='POINT(20 0)', data=json.dumps({'new_place': 'yes', 'name': 3})),
        Place.objects.create(dataset=self.dataset, geometry='POINT(30 0)', data=json.dumps({'new_place': 'yes', 'name': 4})),

        request = self.factory.get(self.path + '?near=0,19&new_place=yes')
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that we have all the places, sorted by distance
        self.assertStatusCode(response, 200)
        self.assertEqual(len(data['features']), 4)
        self.assertEqual([feature['properties']['name'] for feature in data['features']],
                         [3,2,4,1])
        self.assertIn('distance', data['features'][0]['properties'])

    def test_GET_response_with_paginated_data(self):
        for _ in range(150):
            Place.objects.create(
              dataset=self.dataset,
              geometry='POINT(2 3)',
              submitter=self.submitter,
              data=json.dumps({
                'type': 'ATM',
                'name': 'K-Mart',
                'private-secrets': 42
              }),
            )

        # Log-in with session auth
        request = self.factory.get(self.path + '?include_private=True')
        request.user = self.owner

        # Request the first page
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 200)

        # Check that the page has the right number of features
        self.assertEqual(len(data['features']), settings.REST_FRAMEWORK['PAGE_SIZE'])

        # Check that the next page is asking for private data
        self.assertIn('include_private=True', data['metadata']['next'])

    def test_GET_response_with_private_data(self):
        #
        # View should not return private data normally
        #
        request = self.factory.get(self.path)
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 200)

        # Check that the private data is not in the properties
        self.assertNotIn('private-secrets', data['features'][0]['properties'])

        # --------------------------------------------------

        #
        # View should 401 when not allowed to request private data (not authenticated)
        #
        request = self.factory.get(self.path + '?include_private')
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was restricted
        self.assertStatusCode(response, 401)

        # --------------------------------------------------

        #
        # View should 403 when not allowed to request private data (api key)
        #
        request = self.factory.get(self.path + '?include_private')
        request.META[KEY_HEADER] = self.apikey.key
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was restricted
        self.assertStatusCode(response, 403)

        # --------------------------------------------------

        #
        # View should 403 when not allowed to request private data (not owner)
        #
        request = self.factory.get(self.path + '?include_private')
        request.user = User.objects.create(username='new_user', password='password')
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was restricted
        self.assertStatusCode(response, 403)

        # --------------------------------------------------

        #
        # View should return private data when owner is logged in (Session Auth)
        #
        request = self.factory.get(self.path + '?include_private')
        request.user = self.owner
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 200)

        # Check that the private data is in the properties
        self.assertIn('private-secrets', data['features'][0]['properties'])

        # --------------------------------------------------

        #
        # View should return private data when owner is logged in (Basic Auth)
        #
        request = self.factory.get(self.path + '?include_private')
        credentials = ':'.join([self.owner.username, '123']).encode()
        request.META['HTTP_AUTHORIZATION'] = 'Basic ' + base64.b64encode(credentials).decode()
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 200)

        # Check that the private data is in the properties
        self.assertIn('private-secrets', data['features'][0]['properties'])

    def test_GET_invalid_url(self):
        # Make sure that we respond with 404 if a slug is supplied, but for
        # the wrong dataset or owner.
        request_kwargs = {
          'owner_username': 'mischevious_owner',
          'dataset_slug': self.dataset.slug
        }

        path = reverse('place-list', kwargs=request_kwargs)
        request = self.factory.get(path)
        response = self.view(request, **request_kwargs)

        self.assertStatusCode(response, 404)

    def test_POST_response(self):
        place_data = json.dumps({
            'properties': {
                'submitter_name': 'Andy',
                'type': 'Park Bench',
                'private-secrets': 'The mayor loves this bench',
            },
            'type': 'Feature',
            'geometry': {"type": "Point", "coordinates": [-73.99, 40.75]}
        })
        start_num_places = Place.objects.all().count()

        #
        # View should 401 when trying to create when not authenticated
        #
        request = self.factory.post(self.path, data=place_data, content_type='application/json')
        response = self.view(request, **self.request_kwargs)
        self.assertStatusCode(response, 401)

        #
        # View should create the place when owner is authenticated
        #
        request = self.factory.post(self.path, data=place_data, content_type='application/json')
        request.META[KEY_HEADER] = self.apikey.key
        self.apikey.permissions.all().delete()
        self.apikey.permissions.add_permission('places', True, True, False, False)

        response = self.view(request, **self.request_kwargs)

        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 201)

        # Check that the data attributes have been incorporated into the
        # properties
        self.assertEqual(data['properties'].get('type'), 'Park Bench')
        self.assertEqual(data['properties'].get('submitter_name'), 'Andy')

        self.assertIn('submitter', data['properties'])
        self.assertIsNone(data['properties']['submitter'])

        # visible should be true by default
        self.assertTrue(data['properties'].get('visible'))

        # Check that geometry exists
        self.assertIn('geometry', data)

        # private-secrets is not special, but is private, so should not come
        # back down
        self.assertNotIn('private-secrets', data['properties'])

        # Check that we actually created a place
        final_num_places = Place.objects.all().count()
        self.assertEqual(final_num_places, start_num_places + 1)

        #
        # View should 401 when api key does not have enough permission
        #
        request = self.factory.post(self.path, data=place_data, content_type='application/json')
        request.META[KEY_HEADER] = self.apikey.key
        self.apikey.permissions.all().delete()
        self.apikey.permissions.add_permission('places', False, True, False, False)
        self.apikey.permissions.add_permission('comments', True, True, False, False)

        response = self.view(request, **self.request_kwargs)
        self.assertStatusCode(response, 403)

    @unittest.skip("TODO: figure out what the desired behavior for bulk PUT is.")
    def test_PUT_creates_in_bulk(self):
        # Create a couple bogus places so that we can be sure we're not
        # inadvertantly deleting them
        Place.objects.create(dataset=self.dataset, geometry='POINT(0 0)')
        Place.objects.create(dataset=self.dataset, geometry='POINT(0 0)')

        # Make some data that will update the place, and create another
        place_data = json.dumps([
            {
                'properties': {
                    'submitter_name': 'Andy',
                    'type': 'Park Bench',
                    'private-secrets': 'The mayor loves this bench',
                },
                'type': 'Feature',
                'geometry': {"type": "Point", "coordinates": [-73.99, 40.75]}
            },
            {
                'properties': {
                    'submitter_name': 'Mjumbe',
                    'type': 'Street Light',
                    'private-secrets': 'Helps with street safety, but not as much as storefronts do.',
                },
                'type': 'Feature',
                'geometry': {"type": "Point", "coordinates": [-73.98, 40.76]}
            },
        ])
        start_num_places = Place.objects.all().count()

        #
        # View should 401 when trying to update when not authenticated
        #
        request = self.factory.put(self.path, data=place_data, content_type='application/json')
        response = self.view(request, **self.request_kwargs)
        self.assertStatusCode(response, 401)

        #
        # View should update the places when owner is authenticated
        #
        request = self.factory.put(self.path, data=place_data, content_type='application/json')
        request.META[KEY_HEADER] = self.apikey.key

        response = self.view(request, **self.request_kwargs)

        data_list = json.loads(response.rendered_content)['features']

        # Check that the request was successful
        self.assertStatusCode(response, 200)
        self.assertEqual(len(data_list), 2)

        ### Check that we actually created the places
        final_num_places = Place.objects.all().count()
        self.assertEqual(final_num_places, start_num_places + 2)

    @unittest.skip("TODO: figure out what the desired behavior for bulk PUT is.")
    def test_PUT_response_creates_and_updates_at_once(self):
        # Create a couple bogus places so that we can be sure we're not
        # inadvertantly deleting them
        Place.objects.create(dataset=self.dataset, geometry='POINT(0 0)')
        Place.objects.create(dataset=self.dataset, geometry='POINT(0 0)')

        # Create a place
        place = Place.objects.create(dataset=self.dataset, geometry='POINT(0 0)')

        # Make some data that will update the place, and create another
        place_data = json.dumps([
            {
                'properties': {
                    'submitter_name': 'Andy',
                    'type': 'Park Bench',
                    'private-secrets': 'The mayor loves this bench',
                    'id': place.id,
                    'url': 'http://testserver/api/v2/aaron/datasets/ds/places/%s' % (place.id,)
                },
                'type': 'Feature',
                'id': place.id,
                'geometry': {"type": "Point", "coordinates": [-73.99, 40.75]}
            },
            {
                'properties': {
                    'submitter_name': 'Mjumbe',
                    'type': 'Street Light',
                    'private-secrets': 'Helps with street safety, but not as much as storefronts do.',
                },
                'type': 'Feature',
                'geometry': {"type": "Point", "coordinates": [-73.98, 40.76]}
            },
        ])
        start_num_places = Place.objects.all().count()

        #
        # View should 401 when trying to update when not authenticated
        #
        request = self.factory.put(self.path, data=place_data, content_type='application/json')
        response = self.view(request, **self.request_kwargs)
        self.assertStatusCode(response, 401)

        #
        # View should update the places when owner is authenticated
        #
        request = self.factory.put(self.path, data=place_data, content_type='application/json')
        request.META[KEY_HEADER] = self.apikey.key

        response = self.view(request, **self.request_kwargs)

        data_list = json.loads(response.rendered_content)['features']

        # Check that the request was successful
        self.assertStatusCode(response, 200)
        self.assertEqual(len(data_list), 2)

        ### Check the updated item
        data = [item for item in data_list if item['id'] == place.id][0]

        # Check that the data attributes have been incorporated into the
        # properties
        self.assertEqual(data['properties'].get('type'), 'Park Bench')
        self.assertEqual(data['properties'].get('submitter_name'), 'Andy')

        self.assertIn('submitter', data['properties'])
        self.assertIsNone(data['properties']['submitter'])

        # visible should be true by default
        self.assertTrue(data['properties'].get('visible'))

        # Check that geometry exists
        self.assertIn('geometry', data)

        # private-secrets is not special, but is private, so should not come
        # back down
        self.assertNotIn('private-secrets', data['properties'])

        # Check that we actually created a place
        final_num_places = Place.objects.all().count()
        self.assertEqual(final_num_places, start_num_places + 1)

        ### Check the created item
        data = [item for item in data_list if item['id'] != place.id][0]

        # Check that the data attributes have been incorporated into the
        # properties
        self.assertEqual(data['properties'].get('type'), 'Street Light')
        self.assertEqual(data['properties'].get('submitter_name'), 'Mjumbe')

        ### Check that we actually created the places
        final_num_places = Place.objects.all().count()
        self.assertEqual(final_num_places, start_num_places + 1)

    def test_POST_response_with_submitter(self):
        place_data = json.dumps({
            'properties': {
                'type': 'Park Bench',
                'private-secrets': 'The mayor loves this bench',
            },
            'type': 'Feature',
            'geometry': {"type": "Point", "coordinates": [-73.99, 40.75]}
        })
        start_num_places = Place.objects.all().count()

        #
        # View should create the place when owner is authenticated
        #
        request = self.factory.post(self.path, data=place_data, content_type='application/json')
        request.META[KEY_HEADER] = self.apikey.key
        request.user = self.submitter
        request.csrf_processing_done = True

        response = self.view(request, **self.request_kwargs)

        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 201)

        # Check that the data attributes have been incorporated into the
        # properties
        self.assertEqual(data['properties'].get('type'), 'Park Bench')

        self.assertIn('submitter', data['properties'])
        self.assertIsNotNone(data['properties']['submitter'])
        self.assertEqual(data['properties']['submitter']['id'], self.submitter.id)

        # visible should be true by default
        self.assertTrue(data['properties'].get('visible'))

        # Check that geometry exists
        self.assertIn('geometry', data)

        # private-secrets is not special, but is private, so should not come
        # back down
        self.assertNotIn('private-secrets', data['properties'])

        # Check that we actually created a place
        final_num_places = Place.objects.all().count()
        self.assertEqual(final_num_places, start_num_places + 1)

    def test_POST_with_silent_creates_no_activity(self):
        Action.objects.all().delete()
        assert Action.objects.all().count() == 0

        place_data = json.dumps({
          'type': 'Feature',
          'properties': {
            'type': 'Park Bench',
            'private-secrets': 'The mayor loves this bench',
            'submitter': None
          },
          'geometry': {"type": "Point", "coordinates": [-73.99, 40.75]},
        })

        request = self.factory.post(self.path, data=place_data, content_type='application/json', HTTP_X_SHAREABOUTS_SILENT='true')
        request.META[KEY_HEADER] = self.apikey.key
        response = self.view(request, **self.request_kwargs)
        self.assertStatusCode(response, 201)

        self.assertEqual(Action.objects.all().count(), 0)

    def test_GET_response_with_invisible_data(self):
        #
        # View should not return invisible data normally
        #
        request = self.factory.get(self.path)
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 200)
        self.assertEqual(len(data['features']), 1)

        # --------------------------------------------------

        #
        # View should 401 when not allowed to request private data (not authenticated)
        #
        request = self.factory.get(self.path + '?include_invisible')
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was restricted
        self.assertStatusCode(response, 401)

        # --------------------------------------------------

        #
        # View should 403 when not allowed to request private data (api key)
        #
        request = self.factory.get(self.path + '?include_invisible')
        request.META[KEY_HEADER] = self.apikey.key
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was restricted
        self.assertStatusCode(response, 403)

        # --------------------------------------------------

        #
        # View should 403 when not allowed to request private data (not owner)
        #
        request = self.factory.get(self.path + '?include_invisible')
        request.user = User.objects.create(username='new_user', password='password')
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was restricted
        self.assertStatusCode(response, 403)

        # --------------------------------------------------

        #
        # View should return private data when allowed (api key)
        #
        request = self.factory.get(self.path + '?include_invisible')
        self.apikey.permissions.add_permission(
            '*',
            can_create=False,
            can_retrieve=True,
            can_update=False,
            can_destroy=False,
            can_access_protected=True)
        request.META[KEY_HEADER] = self.apikey.key
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was restricted
        self.assertStatusCode(response, 200)

        # --------------------------------------------------

        #
        # View should return private data when owner is logged in (Session Auth)
        #
        request = self.factory.get(self.path + '?include_invisible')
        request.user = self.owner
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 200)
        self.assertEqual(len(data['features']), 2)

        # --------------------------------------------------

        #
        # View should return private data when owner is logged in (Basic Auth)
        #
        request = self.factory.get(self.path + '?include_invisible')
        credentials = ':'.join([self.owner.username, '123']).encode()
        request.META['HTTP_AUTHORIZATION'] = 'Basic ' + base64.b64encode(credentials).decode()
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 200)
        self.assertEqual(len(data['features']), 2)

    def test_POST_invisible_response(self):
        place_data = json.dumps({
            'properties': {
                'submitter_name': 'Andy',
                'type': 'Park Bench',
                'private-secrets': 'The mayor loves this bench',
                'visible': False
            },
            'type': 'Feature',
            'geometry': {"type": "Point", "coordinates": [-73.99, 40.75]},
        })

        request = self.factory.post(self.path, data=place_data, content_type='application/json')
        request.META[KEY_HEADER] = self.apikey.key
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 201)

        # Check that visible is false
        self.assertEqual(data.get('properties').get('visible'), False)

    def test_POST_response_like_XDomainRequest(self):
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
        # View should create the place when origin is supplied, even without a
        # content type.
        #
        request = self.factory.post(self.path, data=place_data, content_type='')
        request.META['HTTP_ORIGIN'] = self.ds_origin.pattern
        response = self.view(request, **self.request_kwargs)

        # Check that the request was successful
        self.assertStatusCode(response, 201)

    def test_model_update_clears_GET_cache_for_multiple_specific_objects(self):
        places = []
        for _ in range(10):
            places.append(Place.objects.create(
              dataset=self.dataset,
              geometry='POINT(2 3)',
              submitter=self.submitter,
              data=json.dumps({
                'type': 'ATM',
                'name': 'K-Mart',
                'private-secrets': 42
              }),
            ))
        cache_buffer.flush()

        request_kwargs = {
          'owner_username': self.owner.username,
          'dataset_slug': self.dataset.slug,
          'pk_list': ','.join([str(p.pk) for p in places[::2]])
        }

        factory = RequestFactory()
        path = reverse('place-list', kwargs=request_kwargs)
        view = PlaceListView.as_view()

        # First call should run queries
        #
        # ---- Check (and cache) permissions
        #
        # - SELECT dataset
        # - SELECT dataset permissions
        # - SELECT keys
        # - SELECT key permissions
        # - SELECT origins
        # - SELECT origin permissions
        #
        # ---- Load the data
        #
        # SELECT COUNT(*) FROM place WHERE (id IN <place ids> AND visible = true AND dataset )
        # SELECT * FROM place INNER JOIN ds ON ( dataset ) LEFT OUTER JOIN user ON ( submitter ) INNER JOIN user ON ( owner ) WHERE (id IN <place ids> AND visible = true AND dataset ) LIMIT 5
        # SELECT * FROM social WHERE user_id IN <place submitters>
        # SELECT * FROM group for users <place submitters>
        # SELECT * FROM sset WHERE place_id IN <place ids>
        # SELECT * FROM att WHERE thing_id IN <place ids>
        #
        request = factory.get(path)
        with self.assertNumQueries(12):
            view(request, **request_kwargs)

        # Second call should hardly hit the database
        request = factory.get(path)
        with self.assertNumQueries(0):
            view(request, **request_kwargs)

        # After we modify one of the places, cache should be invalidated
        places[0].data = json.dumps({
            'type': 'ATM',
            'name': 'K-Mart',
            'private-secrets': 43
        })
        places[0].save()
        cache_buffer.flush()

        # Run same queries as above (except for permissions)
        request = factory.get(path)
        with self.assertNumQueries(6):
            view(request, **request_kwargs)


class TestSubmissionInstanceView (APITestMixin, TestCase):
    def setUp(self):
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
        self.submissions = [
          Submission.objects.create(place=self.place, set_name='comments', dataset=self.dataset, data='{"comment": "Wow!", "private-email": "abc@example.com", "foo": 3}'),
          Submission.objects.create(place=self.place, set_name='comments', dataset=self.dataset, data='{"foo": 3}'),
          Submission.objects.create(place=self.place, set_name='comments', dataset=self.dataset, data='{"foo": 3}', visible=False),
          Submission.objects.create(place=self.place, set_name='likes', dataset=self.dataset, data='{"bar": 3}'),
          Submission.objects.create(place=self.place, set_name='likes', dataset=self.dataset, data='{"bar": 3}'),
          Submission.objects.create(place=self.place, set_name='likes', dataset=self.dataset, data='{"bar": 3}'),
          Submission.objects.create(place=self.place, set_name='likes', dataset=self.dataset, data='{"bar": 3}', visible=False),
        ]

        f = StringIO(u'This is test content in a "file"')
        f.name = 'myfile.txt'
        f.size = 20
        self.attachments = Attachment.objects.create(
            file=File(f, 'myfile.txt'), name='my_file_name', thing=self.submissions[0])

        self.submission = self.submissions[0]

        self.apikey = ApiKey.objects.create(key='abc', dataset=self.dataset)
        ApiKey.objects.create(key='abc2', dataset=self.dataset)

        self.origin = Origin.objects.create(pattern='def', dataset=self.dataset)
        Origin.objects.create(pattern='def2', dataset=self.dataset)

        self.request_kwargs = {
          'owner_username': self.owner.username,
          'dataset_slug': self.dataset.slug,
          'place_id': self.place.id,
          'submission_set_name': 'comments',
          'submission_id': self.submission.id
        }

        self.factory = RequestFactory()
        self.path = reverse('submission-detail', kwargs=self.request_kwargs)
        self.view = SubmissionInstanceView.as_view()

        cache_buffer.reset()
        django_cache.clear()

    def tearDown(self):
        User.objects.all().delete()
        DataSet.objects.all().delete()
        Place.objects.all().delete()
        Submission.objects.all().delete()
        ApiKey.objects.all().delete()

        cache_buffer.reset()
        django_cache.clear()

    def test_GET_response(self):
        request = self.factory.get(self.path)
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 200)

        # Check that data attribute is not present
        self.assertNotIn('data', data)

        # Check that the data attributes have been incorporated into the
        # properties
        self.assertEqual(data.get('comment'), 'Wow!')

        # Check that the appropriate attributes are in the properties
        self.assertIn('url', data)
        self.assertIn('dataset', data)
        self.assertIn('attachments', data)
        self.assertIn('set', data)
        self.assertIn('submitter', data)
        self.assertIn('place', data)

        # Check that the URL is right
        self.assertEqual(data['url'],
            'http://testserver' + reverse('submission-detail', args=[
                self.owner.username, self.dataset.slug, self.place.id,
                self.submission.set_name, self.submission.id]))

    def test_GET_response_with_attachment(self):
        request = self.factory.get(self.path)
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the attachment looks right
        self.assertIn('file', data['attachments'][0])
        self.assertIn('name', data['attachments'][0])

        self.assertEqual(len(data['attachments']), 1)
        self.assertEqual(data['attachments'][0]['name'], 'my_file_name')

        a = self.submissions[0].attachments.all()[0]
        self.assertEqual(a.file.read(), b'This is test content in a "file"')

    def test_GET_response_with_private_data(self):
        #
        # View should not return private data normally
        #
        request = self.factory.get(self.path)
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 200)

        # Check that the private data is not in the properties
        self.assertNotIn('private-email', data)

        # --------------------------------------------------

        #
        # View should 401 when not allowed to request private data (not authenticated)
        #
        request = self.factory.get(self.path + '?include_private')
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was restricted
        self.assertStatusCode(response, 401)

        # --------------------------------------------------

        #
        # View should 403 when not allowed to request private data (api key)
        #
        request = self.factory.get(self.path + '?include_private')
        request.META[KEY_HEADER] = self.apikey.key
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was restricted
        self.assertStatusCode(response, 403)

        # --------------------------------------------------

        #
        # View should 403 when not allowed to request private data (not owner)
        #
        request = self.factory.get(self.path + '?include_private')
        request.user = User.objects.create(username='new_user', password='password')
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was restricted
        self.assertStatusCode(response, 403)

        # --------------------------------------------------

        #
        # View should return private data when owner is logged in (Session Auth)
        #
        request = self.factory.get(self.path + '?include_private')
        request.user = self.owner
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 200)

        # Check that the private data is in the properties
        self.assertIn('private-email', data)

        # --------------------------------------------------

        #
        # View should return private data when owner is logged in (Basic Auth)
        #
        request = self.factory.get(self.path + '?include_private')
        credentials = ':'.join([self.owner.username, '123']).encode()
        request.META['HTTP_AUTHORIZATION'] = 'Basic ' + base64.b64encode(credentials).decode()
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 200)

        # Check that the private data is in the properties
        self.assertIn('private-email', data)

    def test_GET_invalid_url(self):
        # Make sure that we respond with 404 if a place_id is supplied, but for
        # the wrong dataset or owner.
        request_kwargs = {
          'owner_username': 'mischevious_owner',
          'dataset_slug': self.dataset.slug,
          'place_id': self.place.id,
          'submission_set_name': 'comments',
          'submission_id': self.submission.id
        }

        path = reverse('submission-detail', kwargs=request_kwargs)
        request = self.factory.get(path)
        response = self.view(request, **request_kwargs)

        self.assertStatusCode(response, 404)

    def test_GET_from_cache(self):
        path = reverse('submission-detail', kwargs=self.request_kwargs)
        request = self.factory.get(path)

        # Check that we make a finite number of queries
        #
        # ---- Checking data access permissions:
        #
        # - SELECT requested dataset and owner
        # - SELECT dataset permissions
        # - SELECT keys
        # - SELECT key permissions
        # - SELECT origins
        # - SELECT origin permissions
        #
        # ---- Build the data
        #
        # - SELECT * FROM sa_api_submission AS s
        #     JOIN sa_api_submittedthing AS st ON (s.submittedthing_ptr_id = st.id)
        #     JOIN sa_api_dataset AS ds ON (st.dataset_id = ds.id)
        #     JOIN sa_api_submissionset AS ss ON (s.parent_id = ss.id)
        #     JOIN sa_api_place AS p ON (ss.place_id = p.submittedthing_ptr_id)
        #     JOIN sa_api_submittedthing AS pt ON (p.submittedthing_ptr_id = pt.id)
        #    WHERE st.id = <self.submission.id>;
        #
        # - SELECT * FROM sa_api_attachment AS a
        #    WHERE a.thing_id IN (<self.submission.id>);
        #
        with self.assertNumQueries(8):
            response = self.view(request, **self.request_kwargs)
            self.assertStatusCode(response, 200)

        path = reverse('submission-detail', kwargs=self.request_kwargs)
        request = self.factory.get(path)

        # Check that this performs no more queries than required for auth,
        # since the data's all cached
        with self.assertNumQueries(0):
            response = self.view(request, **self.request_kwargs)
            self.assertStatusCode(response, 200)

    def test_DELETE_response(self):
        #
        # View should 401 when trying to delete when not authenticated
        #
        request = self.factory.delete(self.path)
        response = self.view(request, **self.request_kwargs)
        self.assertStatusCode(response, 401)

        #
        # View should delete the place when owner is authenticated
        #
        request = self.factory.delete(self.path)
        request.META[KEY_HEADER] = self.apikey.key
        response = self.view(request, **self.request_kwargs)

        # Check that the request was successful
        self.assertStatusCode(response, 204)

        # Check that no data was returned
        self.assertIsNone(response.data)

    def test_PUT_response(self):
        submission_data = json.dumps({
          'comment': 'Revised opinion',
          'private-email': 'newemail@gmail.com'
        })

        #
        # View should 401 when trying to update when not authenticated
        #
        request = self.factory.put(self.path, data=submission_data, content_type='application/json')
        response = self.view(request, **self.request_kwargs)
        self.assertStatusCode(response, 401)

        #
        # View should update the place when owner is authenticated
        #
        request = self.factory.put(self.path, data=submission_data, content_type='application/json')
        request.META[KEY_HEADER] = self.apikey.key

        response = self.view(request, **self.request_kwargs)

        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 200)

        # Check that the data attributes have been incorporated into the
        # properties
        self.assertEqual(data.get('comment'), 'Revised opinion')

        # submitter is special, and so should be present and None
        self.assertIsNone(data['submitter'])

        # foo is not special (lives in the data blob), so should just be unset
        self.assertNotIn('foo', data)

        # private-email is not special, but is private, so should not come
        # back down
        self.assertNotIn('private-email', data)


class TestSubmissionListView (APITestMixin, TestCase):
    def setUp(self):
        cache_buffer.reset()
        django_cache.clear()

        self.owner_password = '123'
        self.owner = User.objects.create_user(
            username='aaron',
            password=self.owner_password,
            email='abc@example.com')
        self.submitter = User.objects.create_user(
            username='mjumbe',
            password='456',
            email='123@example.com')
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
          Submission.objects.create(place=self.place, set_name='comments', dataset=self.dataset, data='{"comment": "Wow!", "private-email": "abc@example.com", "foo": 3}'),
          Submission.objects.create(place=self.place, set_name='comments', dataset=self.dataset, data='{"foo": 3}'),
          Submission.objects.create(place=self.place, set_name='comments', dataset=self.dataset, data='{"foo": 3}', visible=False),
          Submission.objects.create(place=self.place, set_name='likes', dataset=self.dataset, data='{"bar": 3}'),
          Submission.objects.create(place=self.place, set_name='likes', dataset=self.dataset, data='{"bar": 3}'),
          Submission.objects.create(place=self.place, set_name='likes', dataset=self.dataset, data='{"bar": 3}'),
          Submission.objects.create(place=self.place, set_name='likes', dataset=self.dataset, data='{"bar": 3}', visible=False),
        ]
        self.submission = self.submissions[0]

        # These are mainly around to ensure that we don't get spillover from
        # other datasets.
        dataset2 = DataSet.objects.create(slug='ds2', owner=self.owner)
        place2 = Place.objects.create(
          dataset=dataset2,
          geometry='POINT(3 4)',
        )
        submissions2 = [
          Submission.objects.create(place=place2, set_name='comments', dataset=dataset2, data='{"comment": "Wow!", "private-email": "abc@example.com", "foo": 3}'),
          Submission.objects.create(place=place2, set_name='comments', dataset=dataset2, data='{"foo": 3}'),
          Submission.objects.create(place=place2, set_name='comments', dataset=dataset2, data='{"foo": 3}', visible=False),
        ]

        self.apikey = ApiKey.objects.create(key='abc', dataset=self.dataset)

        self.request_kwargs = {
          'owner_username': self.owner.username,
          'dataset_slug': self.dataset.slug,
          'place_id': self.place.id,
          'submission_set_name': self.submission.set_name
        }

        self.factory = RequestFactory()
        self.path = reverse('submission-list', kwargs=self.request_kwargs)
        self.view = SubmissionListView.as_view()

    def tearDown(self):
        User.objects.all().delete()
        DataSet.objects.all().delete()
        Place.objects.all().delete()
        Submission.objects.all().delete()
        ApiKey.objects.all().delete()

        cache_buffer.reset()
        django_cache.clear()

    def test_OPTIONS_response(self):
        request = self.factory.options(self.path)
        response = self.view(request, **self.request_kwargs)

        # Check that the request was successful
        self.assertStatusCode(response, 200)

    def test_OPTIONS_response_as_owner(self):
        request = self.factory.options(self.path)
        request.user = self.owner
        response = self.view(request, **self.request_kwargs)

        # Check that the request was successful
        self.assertStatusCode(response, 200)

    def test_GET_response(self):
        request = self.factory.get(self.path)
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 200)

        # Check that it's a results collection
        self.assertIn('results', data)
        self.assertIn('metadata', data)

        # Check that the metadata looks right
        self.assertIn('length', data['metadata'])
        self.assertIn('next', data['metadata'])
        self.assertIn('previous', data['metadata'])
        self.assertIn('page', data['metadata'])

        # Check that we have the right number of results
        self.assertEqual(len(data['results']), 2)

        self.assertEqual(data['results'][-1]['url'],
            'http://testserver' + reverse('submission-detail', args=[
                self.owner.username, self.dataset.slug, self.place.id,
                self.submission.set_name, self.submission.id]))

    def test_GET_response_for_multiple_specific_objects(self):
        submissions = []
        for _ in range(10):
            submissions.append(Submission.objects.create(place=self.place, set_name='comments', dataset=self.dataset, data='{"comment": "Wow!", "private-email": "abc@example.com", "foo": 3}'))

        request_kwargs = {
          'owner_username': self.owner.username,
          'dataset_slug': self.dataset.slug,
          'place_id': self.place.id,
          'submission_set_name': self.submission.set_name,
          'pk_list': ','.join([str(s.pk) for s in submissions[::2]])
        }

        factory = RequestFactory()
        path = reverse('submission-list', kwargs=request_kwargs)
        view = SubmissionListView.as_view()

        request = factory.get(path)
        response = view(request, **request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 200)

        # Check that it's a results collection
        self.assertIn('results', data)

        # Check that we have the right number of results
        self.assertEqual(len(data['results']), 5)

        # Check that the pks are correct
        self.assertEqual(
            set([r['id'] for r in data['results']]),
            set([s.pk for s in submissions[::2]])
        )

    def test_GET_csv_response(self):
        request = self.factory.get(self.path + '?format=csv')
        response = self.view(request, **self.request_kwargs)

        rows = list(csv.reader(StringIO(response.rendered_content.decode())))
        headers = rows[0]

        # Check that the request was successful
        self.assertStatusCode(response, 200)

        # Check that it's got good headers
        self.assertIn('dataset', headers)
        self.assertIn('comment', headers)
        self.assertIn('foo', headers)

        # Check that we have the right number of rows
        self.assertEqual(len(rows), 3)

    def test_GET_filtered_response(self):
        Submission.objects.create(dataset=self.dataset, place=self.place, set_name='comments', data=json.dumps({'baz': 'bar', 'name': 1})),
        Submission.objects.create(dataset=self.dataset, place=self.place, set_name='comments', data=json.dumps({'baz': 'bar', 'name': 2})),
        Submission.objects.create(dataset=self.dataset, place=self.place, set_name='comments', data=json.dumps({'baz': 'bam', 'name': 3})),
        Submission.objects.create(dataset=self.dataset, place=self.place, set_name='comments', data=json.dumps({'name': 4})),

        request = self.factory.get(self.path + '?baz=bar')
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content.decode())

        # Check that there are ATM features
        self.assertStatusCode(response, 200)
        self.assertTrue(all([result.get('baz') == 'bar' for result in data['results']]))
        self.assertEqual(len(data['results']), 2)

        request = self.factory.get(self.path + '?baz=qux')
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content.decode())

        # Check that the request was successful
        self.assertStatusCode(response, 200)
        self.assertEqual(len(data['results']), 0)

        request = self.factory.get(self.path + '?nonexistent=foo')
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content.decode())

        # Check that the request was successful
        self.assertStatusCode(response, 200)
        self.assertEqual(len(data['results']), 0)

    def test_GET_response_with_private_data(self):
        #
        # View should not return private data normally
        #
        request = self.factory.get(self.path)
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content.decode())

        # Check that the request was successful
        self.assertStatusCode(response, 200)

        # Check that the private data is not in the properties
        self.assertNotIn('private-email', data['results'][0])

        # --------------------------------------------------

        #
        # View should 401 when not allowed to request private data (not authenticated)
        #
        request = self.factory.get(self.path + '?include_private')
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content.decode())

        # Check that the request was restricted
        self.assertStatusCode(response, 401)

        # --------------------------------------------------

        #
        # View should 403 when not allowed to request private data (api key)
        #
        request = self.factory.get(self.path + '?include_private')
        request.META[KEY_HEADER] = self.apikey.key
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content.decode())

        # Check that the request was restricted
        self.assertStatusCode(response, 403)

        # --------------------------------------------------

        #
        # View should 403 when not allowed to request private data (not owner)
        #
        request = self.factory.get(self.path + '?include_private')
        request.user = User.objects.create(username='new_user', password='password')
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was restricted
        self.assertStatusCode(response, 403)

        # --------------------------------------------------

        #
        # View should return private data when owner is logged in (Session Auth)
        #
        request = self.factory.get(self.path + '?include_private')
        request.user = self.owner
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 200)

        # Check that the private data is in the properties
        self.assertIn('private-email', data['results'][-1])

        # --------------------------------------------------

        #
        # View should return private data when owner is logged in (Basic Auth)
        #
        request = self.factory.get(self.path + '?include_private')
        credentials = ':'.join([self.owner.username, '123']).encode()
        request.META['HTTP_AUTHORIZATION'] = 'Basic ' + base64.b64encode(credentials).decode()
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 200)

        # Check that the private data is in the properties
        self.assertIn('private-email', data['results'][-1])

    def test_GET_invalid_url(self):
        # Make sure that we respond with 404 if a slug is supplied, but for
        # the wrong dataset or owner.
        request_kwargs = {
          'owner_username': 'mischevious_owner',
          'dataset_slug': self.dataset.slug,
          'place_id': self.place.id,
          'submission_set_name': self.submission.set_name
        }

        path = reverse('submission-list', kwargs=request_kwargs)
        request = self.factory.get(path)
        response = self.view(request, **request_kwargs)

        self.assertStatusCode(response, 404)

    def test_POST_response(self):
        submission_data = json.dumps({
          'submitter_name': 'Andy',
          'private-email': 'abc@example.com',
          'foo': 'bar'
        })
        start_num_submissions = Submission.objects.all().count()

        #
        # View should 401 when trying to create when not authenticated
        #
        request = self.factory.post(self.path, data=submission_data, content_type='application/json')
        response = self.view(request, **self.request_kwargs)
        self.assertStatusCode(response, 401)

        #
        # View should create the submission and set when owner is authenticated
        #
        request = self.factory.post(self.path, data=submission_data, content_type='application/json')
        request.META[KEY_HEADER] = self.apikey.key

        response = self.view(request, **self.request_kwargs)

        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 201)

        # Check that the data attributes have been incorporated into the
        # properties
        self.assertEqual(data.get('foo'), 'bar')
        self.assertEqual(data.get('submitter_name'), 'Andy')

        # visible should be true by default
        self.assertTrue(data.get('visible'))

        # private-secrets is not special, but is private, so should not come
        # back down
        self.assertNotIn('private-email', data)

        # Check that we actually created a submission and set
        final_num_submissions = Submission.objects.all().count()
        self.assertEqual(final_num_submissions, start_num_submissions + 1)

    def test_POST_response_without_data_permission(self):
        submission_data = json.dumps({
          'submitter_name': 'Andy',
          'private-email': 'abc@example.com',
          'foo': 'bar'
        })
        start_num_submissions = Submission.objects.all().count()

        # Disable create permission
        key_permission = self.apikey.permissions.all().get()
        key_permission.can_create = False
        key_permission.save()

        #
        # View should 401 when trying to create
        #
        request = self.factory.post(self.path, data=submission_data, content_type='application/json')
        request.META[KEY_HEADER] = self.apikey.key
        response = self.view(request, **self.request_kwargs)
        self.assertStatusCode(response, 403)

    def test_POST_response_with_submitter(self):
        submission_data = json.dumps({
          'private-email': 'abc@example.com',
          'foo': 'bar'
        })
        start_num_submissions = Submission.objects.all().count()

        #
        # View should 401 when trying to create when not authenticated
        #
        request = self.factory.post(self.path, data=submission_data, content_type='application/json')
        response = self.view(request, **self.request_kwargs)
        self.assertStatusCode(response, 401)

        #
        # View should create the submission and set when owner is authenticated
        #
        request = self.factory.post(self.path, data=submission_data, content_type='application/json')
        request.META[KEY_HEADER] = self.apikey.key
        request.user = self.submitter
        request.csrf_processing_done = True

        response = self.view(request, **self.request_kwargs)

        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 201)

        # Check that the data attributes have been incorporated into the
        # properties
        self.assertEqual(data.get('foo'), 'bar')

        self.assertIn('submitter', data)
        self.assertIsNotNone(data['submitter'])
        self.assertEqual(data['submitter']['id'], self.submitter.id)

        # visible should be true by default
        self.assertTrue(data.get('visible'))

        # private-secrets is not special, but is private, so should not come
        # back down
        self.assertNotIn('private-email', data)

        # Check that we actually created a submission and set
        final_num_submissions = Submission.objects.all().count()
        self.assertEqual(final_num_submissions, start_num_submissions + 1)

    @unittest.skip("TODO: figure out what the desired behavior for bulk PUT is.")
    def test_PUT_creates_in_bulk(self):
        # Create a couple bogus places so that we can be sure we're not
        # inadvertantly deleting them
        Submission.objects.create(dataset=self.dataset, place=self.place, set_name='comments')
        Submission.objects.create(dataset=self.dataset, place=self.place, set_name='comments')

        # Make some data that will update the place, and create another
        submission_data = json.dumps([
            {
                'submitter_name': 'Andy',
                'private-email': 'abc@example.com',
                'foo': 'bar'
            },
            {
                'submitter_name': 'Mjumbe',
                'private-email': 'def@example.com',
                'foo': 'baz'
            }
        ])
        start_num_submissions = Submission.objects.all().count()

        #
        # View should 401 when trying to update when not authenticated
        #
        request = self.factory.put(self.path, data=submission_data, content_type='application/json')
        response = self.view(request, **self.request_kwargs)
        self.assertStatusCode(response, 401)

        #
        # View should update the places when owner is authenticated
        #
        request = self.factory.put(self.path, data=submission_data, content_type='application/json')
        request.META[KEY_HEADER] = self.apikey.key

        response = self.view(request, **self.request_kwargs)

        # Check that the request was successful
        self.assertStatusCode(response, 200)
        data_list = json.loads(response.rendered_content)

        self.assertEqual(len(data_list), 2)

        ### Check that we actually created the places
        final_num_submissions = Submission.objects.all().count()
        self.assertEqual(final_num_submissions, start_num_submissions + 2)

    @unittest.skip("TODO: figure out what the desired behavior for bulk PUT is.")
    def test_PUT_response_creates_and_updates_at_once(self):
        # Create a couple bogus places so that we can be sure we're not
        # inadvertantly deleting them
        Submission.objects.create(dataset=self.dataset, place=self.place, set_name='comments')
        Submission.objects.create(dataset=self.dataset, place=self.place, set_name='comments')

        # Create a submission
        submission = Submission.objects.create(dataset=self.dataset, place=self.place, set_name='comments')

        # Make some data that will update the submission, and create another
        submission_data = json.dumps([
            {
                'submitter_name': 'Andy',
                'private-email': 'abc@example.com',
                'foo': 'bar',
                'id': submission.id,
                'url': 'http://testserver/api/v2/aaron/datasets/ds/places/%s/comments/%s' % (self.place.id, submission.id)
            },
            {
                'submitter_name': 'Mjumbe',
                'private-email': 'def@example.com',
                'foo': 'baz'
            }
        ])
        start_num_submissions = Submission.objects.all().count()

        #
        # View should 401 when trying to update when not authenticated
        #
        request = self.factory.put(self.path, data=submission_data, content_type='application/json')
        response = self.view(request, **self.request_kwargs)
        self.assertStatusCode(response, 401)

        #
        # View should update the places when owner is authenticated
        #
        request = self.factory.put(self.path, data=submission_data, content_type='application/json')
        request.META[KEY_HEADER] = self.apikey.key

        response = self.view(request, **self.request_kwargs)

        # Check that the request was successful
        self.assertStatusCode(response, 200)
        data_list = json.loads(response.rendered_content)

        self.assertEqual(len(data_list), 2)

        ### Check the updated item
        data = [item for item in data_list if item['id'] == submission.id][0]

        # Check that the data attributes have been incorporated into the
        # properties
        self.assertEqual(data.get('foo'), 'bar')
        self.assertEqual(data.get('submitter_name'), 'Andy')

        # visible should be true by default
        self.assertTrue(data.get('visible'))

        # private-secrets is not special, but is private, so should not come
        # back down
        self.assertNotIn('private-email', data)

        ### Check the created item
        data = [item for item in data_list if item['id'] != submission.id][0]

        # Check that the data attributes have been incorporated into the
        # properties
        self.assertEqual(data.get('foo'), 'baz')
        self.assertEqual(data.get('submitter_name'), 'Mjumbe')

        ### Check that we actually created the places
        final_num_submissions = Submission.objects.all().count()
        self.assertEqual(final_num_submissions, start_num_submissions + 1)

    def test_GET_response_with_invisible_data(self):
        #
        # View should not return invisible data normally
        #
        request = self.factory.get(self.path)
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 200)
        self.assertEqual(len(data['results']), 2)

        # --------------------------------------------------

        #
        # View should 401 when not allowed to request private data (not authenticated)
        #
        request = self.factory.get(self.path + '?include_invisible')
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was restricted
        self.assertStatusCode(response, 401)

        # --------------------------------------------------

        #
        # View should 403 when not allowed to request private data (api key)
        #
        request = self.factory.get(self.path + '?include_invisible')
        request.META[KEY_HEADER] = self.apikey.key
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was restricted
        self.assertStatusCode(response, 403)

        # --------------------------------------------------

        #
        # View should 403 when not allowed to request private data (not owner)
        #
        request = self.factory.get(self.path + '?include_invisible')
        request.user = User.objects.create(username='new_user', password='password')
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was restricted
        self.assertStatusCode(response, 403)

        # --------------------------------------------------

        #
        # View should return private data when owner is logged in (Session Auth)
        #
        request = self.factory.get(self.path + '?include_invisible')
        request.user = self.owner
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 200)
        self.assertEqual(len(data['results']), 3)

        # --------------------------------------------------

        #
        # View should return private data when owner is logged in (Basic Auth)
        #
        request = self.factory.get(self.path + '?include_invisible')
        credentials = ':'.join([self.owner.username, '123']).encode()
        request.META['HTTP_AUTHORIZATION'] = 'Basic ' + base64.b64encode(credentials).decode()
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 200)
        self.assertEqual(len(data['results']), 3)

    def test_POST_invisible_response(self):
        place_data = json.dumps({
          'submitter_name': 'Andy',
          'type': 'Park Bench',
          'private-secrets': 'The mayor loves this bench',
          'geometry': {"type": "Point", "coordinates": [-73.99, 40.75]},
          'visible': False
        })

        request = self.factory.post(self.path, data=place_data, content_type='application/json')
        request.META[KEY_HEADER] = self.apikey.key
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 201)

        # Check that visible is false
        self.assertEqual(data.get('visible'), False)

    def test_POST_to_new_submission_set_response(self):
        request_kwargs = {
          'owner_username': self.owner.username,
          'dataset_slug': self.dataset.slug,
          'place_id': self.place.id,
          'submission_set_name': 'new-set'
        }

        path = reverse('submission-list', kwargs=request_kwargs)

        submission_data = json.dumps({
          'submitter_name': 'Andy',
          'private-email': 'abc@example.com',
          'foo': 'bar'
        })
        start_num_submissions = Submission.objects.all().count()

        #
        # View should 401 when trying to create when not authenticated
        #
        request = self.factory.post(path, data=submission_data, content_type='application/json')
        response = self.view(request, **request_kwargs)
        self.assertStatusCode(response, 401)

        #
        # View should create the submission and set when owner is authenticated
        #
        request = self.factory.post(path, data=submission_data, content_type='application/json')
        request.META[KEY_HEADER] = self.apikey.key

        response = self.view(request, **request_kwargs)

        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 201)

        # Check that the data attributes have been incorporated into the
        # properties
        self.assertEqual(data.get('foo'), 'bar')
        self.assertEqual(data.get('submitter_name'), 'Andy')

        # visible should be true by default
        self.assertTrue(data.get('visible'))

        # private-secrets is not special, but is private, so should not come
        # back down
        self.assertNotIn('private-email', data)

        # Check that we actually created a submission and set
        final_num_submissions = Submission.objects.all().count()
        self.assertEqual(final_num_submissions, start_num_submissions + 1)


class TestDataSetSubmissionListView (APITestMixin, TestCase):
    def setUp(self):
        cache_buffer.reset()
        django_cache.clear()

        self.owner_password = '123'
        self.owner = User.objects.create_user(
            username='aaron',
            password=self.owner_password,
            email='abc@example.com')
        self.submitter = User.objects.create_user(
            username='mjumbe',
            password='456',
            email='123@example.com')
        self.dataset = DataSet.objects.create(slug='ds', owner=self.owner)
        self.place1 = Place.objects.create(
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
        self.submissions1 = [
          Submission.objects.create(place=self.place1, set_name='comments', dataset=self.dataset, data='{"comment": "Wow!", "private-email": "abc@example.com", "foo": 3}'),
          Submission.objects.create(place=self.place1, set_name='comments', dataset=self.dataset, data='{"foo": 3}'),
          Submission.objects.create(place=self.place1, set_name='comments', dataset=self.dataset, data='{"foo": 3}', visible=False),
          Submission.objects.create(place=self.place1, set_name='likes', dataset=self.dataset, data='{"bar": 3}'),
          Submission.objects.create(place=self.place1, set_name='likes', dataset=self.dataset, data='{"bar": 3}'),
          Submission.objects.create(place=self.place1, set_name='likes', dataset=self.dataset, data='{"bar": 3}'),
          Submission.objects.create(place=self.place1, set_name='likes', dataset=self.dataset, data='{"bar": 3}', visible=False),
        ]
        self.submission1 = self.submissions1[0]

        self.place2 = Place.objects.create(
          dataset=self.dataset,
          geometry='POINT(2 3)',
          submitter=self.submitter,
          data=json.dumps({
            'type': 'ATM',
            'name': 'K-Mart',
            'private-secrets': 42
          }),
        )
        self.submissions2 = [
          Submission.objects.create(place=self.place2, set_name='comments', dataset=self.dataset, data='{"comment": "Wow!", "private-email": "abc@example.com", "foo": 3}'),
          Submission.objects.create(place=self.place2, set_name='comments', dataset=self.dataset, data='{"foo": 3}'),
          Submission.objects.create(place=self.place2, set_name='comments', dataset=self.dataset, data='{"foo": 3}', visible=False),
          Submission.objects.create(place=self.place2, set_name='likes', dataset=self.dataset, data='{"bar": 3}'),
          Submission.objects.create(place=self.place2, set_name='likes', dataset=self.dataset, data='{"bar": 3}'),
          Submission.objects.create(place=self.place2, set_name='likes', dataset=self.dataset, data='{"bar": 3}'),
          Submission.objects.create(place=self.place2, set_name='likes', dataset=self.dataset, data='{"bar": 3}', visible=False),
        ]
        self.submission2 = self.submissions2[0]

        # These are mainly around to ensure that we don't get spillover from
        # other datasets.
        dataset2 = DataSet.objects.create(slug='ds2', owner=self.owner)
        place3 = Place.objects.create(
          dataset=dataset2,
          geometry='POINT(3 4)',
        )
        submissions3 = [
          Submission.objects.create(place=place3, set_name='comments', dataset=dataset2, data='{"comment": "Wow!", "private-email": "abc@example.com", "foo": 3}'),
          Submission.objects.create(place=place3, set_name='comments', dataset=dataset2, data='{"foo": 3}'),
          Submission.objects.create(place=place3, set_name='comments', dataset=dataset2, data='{"foo": 3}', visible=False),
        ]

        self.apikey = ApiKey.objects.create(key='abc', dataset=self.dataset)

        self.request_kwargs = {
          'owner_username': self.owner.username,
          'dataset_slug': self.dataset.slug,
          'submission_set_name': 'comments'
        }

        self.factory = RequestFactory()
        self.path = reverse('dataset-submission-list', kwargs=self.request_kwargs)
        self.view = DataSetSubmissionListView.as_view()

    def tearDown(self):
        User.objects.all().delete()
        DataSet.objects.all().delete()
        Place.objects.all().delete()
        Submission.objects.all().delete()
        ApiKey.objects.all().delete()

        cache_buffer.reset()
        django_cache.clear()

    def test_GET_response(self):
        request = self.factory.get(self.path)
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 200)

        # Check that it's a results collection
        self.assertIn('results', data)
        self.assertIn('metadata', data)

        # Check that the metadata looks right
        self.assertIn('length', data['metadata'])
        self.assertIn('next', data['metadata'])
        self.assertIn('previous', data['metadata'])
        self.assertIn('page', data['metadata'])

        # Check that we have the right number of results
        self.assertEqual(len(data['results']), 4)

        urls = [result['url'] for result in data['results']]
        self.assertIn(
            'http://testserver' + reverse('submission-detail', args=[
                self.owner.username, self.dataset.slug, self.place1.id,
                self.submission1.set_name, self.submission1.id]),
            urls)

    def test_GET_csv_response(self):
        request = self.factory.get(self.path + '?format=csv')
        response = self.view(request, **self.request_kwargs)

        rows = list(csv.reader(StringIO(response.rendered_content.decode())))
        headers = rows[0]

        # Check that the request was successful
        self.assertStatusCode(response, 200)

        # Check that it's got good headers
        self.assertIn('dataset', headers)
        self.assertIn('comment', headers)
        self.assertIn('foo', headers)

        # Check that we have the right number of rows
        self.assertEqual(len(rows), 5)

    def test_GET_filtered_response(self):
        Submission.objects.create(dataset=self.dataset, place=self.place1, set_name='comments', data=json.dumps({'baz': 'bar', 'name': 1})),
        Submission.objects.create(dataset=self.dataset, place=self.place2, set_name='comments', data=json.dumps({'baz': 'bar', 'name': 2})),
        Submission.objects.create(dataset=self.dataset, place=self.place1, set_name='comments', data=json.dumps({'baz': 'bam', 'name': 3})),
        Submission.objects.create(dataset=self.dataset, place=self.place2, set_name='comments', data=json.dumps({'name': 4})),

        request = self.factory.get(self.path + '?baz=bar')
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that there are ATM features
        self.assertStatusCode(response, 200)
        self.assertTrue(all([result.get('baz') == 'bar' for result in data['results']]))
        self.assertEqual(len(data['results']), 2)

        request = self.factory.get(self.path + '?baz=qux')
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 200)
        self.assertEqual(len(data['results']), 0)

        request = self.factory.get(self.path + '?nonexistent=foo')
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 200)
        self.assertEqual(len(data['results']), 0)

    def test_GET_response_with_private_data(self):
        #
        # View should not return private data normally
        #
        request = self.factory.get(self.path)
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 200)

        # Check that the private data is not in the properties
        self.assertNotIn('private-email', data['results'][0])

        # --------------------------------------------------

        #
        # View should 401 when not allowed to request private data (not authenticated)
        #
        request = self.factory.get(self.path + '?include_private')
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was restricted
        self.assertStatusCode(response, 401)

        # --------------------------------------------------

        #
        # View should 403 when not allowed to request private data (api key)
        #
        request = self.factory.get(self.path + '?include_private')
        request.META[KEY_HEADER] = self.apikey.key
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was restricted
        self.assertStatusCode(response, 403)

        # --------------------------------------------------

        #
        # View should 403 when not allowed to request private data (not owner)
        #
        request = self.factory.get(self.path + '?include_private')
        request.user = User.objects.create(username='new_user', password='password')
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was restricted
        self.assertStatusCode(response, 403)

        # --------------------------------------------------

        #
        # View should return private data when owner is logged in (Session Auth)
        #
        request = self.factory.get(self.path + '?include_private')
        request.user = self.owner
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 200)

        # Check that the private data is in the properties
        results_with_private_email = [result for result in data['results'] if 'private-email' in result]
        self.assertNotEqual(len(results_with_private_email), 0)

        # --------------------------------------------------

        #
        # View should return private data when owner is logged in (Basic Auth)
        #
        request = self.factory.get(self.path + '?include_private')
        credentials = ':'.join([self.owner.username, '123']).encode()
        request.META['HTTP_AUTHORIZATION'] = 'Basic ' + base64.b64encode(credentials).decode()
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 200)

        # Check that the private data is in the properties
        results_with_private_email = [result for result in data['results'] if 'private-email' in result]
        self.assertNotEqual(len(results_with_private_email), 0)

    def test_GET_invalid_url(self):
        # Make sure that we respond with 404 if a slug is supplied, but for
        # the wrong dataset or owner.
        request_kwargs = {
          'owner_username': 'mischevious_owner',
          'dataset_slug': self.dataset.slug,
          'submission_set_name': 'comments'
        }

        path = reverse('dataset-submission-list', kwargs=request_kwargs)
        request = self.factory.get(path)
        response = self.view(request, **request_kwargs)

        self.assertStatusCode(response, 404)

    def test_GET_response_with_invisible_data(self):
        #
        # View should not return invisible data normally
        #
        request = self.factory.get(self.path)
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 200)
        self.assertEqual(len(data['results']), 4)

        # --------------------------------------------------

        #
        # View should 401 when not allowed to request private data (not authenticated)
        #
        request = self.factory.get(self.path + '?include_invisible')
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was restricted
        self.assertStatusCode(response, 401)

        # --------------------------------------------------

        #
        # View should 403 when not allowed to request private data (api key)
        #
        request = self.factory.get(self.path + '?include_invisible')
        request.META[KEY_HEADER] = self.apikey.key
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was restricted
        self.assertStatusCode(response, 403)

        # --------------------------------------------------

        #
        # View should 403 when not allowed to request private data (not owner)
        #
        request = self.factory.get(self.path + '?include_invisible')
        request.user = User.objects.create(username='new_user', password='password')
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was restricted
        self.assertStatusCode(response, 403)

        # --------------------------------------------------

        #
        # View should return private data when owner is logged in (Session Auth)
        #
        request = self.factory.get(self.path + '?include_invisible')
        request.user = self.owner
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 200)
        self.assertEqual(len(data['results']), 6)

        # --------------------------------------------------

        #
        # View should return private data when owner is logged in (Basic Auth)
        #
        request = self.factory.get(self.path + '?include_invisible')
        credentials = ':'.join([self.owner.username, '123']).encode()
        request.META['HTTP_AUTHORIZATION'] = 'Basic ' + base64.b64encode(credentials).decode()
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 200)
        self.assertEqual(len(data['results']), 6)


class TestDataSetInstanceView (APITestMixin, TestCase):
    def setUp(self):
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
        self.submissions = [
          Submission.objects.create(place=self.place, set_name='comments', dataset=self.dataset, data='{"comment": "Wow!", "private-email": "abc@example.com", "foo": 3}'),
          Submission.objects.create(place=self.place, set_name='comments', dataset=self.dataset, data='{"foo": 3}'),
          Submission.objects.create(place=self.place, set_name='comments', dataset=self.dataset, data='{"foo": 3}', visible=False),
          Submission.objects.create(place=self.place, set_name='likes', dataset=self.dataset, data='{"bar": 3}'),
          Submission.objects.create(place=self.place, set_name='likes', dataset=self.dataset, data='{"bar": 3}'),
          Submission.objects.create(place=self.place, set_name='likes', dataset=self.dataset, data='{"bar": 3}'),
          Submission.objects.create(place=self.place, set_name='likes', dataset=self.dataset, data='{"bar": 3}', visible=False),
        ]
        self.submission = self.submissions[0]


        self.invisible_place = Place.objects.create(
          dataset=self.dataset,
          geometry='POINT(3 4)',
          submitter=self.submitter,
          visible=False,
          data=json.dumps({
            'type': 'ATM',
            'name': 'K-Mart',
          }),
        )

        self.apikey = ApiKey.objects.create(key='abc', dataset=self.dataset)

        self.request_kwargs = {
          'owner_username': self.owner.username,
          'dataset_slug': self.dataset.slug
        }

        self.factory = RequestFactory()
        self.path = reverse('dataset-detail', kwargs=self.request_kwargs)
        self.view = DataSetInstanceView.as_view()

        cache_buffer.reset()
        django_cache.clear()

    def tearDown(self):
        User.objects.all().delete()
        DataSet.objects.all().delete()
        Place.objects.all().delete()
        Submission.objects.all().delete()
        ApiKey.objects.all().delete()

        cache_buffer.reset()
        django_cache.clear()

    def test_anonymous_GET_response(self):
        request = self.factory.get(self.path)
        response = self.view(request, **self.request_kwargs)

        # Check that the request was successful
        self.assertStatusCode(response, 200)

    def test_GET_response(self):
        request = self.factory.get(self.path)
        request.user = self.owner
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 200)

        # Check that data attribute is not present
        self.assertNotIn('data', data)

        # Check that the appropriate attributes are in the properties
        self.assertIn('url', data)
        self.assertIn('slug', data)
        self.assertIn('display_name', data)
        self.assertNotIn('keys', data)
        self.assertIn('owner', data)
        self.assertIn('places', data)
        self.assertIn('submission_sets', data)

        # Check that the URL is right
        self.assertEqual(data['url'],
            'http://testserver' + reverse('dataset-detail', args=[
                self.owner.username, self.dataset.slug]))

    #
    # Temporarily disable caching on datasets until we add user data to the
    # cache keys.
    #
    # def test_GET_from_cache(self):
    #     path = reverse('dataset-detail', kwargs=self.request_kwargs)
    #     request = self.factory.get(path)

    #     # Check that we make a finite number of queries
    #     # - SELECT * FROM sa_api_dataset
    #     #       INNER JOIN auth_user ON (owner_id = auth_user.id)
    #     #       WHERE (username = '<owner_username>'  AND slug = '<dataset_slug>' );
    #     #
    #     # - SELECT * FROM sa_api_submittedthing
    #     #       WHERE dataset_id IN (<dataset_id>);
    #     #
    #     # - SELECT * FROM sa_api_place
    #     #       INNER JOIN sa_api_submittedthing ON (submittedthing_ptr_id = sa_api_submittedthing.id)
    #     #       WHERE submittedthing_ptr_id IN (<place_ids>);
    #     #
    #     # - SELECT * FROM "auth_user"
    #     #       WHERE id = <owner_id>;
    #     #
    #     # - SELECT COUNT(*) FROM sa_api_place
    #     #       INNER JOIN sa_api_submittedthing ON (submittedthing_ptr_id = sa_api_submittedthing.id)
    #     #       WHERE dataset_id = <dataset_id>  AND visible = True;
    #     #
    #     # - SELECT sa_api_submittedthing.dataset_id, sa_api_submissionset.name, COUNT(*) AS "length" FROM sa_api_submission
    #     #       LEFT OUTER JOIN sa_api_submittedthing ON (submittedthing_ptr_id = sa_api_submittedthing.id)
    #     #       INNER JOIN sa_api_submissionset ON (parent_id = sa_api_submissionset.id)
    #     #       WHERE dataset_id = <dataset_id>
    #     #       GROUP BY dataset_id, sa_api_submissionset.name;
    #     with self.assertNumQueries(6):
    #         response = self.view(request, **self.request_kwargs)
    #         self.assertStatusCode(response, 200)

    #     path = reverse('dataset-detail', kwargs=self.request_kwargs)
    #     request = self.factory.get(path)

    #     # Check that this performs no more queries, since it's all cached
    #     with self.assertNumQueries(0):
    #         response = self.view(request, **self.request_kwargs)
    #         self.assertStatusCode(response, 200)

    def test_DELETE_response(self):
        #
        # View should 401 when trying to delete when not authenticated
        #
        request = self.factory.delete(self.path)
        response = self.view(request, **self.request_kwargs)
        self.assertStatusCode(response, 401)

        #
        # View should 401 or 403 when authenticated with an API key
        #
        request = self.factory.delete(self.path)
        request.META[KEY_HEADER] = self.apikey.key
        response = self.view(request, **self.request_kwargs)

        # Check that the request was successful
        self.assertIn(response.status_code, (401, 403))

        #
        # View should delete the dataset when owner is directly authenticated
        #
        request = self.factory.delete(self.path)
        credentials = ':'.join([self.owner.username, '123']).encode()
        request.META['HTTP_AUTHORIZATION'] = 'Basic ' + base64.b64encode(credentials).decode()
        response = self.view(request, **self.request_kwargs)

        # Check that the request was successful
        self.assertStatusCode(response, 204)

        # Check that no data was returned
        self.assertIsNone(response.data)

    def test_GET_response_with_invisible_data(self):
        #
        # View should not return invisible data normally
        #
        request = self.factory.get(self.path)
        request.user = self.owner
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 200)
        self.assertEqual(data['submission_sets']['likes']['length'], 3)

        # --------------------------------------------------

        #
        # View should 401 when not allowed to request private data (not authenticated)
        #
        request = self.factory.get(self.path + '?include_invisible')
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was restricted
        self.assertStatusCode(response, 401)

        # --------------------------------------------------

        #
        # View should 403 when not allowed to request private data (api key)
        #
        request = self.factory.get(self.path + '?include_invisible')
        request.META[KEY_HEADER] = self.apikey.key
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was restricted
        self.assertIn(response.status_code, (401, 403))

        # --------------------------------------------------

        #
        # View should 403 when not allowed to request private data (not owner)
        #
        request = self.factory.get(self.path + '?include_invisible')
        request.user = User.objects.create(username='new_user', password='password')
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was restricted
        self.assertStatusCode(response, 403)

        # --------------------------------------------------

        #
        # View should return private data when owner is logged in (Session Auth)
        #
        request = self.factory.get(self.path + '?include_invisible')
        request.user = self.owner
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 200)
        self.assertEqual(data['submission_sets']['likes']['length'], 4)

        # --------------------------------------------------

        #
        # View should return private data when owner is logged in (Basic Auth)
        #
        request = self.factory.get(self.path + '?include_invisible')
        credentials = ':'.join([self.owner.username, '123']).encode()
        request.META['HTTP_AUTHORIZATION'] = 'Basic ' + base64.b64encode(credentials).decode()
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 200)
        self.assertEqual(data['submission_sets']['likes']['length'], 4)

    def test_PUT_response(self):
        dataset_data = json.dumps({
          'slug': 'newds',
          'display_name': 'New Name for the DataSet'
        })

        #
        # View should 401 when trying to update when not authenticated
        #
        request = self.factory.put(self.path, data=dataset_data, content_type='application/json')
        response = self.view(request, **self.request_kwargs)
        self.assertStatusCode(response, 401)

        #
        # View should 401 or 403 when authenticated with API key
        #
        request = self.factory.put(self.path, data=dataset_data, content_type='application/json')
        request.META[KEY_HEADER] = self.apikey.key
        response = self.view(request, **self.request_kwargs)
        self.assertIn(response.status_code, (401, 403))

        #
        # View should update the place and 301 when owner is authenticated
        #
        request = self.factory.put(self.path, data=dataset_data, content_type='application/json')
        credentials = ':'.join([self.owner.username, '123']).encode()
        request.META['HTTP_AUTHORIZATION'] = 'Basic ' + base64.b64encode(credentials).decode()

        response = self.view(request, **self.request_kwargs)

        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 301)

        # Check that the summaries have been incorporated into the data
        self.assertEqual(data.get('places').get('length'), 1)
        self.assertEqual(data.get('submission_sets').get('likes').get('length'), 3)


class TestDataSetListView (APITestMixin, TestCase):
    def setUp(self):
        cache_buffer.reset()
        django_cache.clear()

        self.owner_password = '123'
        self.owner = User.objects.create_user(
            username='aaron',
            password=self.owner_password,
            email='abc@example.com')
        self.submitter = User.objects.create_user(
            username='mjumbe',
            password='456',
            email='123@example.com')
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
          Submission.objects.create(place=self.place, set_name='comments', dataset=self.dataset, data='{"comment": "Wow!", "private-email": "abc@example.com", "foo": 3}'),
          Submission.objects.create(place=self.place, set_name='comments', dataset=self.dataset, data='{"foo": 3}'),
          Submission.objects.create(place=self.place, set_name='comments', dataset=self.dataset, data='{"foo": 3}', visible=False),
          Submission.objects.create(place=self.place, set_name='likes', dataset=self.dataset, data='{"bar": 3}'),
          Submission.objects.create(place=self.place, set_name='likes', dataset=self.dataset, data='{"bar": 3}'),
          Submission.objects.create(place=self.place, set_name='likes', dataset=self.dataset, data='{"bar": 3}'),
          Submission.objects.create(place=self.place, set_name='likes', dataset=self.dataset, data='{"bar": 3}', visible=False),
        ]
        self.submission = self.submissions[0]

        # These are mainly around to ensure that we don't get spillover from
        # other datasets.
        dataset2 = DataSet.objects.create(slug='ds2', owner=self.owner)
        place2 = Place.objects.create(
          dataset=dataset2,
          geometry='POINT(3 4)',
        )
        submissions2 = [
          Submission.objects.create(place=place2, set_name='comments', dataset=dataset2, data='{"comment": "Wow!", "private-email": "abc@example.com", "foo": 3}'),
          Submission.objects.create(place=place2, set_name='comments', dataset=dataset2, data='{"foo": 3}'),
          Submission.objects.create(place=place2, set_name='comments', dataset=dataset2, data='{"foo": 3}', visible=False),
        ]

        other_owner = User.objects.create_user(
            username='frank',
            password='789',
            email='def@example.com')
        dataset3 = DataSet.objects.create(owner=other_owner, slug='slug', display_name="Display Name")

        self.apikey = ApiKey.objects.create(key='abc', dataset=self.dataset)

        self.request_kwargs = {
          'owner_username': self.owner.username,
        }

        self.factory = RequestFactory()
        self.path = reverse('dataset-list', kwargs=self.request_kwargs)
        self.view = DataSetListView.as_view()

    def tearDown(self):
        User.objects.all().delete()
        DataSet.objects.all().delete()
        Place.objects.all().delete()
        Submission.objects.all().delete()
        ApiKey.objects.all().delete()

        cache_buffer.reset()
        django_cache.clear()

    def test_anonymous_GET_response(self):
        request = self.factory.get(self.path)
        response = self.view(request, **self.request_kwargs)

        # Check that the request was successful
        self.assertStatusCode(response, 200)

    def test_GET_response(self):
        request = self.factory.get(self.path)
        request.user = self.owner
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 200)

        # Check that it's a results collection
        self.assertIn('results', data)
        self.assertIn('metadata', data)

        # Check that the metadata looks right
        self.assertIn('length', data['metadata'])
        self.assertIn('next', data['metadata'])
        self.assertIn('previous', data['metadata'])
        self.assertIn('page', data['metadata'])

        # Check that we have the right number of results
        self.assertEqual(len(data['results']), 2)

        self.assertEqual(data['results'][0]['url'],
            'http://testserver' + reverse('dataset-detail', args=[
                self.owner.username, self.dataset.slug]))

    def test_POST_response(self):
        dataset_data = json.dumps({
          'slug': 'newds',
          'display_name': 'My New DataSet'
        })
        start_num_datasets = DataSet.objects.all().count()

        #
        # View should 401 when trying to create when not authenticated
        #
        request = self.factory.post(self.path, data=dataset_data, content_type='application/json')
        response = self.view(request, **self.request_kwargs)
        self.assertStatusCode(response, 401)

        #
        # View should 401 or 403 when trying to create with API key
        #
        request = self.factory.post(self.path, data=dataset_data, content_type='application/json')
        request.META[KEY_HEADER] = self.apikey.key
        response = self.view(request, **self.request_kwargs)
        self.assertIn(response.status_code, (401, 403))

        #
        # View should create the submission and set when owner is authenticated
        #
        request = self.factory.post(self.path, data=dataset_data, content_type='application/json')
        credentials = ':'.join([self.owner.username, '123']).encode()
        request.META['HTTP_AUTHORIZATION'] = 'Basic ' + base64.b64encode(credentials).decode()

        response = self.view(request, **self.request_kwargs)

        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 201)

        # Check that the dataset is empty
        self.assertEqual(data['places']['length'], 0)
        self.assertEqual(data['submission_sets'], {})

        # Check that we actually created a dataset
        final_num_datasets = DataSet.objects.all().count()
        self.assertEqual(final_num_datasets, start_num_datasets + 1)

    def test_POST_cloning_comma_separated_dataset(self):
        dataset_data = json.dumps({
          'slug': self.dataset.slug + '-clone',
        })
        start_num_datasets = DataSet.objects.all().count()

        #
        # View should create the submission and set when owner is authenticated
        #
        request = self.factory.post(self.path, data=dataset_data, content_type='application/json')
        credentials = ':'.join([self.owner.username, '123']).encode()
        request.META['HTTP_AUTHORIZATION'] = 'Basic ' + base64.b64encode(credentials).decode()
        request.META['HTTP_X_SHAREABOUTS_CLONE'] = ','.join([self.owner.username, self.dataset.slug])

        response = self.view(request, **self.request_kwargs)

        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 202)

        # Check that the dataset has the same name as the original
        # self.assertEqual(data['places']['length'], 0)
        # self.assertEqual(data['submission_sets'], {})
        self.assertEqual(data['display_name'], self.dataset.display_name)

        # Check that we actually created a dataset
        final_num_datasets = DataSet.objects.all().count()
        self.assertEqual(final_num_datasets, start_num_datasets + 1)

    def test_POST_cloning_dataset_url(self):
        dataset_data = json.dumps({
          'slug': self.dataset.slug + '-clone',
        })
        start_num_datasets = DataSet.objects.all().count()

        #
        # View should create the submission and set when owner is authenticated
        #
        request = self.factory.post(self.path, data=dataset_data, content_type='application/json')
        credentials = ':'.join([self.owner.username, '123']).encode()
        request.META['HTTP_AUTHORIZATION'] = 'Basic ' + base64.b64encode(credentials).decode()
        request.META['HTTP_X_SHAREABOUTS_CLONE'] = 'http://testserver' + reverse('dataset-detail', args=[self.owner.username, self.dataset.slug])

        response = self.view(request, **self.request_kwargs)

        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 202)

        # Check that the dataset has the same name as the original
        # self.assertEqual(data['places']['length'], 0)
        # self.assertEqual(data['submission_sets'], {})
        self.assertEqual(data['display_name'], self.dataset.display_name)

        # Check that we actually created a dataset
        final_num_datasets = DataSet.objects.all().count()
        self.assertEqual(final_num_datasets, start_num_datasets + 1)

    def test_POST_cloning_dataset_id(self):
        dataset_data = json.dumps({
          'slug': self.dataset.slug + '-clone',
        })
        start_num_datasets = DataSet.objects.all().count()

        #
        # View should create the submission and set when owner is authenticated
        #
        request = self.factory.post(self.path, data=dataset_data, content_type='application/json')
        credentials = ':'.join([self.owner.username, '123']).encode()
        request.META['HTTP_AUTHORIZATION'] = 'Basic ' + base64.b64encode(credentials).decode()
        request.META['HTTP_X_SHAREABOUTS_CLONE'] = str(self.dataset.id)

        response = self.view(request, **self.request_kwargs)

        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 202)

        # Check that the dataset has the same name as the original
        # self.assertEqual(data['places']['length'], 0)
        # self.assertEqual(data['submission_sets'], {})
        self.assertEqual(data['display_name'], self.dataset.display_name)

        # Check that we actually created a dataset
        final_num_datasets = DataSet.objects.all().count()
        self.assertEqual(final_num_datasets, start_num_datasets + 1)

    def test_POST_cloning_dataset_without_specifying_slug(self):
        dataset_data = json.dumps({})
        start_num_datasets = DataSet.objects.all().count()

        #
        # View should create the submission and set when owner is authenticated
        #
        request = self.factory.post(self.path, data=dataset_data, content_type='application/json')
        credentials = ':'.join([self.owner.username, '123']).encode()
        request.META['HTTP_AUTHORIZATION'] = 'Basic ' + base64.b64encode(credentials).decode()
        request.META['HTTP_X_SHAREABOUTS_CLONE'] = str(self.dataset.id)

        response = self.view(request, **self.request_kwargs)

        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 202)

        # Check that the dataset has the same name as the original
        # self.assertEqual(data['places']['length'], 0)
        # self.assertEqual(data['submission_sets'], {})
        self.assertEqual(data['display_name'], self.dataset.display_name)
        self.assertTrue(data['slug'].startswith(self.dataset.slug))

        # Check that we actually created a dataset
        final_num_datasets = DataSet.objects.all().count()
        self.assertEqual(final_num_datasets, start_num_datasets + 1)

    def test_get_all_submission_sets(self):
        request = self.factory.get(self.path)
        view = DataSetListView()
        view.request = request
        view.kwargs = self.request_kwargs

        sets = view.get_all_submission_sets()
        self.assertIn('likes', [s['set_name'] for s in sets[self.dataset.pk]])

    def test_GET_response_with_invisible_data(self):
        #
        # View should not return invisible data normally
        #
        request = self.factory.get(self.path)
        request.user = self.owner
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 200)
        self.assertEqual(data['results'][0]['places']['length'], 1)
        self.assertEqual(data['results'][0]['submission_sets']['likes']['length'], 3)

        # --------------------------------------------------

        #
        # View should 401 when not allowed to request private data (not authenticated)
        #
        request = self.factory.get(self.path + '?include_invisible')
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was restricted
        self.assertStatusCode(response, 401)

        # --------------------------------------------------

        #
        # View should 403 when not allowed to request private data (api key)
        #
        request = self.factory.get(self.path + '?include_invisible')
        request.META[KEY_HEADER] = self.apikey.key
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was restricted
        self.assertIn(response.status_code, (401, 403))

        # --------------------------------------------------

        #
        # View should 403 when not allowed to request private data (not owner)
        #
        request = self.factory.get(self.path + '?include_invisible')
        request.user = User.objects.create(username='new_user', password='password')
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was restricted
        self.assertStatusCode(response, 403)

        # --------------------------------------------------

        #
        # View should return private data when owner is logged in (Session Auth)
        #
        request = self.factory.get(self.path + '?include_invisible')
        request.user = self.owner
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 200)
        self.assertEqual(data['results'][0]['places']['length'], 2)
        self.assertIn('likes', data['results'][0]['submission_sets'])
        self.assertEqual(data['results'][0]['submission_sets']['likes']['length'], 4)

        # --------------------------------------------------

        #
        # View should return private data when owner is logged in (Basic Auth)
        #
        request = self.factory.get(self.path + '?include_invisible')
        credentials = ':'.join([self.owner.username, '123']).encode()
        request.META['HTTP_AUTHORIZATION'] = 'Basic ' + base64.b64encode(credentials).decode()
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 200)
        self.assertEqual(data['results'][0]['places']['length'], 2)
        self.assertEqual(data['results'][0]['submission_sets']['likes']['length'], 4)


class TestPlaceAttachmentListView (APITestMixin, TestCase):
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
            'name': 'K-Mart',
          }),
        )

        self.file = StringIO(u'This is test content in a "file"')
        self.file.name = 'myfile.txt'
        self.file.size = 20
        # self.attachments = Attachment.objects.create(
        #     file=File(f, 'myfile.txt'), name='my_file_name', thing=self.place)

        self.apikey = ApiKey.objects.create(key='abc', dataset=self.dataset)

        self.request_kwargs = {
          'owner_username': self.owner.username,
          'dataset_slug': self.dataset.slug,
          'thing_id': str(self.place.id)
        }

        self.invisible_request_kwargs = {
          'owner_username': self.owner.username,
          'dataset_slug': self.dataset.slug,
          'thing_id': str(self.invisible_place.id)
        }

        self.factory = RequestFactory()
        self.path = reverse('place-attachments', kwargs=self.request_kwargs)
        self.invisible_path = reverse('place-attachments', kwargs=self.invisible_request_kwargs)
        self.view = AttachmentListView.as_view()

    def tearDown(self):
        User.objects.all().delete()
        DataSet.objects.all().delete()
        Place.objects.all().delete()
        Submission.objects.all().delete()
        ApiKey.objects.all().delete()

        cache_buffer.reset()
        django_cache.clear()

    def test_GET_attachments_from_place(self):
        Attachment.objects.create(
            file=File(self.file, 'myfile.txt'), name='my_file_name', thing=self.place)

        request = self.factory.get(self.path)
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 200)

        # Check that the attachment looks right
        self.assertEqual(len(data['results']), 1)
        self.assertIn('file', data['results'][0])
        self.assertIn('name', data['results'][0])
        self.assertEqual(data['results'][0]['name'], 'my_file_name')

    def test_POST_attachment_to_place(self):
        #
        # Can't write if not authenticated
        #
        f = StringIO(u'This is test content in a "file"')
        f.name = 'myfile.txt'
        request = self.factory.post(self.path, data={'file': f, 'name': 'my-file'})
        response = self.view(request, **self.request_kwargs)
        self.assertStatusCode(response, 401, response.render())

        # --------------------------------------------------

        #
        # Can write with the API key.
        #
        f = StringIO(u'This is test content in a "file"')
        f.name = 'myfile.txt'
        request = self.factory.post(self.path, data={'file': f, 'name': 'my-file'})
        request.META[KEY_HEADER] = self.apikey.key
        response = self.view(request, **self.request_kwargs)

        # Check that the request was successful
        self.assertStatusCode(response, 201, response.render())

        # Check that the attachment looks right
        self.assertEqual(self.place.attachments.all().count(), 1)
        a = self.place.attachments.all()[0]
        self.assertEqual(a.name, 'my-file')
        self.assertEqual(a.file.read(), b'This is test content in a "file"')

        # --------------------------------------------------

        #
        # Can not write when logged in as not owner.
        #
        f = StringIO(u'This is test content in a "file"')
        f.name = 'myfile.txt'
        request = self.factory.post(self.path, data={'file': f, 'name': 'my-file'})
        User.objects.create_user(username='new_user', password='password')
        credentials =  ':'.join(['new_user', 'password']).encode()
        request.META['HTTP_AUTHORIZATION'] = 'Basic ' + base64.b64encode(credentials).decode()
        response = self.view(request, **self.request_kwargs)

        # Check that the request was successful
        self.assertStatusCode(response, 403, response.render())

        # --------------------------------------------------

        #
        # Can write when logged in as owner.
        #
        f = StringIO(u'This is test content in a "file"')
        f.name = 'myfile.txt'
        request = self.factory.post(self.path, data={'file': f, 'name': 'my-file'})
        credentials = ':'.join([self.owner.username, '123']).encode()
        request.META['HTTP_AUTHORIZATION'] = 'Basic ' + base64.b64encode(credentials).decode()
        response = self.view(request, **self.request_kwargs)

        # Check that the request was successful
        self.assertStatusCode(response, 201, response.render())

    def test_POST_attachment_to_invisible_place(self):
        #
        # Can't write if not authenticated
        #
        f = StringIO(u'This is test content in a "file"')
        f.name = 'myfile.txt'
        request = self.factory.post(self.invisible_path + '?include_invisible', data={'file': f, 'name': 'my-file'})
        response = self.view(request, **self.invisible_request_kwargs)
        self.assertStatusCode(response, 401, response.render())

        # --------------------------------------------------

        #
        # Can't write with the API key/include_invisible. (400)
        #
        f = StringIO(u'This is test content in a "file"')
        f.name = 'myfile.txt'
        request = self.factory.post(self.invisible_path, data={'file': f, 'name': 'my-file'})
        request.META[KEY_HEADER] = self.apikey.key
        response = self.view(request, **self.invisible_request_kwargs)
        self.assertStatusCode(response, 400, response.render())


        # --------------------------------------------------

        #
        # Can't write with the API key (403).
        #
        f = StringIO(u'This is test content in a "file"')
        f.name = 'myfile.txt'
        request = self.factory.post(self.invisible_path + '?include_invisible', data={'file': f, 'name': 'my-file'})
        request.META[KEY_HEADER] = self.apikey.key
        response = self.view(request, **self.invisible_request_kwargs)
        self.assertStatusCode(response, 403, response.render())

        # --------------------------------------------------

        #
        # Can not write when logged in as not owner.
        #
        f = StringIO(u'This is test content in a "file"')
        f.name = 'myfile.txt'
        request = self.factory.post(self.invisible_path + '?include_invisible', data={'file': f, 'name': 'my-file'})
        User.objects.create_user(username='new_user', password='password')
        credentials =  ':'.join(['new_user', 'password']).encode()
        request.META['HTTP_AUTHORIZATION'] = 'Basic ' + base64.b64encode(credentials).decode()
        response = self.view(request, **self.invisible_request_kwargs)

        # Check that the request was successful
        self.assertStatusCode(response, 403, response.render())

        # --------------------------------------------------

        #
        # Can't write when logged in as owner without include_invisible (400).
        #
        f = StringIO(u'This is test content in a "file"')
        f.name = 'myfile.txt'
        request = self.factory.post(self.invisible_path, data={'file': f, 'name': 'my-file'})
        credentials = ':'.join([self.owner.username, '123']).encode()
        request.META['HTTP_AUTHORIZATION'] = 'Basic ' + base64.b64encode(credentials).decode()
        response = self.view(request, **self.invisible_request_kwargs)
        self.assertStatusCode(response, 400, response.render())

        # --------------------------------------------------

        #
        # Can write when logged in as owner.
        #
        f = StringIO(u'This is test content in a "file"')
        f.name = 'myfile.txt'
        request = self.factory.post(self.invisible_path + '?include_invisible', data={'file': f, 'name': 'my-file'})
        credentials = ':'.join([self.owner.username, '123']).encode()
        request.META['HTTP_AUTHORIZATION'] = 'Basic ' + base64.b64encode(credentials).decode()
        response = self.view(request, **self.invisible_request_kwargs)

        # Check that the request was successful
        self.assertStatusCode(response, 201, response.render())

    def test_GET_attachments_from_invisible_place(self):
        #
        # View should not return invisible data normally
        #
        request = self.factory.get(self.invisible_path)
        response = self.view(request, **self.invisible_request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 400)

        # --------------------------------------------------

        #
        # View should 401 when not allowed to request private data (not authenticated)
        #
        request = self.factory.get(self.invisible_path + '?include_invisible')
        response = self.view(request, **self.invisible_request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was restricted
        self.assertStatusCode(response, 401)

        # --------------------------------------------------

        #
        # View should 403 when not allowed to request private data (api key)
        #
        request = self.factory.get(self.invisible_path + '?include_invisible')
        request.META[KEY_HEADER] = self.apikey.key
        response = self.view(request, **self.invisible_request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was restricted
        self.assertStatusCode(response, 403)

        # --------------------------------------------------

        #
        # View should 403 when not allowed to request private data (not owner)
        #
        request = self.factory.get(self.invisible_path + '?include_invisible')
        request.user = User.objects.create(username='new_user', password='password')
        response = self.view(request, **self.invisible_request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was restricted
        self.assertStatusCode(response, 403)

        # --------------------------------------------------

        #
        # View should return private data when owner is logged in (Session Auth)
        #
        request = self.factory.get(self.invisible_path + '?include_invisible')
        request.user = self.owner
        response = self.view(request, **self.invisible_request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 200)

        # --------------------------------------------------

        #
        # View should return private data when owner is logged in (Basic Auth)
        #
        request = self.factory.get(self.invisible_path + '?include_invisible')
        credentials = ':'.join([self.owner.username, '123']).encode()
        request.META['HTTP_AUTHORIZATION'] = 'Basic ' + base64.b64encode(credentials).decode()
        response = self.view(request, **self.invisible_request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 200)

        # --------------------------------------------------

        #
        # View should 400 when owner is logged in but doesn't request invisible
        #
        request = self.factory.get(self.invisible_path)
        request.user = self.owner
        response = self.view(request, **self.invisible_request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 400)


class TestSubmissionAttachmentListView (APITestMixin, TestCase):
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
            'name': 'K-Mart',
          }),
        )

        self.submissions = [
          Submission.objects.create(place=self.place, set_name='comments', dataset=self.dataset, data='{"foo": 3}'),
          Submission.objects.create(place=self.place, set_name='comments', dataset=self.dataset, data='{"foo": 3}', visible=False),
        ]

        self.file = StringIO(u'This is test content in a "file"')
        self.file.name = 'myfile.txt'
        self.file.size = 20

        self.apikey = ApiKey.objects.create(key='abc', dataset=self.dataset)

        self.request_kwargs = {
          'owner_username': self.owner.username,
          'dataset_slug': self.dataset.slug,
          'place_id': self.place.id,
          'submission_set_name': 'comments',
          'thing_id': str(self.submissions[0].id)
        }

        self.invisible_request_kwargs = {
          'owner_username': self.owner.username,
          'dataset_slug': self.dataset.slug,
          'place_id': self.place.id,
          'submission_set_name': 'comments',
          'thing_id': str(self.submissions[1].id)
        }

        self.factory = RequestFactory()
        self.path = reverse('submission-attachments', kwargs=self.request_kwargs)
        self.invisible_path = reverse('submission-attachments', kwargs=self.invisible_request_kwargs)
        self.view = AttachmentListView.as_view()

    def tearDown(self):
        User.objects.all().delete()
        DataSet.objects.all().delete()
        Place.objects.all().delete()
        Submission.objects.all().delete()
        ApiKey.objects.all().delete()

        cache_buffer.reset()
        django_cache.clear()

    def test_GET_attachments_from_visible_submission(self):
        Attachment.objects.create(
            file=File(self.file, 'myfile.txt'), name='my_file_name', thing=self.submissions[0])

        request = self.factory.get(self.path)
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 200)

        # Check that the attachment looks right
        self.assertEqual(len(data['results']), 1)
        self.assertIn('file', data['results'][0])
        self.assertIn('name', data['results'][0])
        self.assertEqual(data['results'][0]['name'], 'my_file_name')

    def test_GET_attachments_from_invisible_submission(self):
        #
        # View should not return invisible data normally
        #
        request = self.factory.get(self.invisible_path)
        response = self.view(request, **self.invisible_request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 400)

        # --------------------------------------------------

        #
        # View should 401 when not allowed to request private data (not authenticated)
        #
        request = self.factory.get(self.invisible_path + '?include_invisible')
        response = self.view(request, **self.invisible_request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was restricted
        self.assertStatusCode(response, 401)

        # --------------------------------------------------

        #
        # View should 403 when not allowed to request private data (api key)
        #
        request = self.factory.get(self.invisible_path + '?include_invisible')
        request.META[KEY_HEADER] = self.apikey.key
        response = self.view(request, **self.invisible_request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was restricted
        self.assertStatusCode(response, 403)

        # --------------------------------------------------

        #
        # View should 403 when not allowed to request private data (not owner)
        #
        request = self.factory.get(self.invisible_path + '?include_invisible')
        request.user = User.objects.create(username='new_user', password='password')
        response = self.view(request, **self.invisible_request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was restricted
        self.assertStatusCode(response, 403)

        # --------------------------------------------------

        #
        # View should return private data when owner is logged in (Session Auth)
        #
        request = self.factory.get(self.invisible_path + '?include_invisible')
        request.user = self.owner
        response = self.view(request, **self.invisible_request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 200)

        # --------------------------------------------------

        #
        # View should return private data when owner is logged in (Basic Auth)
        #
        request = self.factory.get(self.invisible_path + '?include_invisible')
        credentials = ':'.join([self.owner.username, '123']).encode()
        request.META['HTTP_AUTHORIZATION'] = 'Basic ' + base64.b64encode(credentials).decode()
        response = self.view(request, **self.invisible_request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 200)

        # --------------------------------------------------

        #
        # View should 400 when owner is logged in but doesn't request invisible
        #
        request = self.factory.get(self.invisible_path)
        request.user = self.owner
        response = self.view(request, **self.invisible_request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that the request was successful
        self.assertStatusCode(response, 400)

    def test_POST_attachment_to_submission(self):
        #
        # Can't write if not authenticated
        #
        f = StringIO(u'This is test content in a "file"')
        f.name = 'myfile.txt'
        request = self.factory.post(self.path, data={'file': f, 'name': 'my-file'})
        response = self.view(request, **self.request_kwargs)
        self.assertStatusCode(response, 401, response.render())

        # --------------------------------------------------

        #
        # Can write with the API key.
        #
        f = StringIO(u'This is test content in a "file"')
        f.name = 'myfile.txt'
        request = self.factory.post(self.path, data={'file': f, 'name': 'my-file'})
        request.META[KEY_HEADER] = self.apikey.key
        response = self.view(request, **self.request_kwargs)

        # Check that the request was successful
        self.assertStatusCode(response, 201, response.render())

        # Check that the attachment looks right
        self.assertEqual(self.submissions[0].attachments.all().count(), 1)
        a = self.submissions[0].attachments.all()[0]
        self.assertEqual(a.name, 'my-file')
        self.assertEqual(a.file.read(), b'This is test content in a "file"')

        # --------------------------------------------------

        #
        # Can not write when logged in as not owner.
        #
        f = StringIO(u'This is test content in a "file"')
        f.name = 'myfile.txt'
        request = self.factory.post(self.path, data={'file': f, 'name': 'my-file'})
        User.objects.create_user(username='new_user', password='password')
        credentials =  ':'.join(['new_user', 'password']).encode()
        request.META['HTTP_AUTHORIZATION'] = 'Basic ' + base64.b64encode(credentials).decode()
        response = self.view(request, **self.request_kwargs)

        # Check that the request was successful
        self.assertStatusCode(response, 403, response.render())

        # --------------------------------------------------

        #
        # Can write when logged in as owner.
        #
        f = StringIO(u'This is test content in a "file"')
        f.name = 'myfile.txt'
        request = self.factory.post(self.path, data={'file': f, 'name': 'my-file'})
        credentials = ':'.join([self.owner.username, '123']).encode()
        request.META['HTTP_AUTHORIZATION'] = 'Basic ' + base64.b64encode(credentials).decode()
        response = self.view(request, **self.request_kwargs)

        # Check that the request was successful
        self.assertStatusCode(response, 201, response.render())

    def test_POST_attachment_to_invisible_submission(self):
        #
        # Can't write if not authenticated
        #
        f = StringIO(u'This is test content in a "file"')
        f.name = 'myfile.txt'
        request = self.factory.post(self.invisible_path + '?include_invisible', data={'file': f, 'name': 'my-file'})
        response = self.view(request, **self.invisible_request_kwargs)
        self.assertStatusCode(response, 401, response.render())

        # --------------------------------------------------

        #
        # Can't write with the API key/include_invisible. (400)
        #
        f = StringIO(u'This is test content in a "file"')
        f.name = 'myfile.txt'
        request = self.factory.post(self.invisible_path, data={'file': f, 'name': 'my-file'})
        request.META[KEY_HEADER] = self.apikey.key
        response = self.view(request, **self.invisible_request_kwargs)
        self.assertStatusCode(response, 400, response.render())


        # --------------------------------------------------

        #
        # Can't write with the API key (403).
        #
        f = StringIO(u'This is test content in a "file"')
        f.name = 'myfile.txt'
        request = self.factory.post(self.invisible_path + '?include_invisible', data={'file': f, 'name': 'my-file'})
        request.META[KEY_HEADER] = self.apikey.key
        response = self.view(request, **self.invisible_request_kwargs)
        self.assertStatusCode(response, 403, response.render())

        # --------------------------------------------------

        #
        # Can not write when logged in as not owner.
        #
        f = StringIO(u'This is test content in a "file"')
        f.name = 'myfile.txt'
        request = self.factory.post(self.invisible_path + '?include_invisible', data={'file': f, 'name': 'my-file'})
        User.objects.create_user(username='new_user', password='password')
        credentials =  ':'.join(['new_user', 'password']).encode()
        request.META['HTTP_AUTHORIZATION'] = 'Basic ' + base64.b64encode(credentials).decode()
        response = self.view(request, **self.invisible_request_kwargs)

        # Check that the request was successful
        self.assertStatusCode(response, 403, response.render())

        # --------------------------------------------------

        #
        # Can't write when logged in as owner without include_invisible (400).
        #
        f = StringIO(u'This is test content in a "file"')
        f.name = 'myfile.txt'
        request = self.factory.post(self.invisible_path, data={'file': f, 'name': 'my-file'})
        credentials = ':'.join([self.owner.username, '123']).encode()
        request.META['HTTP_AUTHORIZATION'] = 'Basic ' + base64.b64encode(credentials).decode()
        response = self.view(request, **self.invisible_request_kwargs)
        self.assertStatusCode(response, 400, response.render())

        # --------------------------------------------------

        #
        # Can write when logged in as owner.
        #
        f = StringIO(u'This is test content in a "file"')
        f.name = 'myfile.txt'
        request = self.factory.post(self.invisible_path + '?include_invisible', data={'file': f, 'name': 'my-file'})
        credentials = ':'.join([self.owner.username, '123']).encode()
        request.META['HTTP_AUTHORIZATION'] = 'Basic ' + base64.b64encode(credentials).decode()
        response = self.view(request, **self.invisible_request_kwargs)

        # Check that the request was successful
        self.assertStatusCode(response, 201, response.render())


class TestActivityView(APITestMixin, TestCase):

    def setUp(self):
        User.objects.all().delete()
        DataSet.objects.all().delete()
        Place.objects.all().delete()
        Submission.objects.all().delete()
        Action.objects.all().delete()

        self.owner = User.objects.create_user(username='myuser', password='123')
        self.dataset = DataSet.objects.create(slug='data',
                                              owner_id=self.owner.id)

        self.visible_place = Place.objects.create(dataset=self.dataset, geometry='POINT (0 0)', visible=True)
        self.invisible_place = Place.objects.create(dataset=self.dataset, geometry='POINT (0 0)', visible=False)

        self.visible_submission = Submission.objects.create(dataset=self.dataset, place=self.visible_place, set_name='vis')
        self.invisible_submission = Submission.objects.create(dataset=self.dataset, place=self.invisible_place, set_name='invis')
        self.invisible_submission2 = Submission.objects.create(dataset=self.dataset, place=self.visible_place, set_name='vis', visible=False)

        self.actions = [
            # Get existing activity for visible things that have been created
            Action.objects.get(thing=self.visible_place),
            Action.objects.get(thing=self.visible_submission),

            # Create some more activities for visible things
            Action.objects.create(thing=self.visible_place.submittedthing_ptr, action='update'),
            Action.objects.create(thing=self.visible_place.submittedthing_ptr, action='delete'),
        ]

        self.apikey = ApiKey.objects.create(key='abc', dataset=self.dataset)

        self.kwargs = {
            'owner_username': self.owner.username,
            'dataset_slug': 'data'
        }
        self.url = reverse('action-list', kwargs=self.kwargs)
        self.view = ActionListView.as_view()
        self.factory = RequestFactory()

        # This was here first and marked as deprecated, but above doesn't
        # work either.
        # self.url = reverse('activity_collection')

        cache_buffer.reset()
        django_cache.clear()

    def test_GET_with_no_params_returns_only_visible_things(self):
        request = self.factory.get(self.url)
        response = self.view(request, **self.kwargs)
        data = json.loads(response.rendered_content)

        self.assertIn('results', data)
        self.assertEqual(len(data['results']), len(self.actions))

    def test_GET_returns_all_things_with_include_invisible(self):
        #
        # View should 401 when not allowed to request private data (not authenticated)
        #
        request = self.factory.get(self.url + '?include_invisible')
        response = self.view(request, **self.kwargs)

        # Check that the request was restricted
        self.assertStatusCode(response, 401)

        # --------------------------------------------------

        #
        # View should 403 when not allowed to request private data (api key)
        #
        request = self.factory.get(self.url + '?include_invisible')
        request.META[KEY_HEADER] = self.apikey.key
        response = self.view(request, **self.kwargs)

        # Check that the request was restricted
        self.assertStatusCode(response, 403)

        # --------------------------------------------------

        #
        # View should 403 when not allowed to request private data (not owner)
        #
        request = self.factory.get(self.url + '?include_invisible')
        request.user = User.objects.create(username='new_user', password='password')
        response = self.view(request, **self.kwargs)

        # Check that the request was restricted
        self.assertStatusCode(response, 403)

        # --------------------------------------------------

        #
        # View should return private data when owner is logged in (Session Auth)
        #
        request = self.factory.get(self.url + '?include_invisible')
        request.user = self.owner
        response = self.view(request, **self.kwargs)

        # Check that the request was successful
        self.assertStatusCode(response, 200)

        # --------------------------------------------------

        #
        # View should return private data when owner is logged in (Basic Auth)
        #
        request = self.factory.get(self.url + '?include_invisible')
        credentials = ':'.join([self.owner.username, '123'])
        encoded_credentials = base64.b64encode(credentials.encode())
        request.META['HTTP_AUTHORIZATION'] = 'Basic ' + encoded_credentials.decode()
        response = self.view(request, **self.kwargs)

        # Check that the request was successful
        self.assertStatusCode(response, 200)

    def test_returns_from_cache_based_on_params(self):
        no_params = self.factory.get(self.url)
        vis_param = self.factory.get(self.url + '?include_invisible')

        no_params.user = self.owner
        vis_param.user = self.owner

        no_params.META['HTTP_ACCEPT'] = 'application/json'
        vis_param.META['HTTP_ACCEPT'] = 'application/json'

        self.view(no_params, **self.kwargs)
        self.view(vis_param, **self.kwargs)

        # Both requests should be made without hitting the database...
        with self.assertNumQueries(0):
            no_params_response = self.view(no_params, **self.kwargs)
            vis_param_response = self.view(vis_param, **self.kwargs)

        # But they should each correspond to different cached values.
        self.assertNotEqual(no_params_response.rendered_content,
                            vis_param_response.rendered_content)

    def test_returns_from_db_when_object_changes(self):
        request = self.factory.get(self.url + '?include_invisible')
        request.user = self.owner
        request.META['HTTP_ACCEPT'] = 'application/json'

        self.view(request, **self.kwargs)

        # Next requests should be made without hitting the database...
        with self.assertNumQueries(0):
            response1 = self.view(request, **self.kwargs)

        # But cache should be invalidated after changing a place.
        self.visible_place.geometry = geos.Point(1, 1)
        self.visible_place.save()
        cache_buffer.flush()

        response2 = self.view(request, **self.kwargs)

        self.assertNotEqual(response1.rendered_content, response2.rendered_content)
