from django.test import TestCase
from django.test.client import RequestFactory
from django.core.urlresolvers import reverse
from django.core.cache import cache as django_cache
from django.core.files import File
from django.contrib.gis import geos
import base64
import csv
import json
from StringIO import StringIO
from ..models import User, DataSet, Place, SubmissionSet, Submission, Attachment, Action
from ..cache import cache_buffer
from ..apikey.models import ApiKey
from ..apikey.auth import KEY_HEADER
from ..cors.models import Origin
from ..views import (PlaceInstanceView, PlaceListView, SubmissionInstanceView,
    SubmissionListView, DataSetSubmissionListView, DataSetInstanceView,
    DataSetListView, AttachmentListView, ActionListView)


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
        f = StringIO('This is test content in a "file"')
        f.name = 'myfile.txt'
        f.size = 20
        self.attachments = Attachment.objects.create(
            file=File(f, 'myfile.txt'), name='my_file_name', thing=self.place)
        self.comments = SubmissionSet.objects.create(place=self.place, name='comments')
        self.likes = SubmissionSet.objects.create(place=self.place, name='likes')
        self.applause = SubmissionSet.objects.create(place=self.place, name='applause')
        self.submissions = [
          Submission.objects.create(parent=self.comments, dataset=self.dataset, data='{"foo": 3}'),
          Submission.objects.create(parent=self.comments, dataset=self.dataset, data='{"foo": 3}'),
          Submission.objects.create(parent=self.comments, dataset=self.dataset, data='{"foo": 3}', visible=False),
          Submission.objects.create(parent=self.likes, dataset=self.dataset, data='{"bar": 3}'),
          Submission.objects.create(parent=self.likes, dataset=self.dataset, data='{"bar": 3}'),
          Submission.objects.create(parent=self.likes, dataset=self.dataset, data='{"bar": 3}'),
          Submission.objects.create(parent=self.likes, dataset=self.dataset, data='{"bar": 3}', visible=False),
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

        self.apikey = ApiKey.objects.create(key='abc')
        self.apikey.datasets.add(self.dataset)

        self.ds_origin = Origin.objects.create(pattern='openplans.github.com')
        self.ds_origin.datasets.add(self.dataset)

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
        SubmissionSet.objects.all().delete()
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
        self.assertIn('comments', data['properties']['submission_sets'].keys())
        self.assertIn('likes', data['properties']['submission_sets'].keys())
        self.assertNotIn('applause', data['properties']['submission_sets'].keys())

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
        self.assert_(all([comment['visible'] for comment in comments_set]))

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
        self.assert_(not all([comment['visible'] for comment in comments_set]))

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
        self.assertEqual(a.file.read(), 'This is test content in a "file"')

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
        request.META['HTTP_AUTHORIZATION'] = 'Basic ' + base64.b64encode(':'.join([self.owner.username, '123']))
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
        request.META['HTTP_AUTHORIZATION'] = 'Basic ' + base64.b64encode(':'.join([self.owner.username, '123']))
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
        # - SELECT * FROM sa_api_submissionset AS ss
        #    WHERE ss.place_id IN (<self.place.id>);
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
        # - SELECT * FROM sa_api_group as g
        #     JOIN sa_api_group_submitters as s ON (g.id = s.group_id)
        #    WHERE gs.user_id IN (<[each submitter id]>);
        #
        with self.assertNumQueries(11): # TODO: This should be 9, but might be 14 :(
            response = self.view(request, **self.request_kwargs)
            self.assertStatusCode(response, 200)

        path = reverse('place-detail', kwargs=self.request_kwargs)
        request = self.factory.get(path)

        # Check that this performs no more queries, since it's all cached
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

    def test_PUT_response_as_owner(self):
        place_data = json.dumps({
          'type': 'Feature',
          'properties': {
            'type': 'Park Bench',
            'private-secrets': 'The mayor loves this bench'
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

        # submitter is special, and so should be present and None
        self.assertIsNone(data['properties']['submitter'])

        # name is not special (lives in the data blob), so should just be unset
        self.assertNotIn('name', data['properties'])

        # private-secrets is not special, but is private, so should not come
        # back down
        self.assertNotIn('private-secrets', data['properties'])


    def test_PUT_response_as_submitter(self):
        pass
        ## TODO: Use the SubmittedThingSerializer to implement the following
        ##       permission structure.
        ##

        # place_data = json.dumps({
        #   'type': 'Feature',
        #   'properties': {
        #     'type': 'Park Bench',
        #     'private-secrets': 'The mayor loves this bench'
        #   },
        #   'geometry': {"type": "Point", "coordinates": [-73.99, 40.75]},
        #   'submitter': {'id': self.submitter.id}
        # })
        # other_user_place_data = json.dumps({
        #   'type': 'Feature',
        #   'properties': {
        #     'type': 'Park Bench',
        #     'private-secrets': 'The mayor loves this bench'
        #   },
        #   'geometry': {"type": "Point", "coordinates": [-73.99, 40.75]},
        #   'submitter': {'id': self.other_user.id}
        # })

        # #
        # # View should 403 when client not provided
        # #
        # request = self.factory.put(self.path, data=place_data, content_type='application/json')
        # request.user = self.submitter
        # response = self.view(request, **self.request_kwargs)
        # self.assertStatusCode(response, 403)

        # #
        # # View should 403 when authenticated as different user
        # #
        # request = self.factory.put(self.path, data=other_user_place_data, content_type='application/json')
        # request.META[KEY_HEADER] = self.apikey.key
        # request.user = self.other_user
        # response = self.view(request, **self.request_kwargs)
        # self.assertStatusCode(response, 403)

        # #
        # # View should 400 when setting a different submitter
        # #
        # request = self.factory.put(self.path, data=other_user_place_data, content_type='application/json')
        # request.META[KEY_HEADER] = self.apikey.key
        # request.user = self.submitter
        # response = self.view(request, **self.request_kwargs)
        # self.assertStatusCode(response, 400)

        # #
        # # View should update the place when submitter is authenticated and
        # # owner is authenticated through client
        # #
        # request = self.factory.put(self.path, data=place_data, content_type='application/json')
        # request.META[KEY_HEADER] = self.apikey.key
        # request.user = self.submitter

        # response = self.view(request, **self.request_kwargs)

        # data = json.loads(response.rendered_content)

        # # Check that the request was successful
        # self.assertStatusCode(response, 200)

        # # Check that the data attributes have been incorporated into the
        # # properties
        # self.assertEqual(data['properties'].get('type'), 'Park Bench')

        # # private-secrets is not special, but is private, so should not come
        # # back down
        # self.assertNotIn('private-secrets', data['properties'])

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
        request.META['HTTP_AUTHORIZATION'] = 'Basic ' + base64.b64encode(':'.join([self.owner.username, '123']))
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
        self.comments = SubmissionSet.objects.create(place=self.place, name='comments')
        self.likes = SubmissionSet.objects.create(place=self.place, name='likes')
        self.applause = SubmissionSet.objects.create(place=self.place, name='applause')
        self.submissions = [
          Submission.objects.create(parent=self.comments, dataset=self.dataset, data='{}'),
          Submission.objects.create(parent=self.comments, dataset=self.dataset, data='{}'),
          Submission.objects.create(parent=self.likes, dataset=self.dataset, data='{}'),
          Submission.objects.create(parent=self.likes, dataset=self.dataset, data='{}'),
          Submission.objects.create(parent=self.likes, dataset=self.dataset, data='{}'),
        ]

        dataset2 = DataSet.objects.create(slug='ds2', owner=self.owner)
        place2 = Place.objects.create(
          dataset=dataset2,
          geometry='POINT(3 4)',
        )

        self.apikey = ApiKey.objects.create(key='abc')
        self.apikey.datasets.add(self.dataset)

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
        SubmissionSet.objects.all().delete()
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

        rows = list(csv.reader(StringIO(response.rendered_content)))
        headers = rows[0]

        # Check that the request was successful
        self.assertStatusCode(response, 200)

        # Check that it's got good headers
        self.assertIn('dataset', headers)
        self.assertIn('geometry', headers)
        self.assertIn('name', headers)

        # Check that we have the right number of rows
        self.assertEqual(len(rows), 2)

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
        self.assert_(all([feature['properties'].get('foo') == 'bar' for feature in data['features']]))
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

    def test_GET_paginated_response(self):
        # Create a view with pagination configuration set, for consistency
        class OverridePlaceListView (PlaceListView):
            paginate_by = 50
            paginate_by_param = 'page_size'
        self.view = OverridePlaceListView.as_view()

        for _ in range(30):
            Place.objects.create(dataset=self.dataset, geometry='POINT(0 0)', data=json.dumps({'foo': 'bar', 'name': 1})),
            Place.objects.create(dataset=self.dataset, geometry='POINT(1 0)', data=json.dumps({'foo': 'bar', 'name': 2})),
            Place.objects.create(dataset=self.dataset, geometry='POINT(2 0)', data=json.dumps({'foo': 'baz', 'name': 3})),
            Place.objects.create(dataset=self.dataset, geometry='POINT(3 0)', data=json.dumps({'name': 4})),

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
        request.META['HTTP_AUTHORIZATION'] = 'Basic ' + base64.b64encode(':'.join([self.owner.username, '123']))
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
        self.assert_(data['properties'].get('visible'))

        # Check that geometry exists
        self.assertIn('geometry', data)

        # private-secrets is not special, but is private, so should not come
        # back down
        self.assertNotIn('private-secrets', data['properties'])

        # Check that we actually created a place
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
        self.assert_(data['properties'].get('visible'))

        # Check that geometry exists
        self.assertIn('geometry', data)

        # private-secrets is not special, but is private, so should not come
        # back down
        self.assertNotIn('private-secrets', data['properties'])

        # Check that we actually created a place
        final_num_places = Place.objects.all().count()
        self.assertEqual(final_num_places, start_num_places + 1)

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
        request.META['HTTP_AUTHORIZATION'] = 'Basic ' + base64.b64encode(':'.join([self.owner.username, '123']))
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
        self.comments = SubmissionSet.objects.create(place=self.place, name='comments')
        self.likes = SubmissionSet.objects.create(place=self.place, name='likes')
        self.applause = SubmissionSet.objects.create(place=self.place, name='applause')
        self.submissions = [
          Submission.objects.create(parent=self.comments, dataset=self.dataset, data='{"comment": "Wow!", "private-email": "abc@example.com", "foo": 3}'),
          Submission.objects.create(parent=self.comments, dataset=self.dataset, data='{"foo": 3}'),
          Submission.objects.create(parent=self.comments, dataset=self.dataset, data='{"foo": 3}', visible=False),
          Submission.objects.create(parent=self.likes, dataset=self.dataset, data='{"bar": 3}'),
          Submission.objects.create(parent=self.likes, dataset=self.dataset, data='{"bar": 3}'),
          Submission.objects.create(parent=self.likes, dataset=self.dataset, data='{"bar": 3}'),
          Submission.objects.create(parent=self.likes, dataset=self.dataset, data='{"bar": 3}', visible=False),
        ]

        f = StringIO('This is test content in a "file"')
        f.name = 'myfile.txt'
        f.size = 20
        self.attachments = Attachment.objects.create(
            file=File(f, 'myfile.txt'), name='my_file_name', thing=self.submissions[0])

        self.submission = self.submissions[0]

        self.apikey = ApiKey.objects.create(key='abc')
        self.apikey.datasets.add(self.dataset)

        self.request_kwargs = {
          'owner_username': self.owner.username,
          'dataset_slug': self.dataset.slug,
          'place_id': self.place.id,
          'submission_set_name': self.comments.name,
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
        SubmissionSet.objects.all().delete()
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
        self.assertEqual(a.file.read(), 'This is test content in a "file"')

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
        request.META['HTTP_AUTHORIZATION'] = 'Basic ' + base64.b64encode(':'.join([self.owner.username, '123']))
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
          'submission_set_name': self.comments.name,
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
        # - SELECT * FROM sa_api_datasetpermissions AS perm
        #    WHERE perm.dataset_id IN (<self.submission.dataset.id>);
        #
        with self.assertNumQueries(4):
            response = self.view(request, **self.request_kwargs)
            self.assertStatusCode(response, 200)

        path = reverse('submission-detail', kwargs=self.request_kwargs)
        request = self.factory.get(path)

        # Check that this performs no more queries, since it's all cached
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
        self.comments = SubmissionSet.objects.create(place=self.place, name='comments')
        self.likes = SubmissionSet.objects.create(place=self.place, name='likes')
        self.applause = SubmissionSet.objects.create(place=self.place, name='applause')
        self.submissions = [
          Submission.objects.create(parent=self.comments, dataset=self.dataset, data='{"comment": "Wow!", "private-email": "abc@example.com", "foo": 3}'),
          Submission.objects.create(parent=self.comments, dataset=self.dataset, data='{"foo": 3}'),
          Submission.objects.create(parent=self.comments, dataset=self.dataset, data='{"foo": 3}', visible=False),
          Submission.objects.create(parent=self.likes, dataset=self.dataset, data='{"bar": 3}'),
          Submission.objects.create(parent=self.likes, dataset=self.dataset, data='{"bar": 3}'),
          Submission.objects.create(parent=self.likes, dataset=self.dataset, data='{"bar": 3}'),
          Submission.objects.create(parent=self.likes, dataset=self.dataset, data='{"bar": 3}', visible=False),
        ]
        self.submission = self.submissions[0]

        # These are mainly around to ensure that we don't get spillover from
        # other datasets.
        dataset2 = DataSet.objects.create(slug='ds2', owner=self.owner)
        place2 = Place.objects.create(
          dataset=dataset2,
          geometry='POINT(3 4)',
        )
        comments2 = SubmissionSet.objects.create(place=place2, name='comments')
        submissions2 = [
          Submission.objects.create(parent=comments2, dataset=dataset2, data='{"comment": "Wow!", "private-email": "abc@example.com", "foo": 3}'),
          Submission.objects.create(parent=comments2, dataset=dataset2, data='{"foo": 3}'),
          Submission.objects.create(parent=comments2, dataset=dataset2, data='{"foo": 3}', visible=False),
        ]

        self.apikey = ApiKey.objects.create(key='abc')
        self.apikey.datasets.add(self.dataset)

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
        SubmissionSet.objects.all().delete()
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
        self.assertEqual(len(data['results']), 2)

        self.assertEqual(data['results'][-1]['url'],
            'http://testserver' + reverse('submission-detail', args=[
                self.owner.username, self.dataset.slug, self.place.id,
                self.submission.set_name, self.submission.id]))

    def test_GET_response_for_multiple_specific_objects(self):
        submissions = []
        for _ in range(10):
            submissions.append(Submission.objects.create(parent=self.comments, dataset=self.dataset, data='{"comment": "Wow!", "private-email": "abc@example.com", "foo": 3}'))

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

        rows = list(csv.reader(StringIO(response.rendered_content)))
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
        Submission.objects.create(dataset=self.dataset, parent=self.comments, data=json.dumps({'baz': 'bar', 'name': 1})),
        Submission.objects.create(dataset=self.dataset, parent=self.comments, data=json.dumps({'baz': 'bar', 'name': 2})),
        Submission.objects.create(dataset=self.dataset, parent=self.comments, data=json.dumps({'baz': 'bam', 'name': 3})),
        Submission.objects.create(dataset=self.dataset, parent=self.comments, data=json.dumps({'name': 4})),

        request = self.factory.get(self.path + '?baz=bar')
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that there are ATM features
        self.assertStatusCode(response, 200)
        self.assert_(all([result.get('baz') == 'bar' for result in data['results']]))
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
        self.assertIn('private-email', data['results'][-1])

        # --------------------------------------------------

        #
        # View should return private data when owner is logged in (Basic Auth)
        #
        request = self.factory.get(self.path + '?include_private')
        request.META['HTTP_AUTHORIZATION'] = 'Basic ' + base64.b64encode(':'.join([self.owner.username, '123']))
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
        self.assert_(data.get('visible'))

        # private-secrets is not special, but is private, so should not come
        # back down
        self.assertNotIn('private-email', data)

        # Check that we actually created a submission and set
        final_num_submissions = Submission.objects.all().count()
        self.assertEqual(final_num_submissions, start_num_submissions + 1)

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
        self.assert_(data.get('visible'))

        # private-secrets is not special, but is private, so should not come
        # back down
        self.assertNotIn('private-email', data)

        # Check that we actually created a submission and set
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
        request.META['HTTP_AUTHORIZATION'] = 'Basic ' + base64.b64encode(':'.join([self.owner.username, '123']))
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
        start_num_sets = SubmissionSet.objects.all().count()

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
        self.assert_(data.get('visible'))

        # private-secrets is not special, but is private, so should not come
        # back down
        self.assertNotIn('private-email', data)

        # Check that we actually created a submission and set
        final_num_submissions = Submission.objects.all().count()
        self.assertEqual(final_num_submissions, start_num_submissions + 1)
        final_num_sets = SubmissionSet.objects.all().count()
        self.assertEqual(final_num_sets, start_num_sets + 1)


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
        self.comments1 = SubmissionSet.objects.create(place=self.place1, name='comments')
        self.likes1 = SubmissionSet.objects.create(place=self.place1, name='likes')
        self.applause1 = SubmissionSet.objects.create(place=self.place1, name='applause')
        self.submissions1 = [
          Submission.objects.create(parent=self.comments1, dataset=self.dataset, data='{"comment": "Wow!", "private-email": "abc@example.com", "foo": 3}'),
          Submission.objects.create(parent=self.comments1, dataset=self.dataset, data='{"foo": 3}'),
          Submission.objects.create(parent=self.comments1, dataset=self.dataset, data='{"foo": 3}', visible=False),
          Submission.objects.create(parent=self.likes1, dataset=self.dataset, data='{"bar": 3}'),
          Submission.objects.create(parent=self.likes1, dataset=self.dataset, data='{"bar": 3}'),
          Submission.objects.create(parent=self.likes1, dataset=self.dataset, data='{"bar": 3}'),
          Submission.objects.create(parent=self.likes1, dataset=self.dataset, data='{"bar": 3}', visible=False),
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
        self.comments2 = SubmissionSet.objects.create(place=self.place2, name='comments')
        self.likes2 = SubmissionSet.objects.create(place=self.place2, name='likes')
        self.applause2 = SubmissionSet.objects.create(place=self.place2, name='applause')
        self.submissions2 = [
          Submission.objects.create(parent=self.comments2, dataset=self.dataset, data='{"comment": "Wow!", "private-email": "abc@example.com", "foo": 3}'),
          Submission.objects.create(parent=self.comments2, dataset=self.dataset, data='{"foo": 3}'),
          Submission.objects.create(parent=self.comments2, dataset=self.dataset, data='{"foo": 3}', visible=False),
          Submission.objects.create(parent=self.likes2, dataset=self.dataset, data='{"bar": 3}'),
          Submission.objects.create(parent=self.likes2, dataset=self.dataset, data='{"bar": 3}'),
          Submission.objects.create(parent=self.likes2, dataset=self.dataset, data='{"bar": 3}'),
          Submission.objects.create(parent=self.likes2, dataset=self.dataset, data='{"bar": 3}', visible=False),
        ]
        self.submission2 = self.submissions2[0]

        # These are mainly around to ensure that we don't get spillover from
        # other datasets.
        dataset2 = DataSet.objects.create(slug='ds2', owner=self.owner)
        place3 = Place.objects.create(
          dataset=dataset2,
          geometry='POINT(3 4)',
        )
        comments3 = SubmissionSet.objects.create(place=place3, name='comments')
        submissions3 = [
          Submission.objects.create(parent=comments3, dataset=dataset2, data='{"comment": "Wow!", "private-email": "abc@example.com", "foo": 3}'),
          Submission.objects.create(parent=comments3, dataset=dataset2, data='{"foo": 3}'),
          Submission.objects.create(parent=comments3, dataset=dataset2, data='{"foo": 3}', visible=False),
        ]

        self.apikey = ApiKey.objects.create(key='abc')
        self.apikey.datasets.add(self.dataset)

        self.request_kwargs = {
          'owner_username': self.owner.username,
          'dataset_slug': self.dataset.slug,
          'submission_set_name': self.comments1.name
        }

        self.factory = RequestFactory()
        self.path = reverse('dataset-submission-list', kwargs=self.request_kwargs)
        self.view = DataSetSubmissionListView.as_view()

    def tearDown(self):
        User.objects.all().delete()
        DataSet.objects.all().delete()
        Place.objects.all().delete()
        SubmissionSet.objects.all().delete()
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

        rows = list(csv.reader(StringIO(response.rendered_content)))
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
        Submission.objects.create(dataset=self.dataset, parent=self.comments1, data=json.dumps({'baz': 'bar', 'name': 1})),
        Submission.objects.create(dataset=self.dataset, parent=self.comments2, data=json.dumps({'baz': 'bar', 'name': 2})),
        Submission.objects.create(dataset=self.dataset, parent=self.comments1, data=json.dumps({'baz': 'bam', 'name': 3})),
        Submission.objects.create(dataset=self.dataset, parent=self.comments2, data=json.dumps({'name': 4})),

        request = self.factory.get(self.path + '?baz=bar')
        response = self.view(request, **self.request_kwargs)
        data = json.loads(response.rendered_content)

        # Check that there are ATM features
        self.assertStatusCode(response, 200)
        self.assert_(all([result.get('baz') == 'bar' for result in data['results']]))
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
        request.META['HTTP_AUTHORIZATION'] = 'Basic ' + base64.b64encode(':'.join([self.owner.username, '123']))
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
          'submission_set_name': self.comments1.name
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
        request.META['HTTP_AUTHORIZATION'] = 'Basic ' + base64.b64encode(':'.join([self.owner.username, '123']))
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
        self.comments = SubmissionSet.objects.create(place=self.place, name='comments')
        self.likes = SubmissionSet.objects.create(place=self.place, name='likes')
        self.applause = SubmissionSet.objects.create(place=self.place, name='applause')
        self.submissions = [
          Submission.objects.create(parent=self.comments, dataset=self.dataset, data='{"comment": "Wow!", "private-email": "abc@example.com", "foo": 3}'),
          Submission.objects.create(parent=self.comments, dataset=self.dataset, data='{"foo": 3}'),
          Submission.objects.create(parent=self.comments, dataset=self.dataset, data='{"foo": 3}', visible=False),
          Submission.objects.create(parent=self.likes, dataset=self.dataset, data='{"bar": 3}'),
          Submission.objects.create(parent=self.likes, dataset=self.dataset, data='{"bar": 3}'),
          Submission.objects.create(parent=self.likes, dataset=self.dataset, data='{"bar": 3}'),
          Submission.objects.create(parent=self.likes, dataset=self.dataset, data='{"bar": 3}', visible=False),
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

        self.apikey = ApiKey.objects.create(key='abc')
        self.apikey.datasets.add(self.dataset)

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
        SubmissionSet.objects.all().delete()
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

        # Check that the appropriate attributes are in the properties
        self.assertIn('url', data)
        self.assertIn('slug', data)
        self.assertIn('display_name', data)
        self.assertIn('keys', data)
        self.assertIn('owner', data)
        self.assertIn('places', data)
        self.assertIn('submission_sets', data)

        # Check that the URL is right
        self.assertEqual(data['url'],
            'http://testserver' + reverse('dataset-detail', args=[
                self.owner.username, self.dataset.slug]))

    def test_GET_from_cache(self):
        path = reverse('dataset-detail', kwargs=self.request_kwargs)
        request = self.factory.get(path)

        # Check that we make a finite number of queries
        # - SELECT * FROM sa_api_dataset
        #       INNER JOIN auth_user ON (owner_id = auth_user.id)
        #       WHERE (username = '<owner_username>'  AND slug = '<dataset_slug>' );
        #
        # - SELECT * FROM sa_api_datasetpermission
        #       INNER JOIN auth_user ON (owner_id = auth_user.id)
        #       WHERE (username = '<owner_username>'  AND slug = '<dataset_slug>' );
        #
        # - SELECT * FROM "auth_user"
        #       WHERE id = <owner_id>;
        #
        # - SELECT COUNT(*) FROM sa_api_place
        #       INNER JOIN sa_api_submittedthing ON (submittedthing_ptr_id = sa_api_submittedthing.id)
        #       WHERE dataset_id = <dataset_id>  AND visible = True;
        #
        # - SELECT sa_api_submittedthing.dataset_id, sa_api_submissionset.name, COUNT(*) AS "length" FROM sa_api_submission
        #       LEFT OUTER JOIN sa_api_submittedthing ON (submittedthing_ptr_id = sa_api_submittedthing.id)
        #       INNER JOIN sa_api_submissionset ON (parent_id = sa_api_submissionset.id)
        #       WHERE dataset_id = <dataset_id>
        #       GROUP BY dataset_id, sa_api_submissionset.name;
        with self.assertNumQueries(5):
            response = self.view(request, **self.request_kwargs)
            self.assertStatusCode(response, 200)

        path = reverse('dataset-detail', kwargs=self.request_kwargs)
        request = self.factory.get(path)

        # Check that this performs no more queries, since it's all cached
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
        request.META['HTTP_AUTHORIZATION'] = 'Basic ' + base64.b64encode(':'.join([self.owner.username, '123']))
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
        request.META['HTTP_AUTHORIZATION'] = 'Basic ' + base64.b64encode(':'.join([self.owner.username, '123']))
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
        request.META['HTTP_AUTHORIZATION'] = 'Basic ' + base64.b64encode(':'.join([self.owner.username, '123']))

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
        self.comments = SubmissionSet.objects.create(place=self.place, name='comments')
        self.likes = SubmissionSet.objects.create(place=self.place, name='likes')
        self.applause = SubmissionSet.objects.create(place=self.place, name='applause')
        self.submissions = [
          Submission.objects.create(parent=self.comments, dataset=self.dataset, data='{"comment": "Wow!", "private-email": "abc@example.com", "foo": 3}'),
          Submission.objects.create(parent=self.comments, dataset=self.dataset, data='{"foo": 3}'),
          Submission.objects.create(parent=self.comments, dataset=self.dataset, data='{"foo": 3}', visible=False),
          Submission.objects.create(parent=self.likes, dataset=self.dataset, data='{"bar": 3}'),
          Submission.objects.create(parent=self.likes, dataset=self.dataset, data='{"bar": 3}'),
          Submission.objects.create(parent=self.likes, dataset=self.dataset, data='{"bar": 3}'),
          Submission.objects.create(parent=self.likes, dataset=self.dataset, data='{"bar": 3}', visible=False),
        ]
        self.submission = self.submissions[0]

        # These are mainly around to ensure that we don't get spillover from
        # other datasets.
        dataset2 = DataSet.objects.create(slug='ds2', owner=self.owner)
        place2 = Place.objects.create(
          dataset=dataset2,
          geometry='POINT(3 4)',
        )
        comments2 = SubmissionSet.objects.create(place=place2, name='comments')
        submissions2 = [
          Submission.objects.create(parent=comments2, dataset=dataset2, data='{"comment": "Wow!", "private-email": "abc@example.com", "foo": 3}'),
          Submission.objects.create(parent=comments2, dataset=dataset2, data='{"foo": 3}'),
          Submission.objects.create(parent=comments2, dataset=dataset2, data='{"foo": 3}', visible=False),
        ]

        other_owner = User.objects.create_user(
            username='frank',
            password='789',
            email='def@example.com')
        dataset3 = DataSet.objects.create(owner=other_owner, slug='slug', display_name="Display Name")

        self.apikey = ApiKey.objects.create(key='abc')
        self.apikey.datasets.add(self.dataset)

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
        SubmissionSet.objects.all().delete()
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
        request.META['HTTP_AUTHORIZATION'] = 'Basic ' + base64.b64encode(':'.join([self.owner.username, '123']))

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

    def test_get_all_submission_sets(self):
        request = self.factory.get(self.path)
        view = DataSetListView()
        view.request = request
        view.kwargs = self.request_kwargs

        sets = view.get_all_submission_sets()
        self.assertIn('likes', [s['parent__name'] for s in sets[self.dataset.pk]])

    def test_GET_response_with_invisible_data(self):
        #
        # View should not return invisible data normally
        #
        request = self.factory.get(self.path)
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
        request.META['HTTP_AUTHORIZATION'] = 'Basic ' + base64.b64encode(':'.join([self.owner.username, '123']))
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

        self.file = StringIO('This is test content in a "file"')
        self.file.name = 'myfile.txt'
        self.file.size = 20
        # self.attachments = Attachment.objects.create(
        #     file=File(f, 'myfile.txt'), name='my_file_name', thing=self.place)

        self.apikey = ApiKey.objects.create(key='abc')
        self.apikey.datasets.add(self.dataset)

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
        SubmissionSet.objects.all().delete()
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
        f = StringIO('This is test content in a "file"')
        f.name = 'myfile.txt'
        request = self.factory.post(self.path, data={'file': f, 'name': 'my-file'})
        response = self.view(request, **self.request_kwargs)
        self.assertStatusCode(response, 401, response.render())

        # --------------------------------------------------

        #
        # Can write with the API key.
        #
        f = StringIO('This is test content in a "file"')
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
        self.assertEqual(a.file.read(), 'This is test content in a "file"')

        # --------------------------------------------------

        #
        # Can not write when logged in as not owner.
        #
        f = StringIO('This is test content in a "file"')
        f.name = 'myfile.txt'
        request = self.factory.post(self.path, data={'file': f, 'name': 'my-file'})
        User.objects.create_user(username='new_user', password='password')
        request.META['HTTP_AUTHORIZATION'] = 'Basic ' + base64.b64encode(':'.join(['new_user', 'password']))
        response = self.view(request, **self.request_kwargs)

        # Check that the request was successful
        self.assertStatusCode(response, 403, response.render())

        # --------------------------------------------------

        #
        # Can write when logged in as owner.
        #
        f = StringIO('This is test content in a "file"')
        f.name = 'myfile.txt'
        request = self.factory.post(self.path, data={'file': f, 'name': 'my-file'})
        request.META['HTTP_AUTHORIZATION'] = 'Basic ' + base64.b64encode(':'.join([self.owner.username, '123']))
        response = self.view(request, **self.request_kwargs)

        # Check that the request was successful
        self.assertStatusCode(response, 201, response.render())

    def test_POST_attachment_to_invisible_place(self):
        #
        # Can't write if not authenticated
        #
        f = StringIO('This is test content in a "file"')
        f.name = 'myfile.txt'
        request = self.factory.post(self.invisible_path + '?include_invisible', data={'file': f, 'name': 'my-file'})
        response = self.view(request, **self.invisible_request_kwargs)
        self.assertStatusCode(response, 401, response.render())

        # --------------------------------------------------

        #
        # Can't write with the API key/include_invisible. (400)
        #
        f = StringIO('This is test content in a "file"')
        f.name = 'myfile.txt'
        request = self.factory.post(self.invisible_path, data={'file': f, 'name': 'my-file'})
        request.META[KEY_HEADER] = self.apikey.key
        response = self.view(request, **self.invisible_request_kwargs)
        self.assertStatusCode(response, 400, response.render())


        # --------------------------------------------------

        #
        # Can't write with the API key (403).
        #
        f = StringIO('This is test content in a "file"')
        f.name = 'myfile.txt'
        request = self.factory.post(self.invisible_path + '?include_invisible', data={'file': f, 'name': 'my-file'})
        request.META[KEY_HEADER] = self.apikey.key
        response = self.view(request, **self.invisible_request_kwargs)
        self.assertStatusCode(response, 403, response.render())

        # --------------------------------------------------

        #
        # Can not write when logged in as not owner.
        #
        f = StringIO('This is test content in a "file"')
        f.name = 'myfile.txt'
        request = self.factory.post(self.invisible_path + '?include_invisible', data={'file': f, 'name': 'my-file'})
        User.objects.create_user(username='new_user', password='password')
        request.META['HTTP_AUTHORIZATION'] = 'Basic ' + base64.b64encode(':'.join(['new_user', 'password']))
        response = self.view(request, **self.invisible_request_kwargs)

        # Check that the request was successful
        self.assertStatusCode(response, 403, response.render())

        # --------------------------------------------------

        #
        # Can't write when logged in as owner without include_invisible (400).
        #
        f = StringIO('This is test content in a "file"')
        f.name = 'myfile.txt'
        request = self.factory.post(self.invisible_path, data={'file': f, 'name': 'my-file'})
        request.META['HTTP_AUTHORIZATION'] = 'Basic ' + base64.b64encode(':'.join([self.owner.username, '123']))
        response = self.view(request, **self.invisible_request_kwargs)
        self.assertStatusCode(response, 400, response.render())

        # --------------------------------------------------

        #
        # Can write when logged in as owner.
        #
        f = StringIO('This is test content in a "file"')
        f.name = 'myfile.txt'
        request = self.factory.post(self.invisible_path + '?include_invisible', data={'file': f, 'name': 'my-file'})
        request.META['HTTP_AUTHORIZATION'] = 'Basic ' + base64.b64encode(':'.join([self.owner.username, '123']))
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
        request.META['HTTP_AUTHORIZATION'] = 'Basic ' + base64.b64encode(':'.join([self.owner.username, '123']))
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

        self.comments = SubmissionSet.objects.create(place=self.place, name='comments')
        self.submissions = [
          Submission.objects.create(parent=self.comments, dataset=self.dataset, data='{"foo": 3}'),
          Submission.objects.create(parent=self.comments, dataset=self.dataset, data='{"foo": 3}', visible=False),
        ]

        self.file = StringIO('This is test content in a "file"')
        self.file.name = 'myfile.txt'
        self.file.size = 20

        self.apikey = ApiKey.objects.create(key='abc')
        self.apikey.datasets.add(self.dataset)

        self.request_kwargs = {
          'owner_username': self.owner.username,
          'dataset_slug': self.dataset.slug,
          'place_id': self.place.id,
          'submission_set_name': self.comments.name,
          'thing_id': str(self.submissions[0].id)
        }

        self.invisible_request_kwargs = {
          'owner_username': self.owner.username,
          'dataset_slug': self.dataset.slug,
          'place_id': self.place.id,
          'submission_set_name': self.comments.name,
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
        SubmissionSet.objects.all().delete()
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
        request.META['HTTP_AUTHORIZATION'] = 'Basic ' + base64.b64encode(':'.join([self.owner.username, '123']))
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
        f = StringIO('This is test content in a "file"')
        f.name = 'myfile.txt'
        request = self.factory.post(self.path, data={'file': f, 'name': 'my-file'})
        response = self.view(request, **self.request_kwargs)
        self.assertStatusCode(response, 401, response.render())

        # --------------------------------------------------

        #
        # Can write with the API key.
        #
        f = StringIO('This is test content in a "file"')
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
        self.assertEqual(a.file.read(), 'This is test content in a "file"')

        # --------------------------------------------------

        #
        # Can not write when logged in as not owner.
        #
        f = StringIO('This is test content in a "file"')
        f.name = 'myfile.txt'
        request = self.factory.post(self.path, data={'file': f, 'name': 'my-file'})
        User.objects.create_user(username='new_user', password='password')
        request.META['HTTP_AUTHORIZATION'] = 'Basic ' + base64.b64encode(':'.join(['new_user', 'password']))
        response = self.view(request, **self.request_kwargs)

        # Check that the request was successful
        self.assertStatusCode(response, 403, response.render())

        # --------------------------------------------------

        #
        # Can write when logged in as owner.
        #
        f = StringIO('This is test content in a "file"')
        f.name = 'myfile.txt'
        request = self.factory.post(self.path, data={'file': f, 'name': 'my-file'})
        request.META['HTTP_AUTHORIZATION'] = 'Basic ' + base64.b64encode(':'.join([self.owner.username, '123']))
        response = self.view(request, **self.request_kwargs)

        # Check that the request was successful
        self.assertStatusCode(response, 201, response.render())

    def test_POST_attachment_to_invisible_submission(self):
        #
        # Can't write if not authenticated
        #
        f = StringIO('This is test content in a "file"')
        f.name = 'myfile.txt'
        request = self.factory.post(self.invisible_path + '?include_invisible', data={'file': f, 'name': 'my-file'})
        response = self.view(request, **self.invisible_request_kwargs)
        self.assertStatusCode(response, 401, response.render())

        # --------------------------------------------------

        #
        # Can't write with the API key/include_invisible. (400)
        #
        f = StringIO('This is test content in a "file"')
        f.name = 'myfile.txt'
        request = self.factory.post(self.invisible_path, data={'file': f, 'name': 'my-file'})
        request.META[KEY_HEADER] = self.apikey.key
        response = self.view(request, **self.invisible_request_kwargs)
        self.assertStatusCode(response, 400, response.render())


        # --------------------------------------------------

        #
        # Can't write with the API key (403).
        #
        f = StringIO('This is test content in a "file"')
        f.name = 'myfile.txt'
        request = self.factory.post(self.invisible_path + '?include_invisible', data={'file': f, 'name': 'my-file'})
        request.META[KEY_HEADER] = self.apikey.key
        response = self.view(request, **self.invisible_request_kwargs)
        self.assertStatusCode(response, 403, response.render())

        # --------------------------------------------------

        #
        # Can not write when logged in as not owner.
        #
        f = StringIO('This is test content in a "file"')
        f.name = 'myfile.txt'
        request = self.factory.post(self.invisible_path + '?include_invisible', data={'file': f, 'name': 'my-file'})
        User.objects.create_user(username='new_user', password='password')
        request.META['HTTP_AUTHORIZATION'] = 'Basic ' + base64.b64encode(':'.join(['new_user', 'password']))
        response = self.view(request, **self.invisible_request_kwargs)

        # Check that the request was successful
        self.assertStatusCode(response, 403, response.render())

        # --------------------------------------------------

        #
        # Can't write when logged in as owner without include_invisible (400).
        #
        f = StringIO('This is test content in a "file"')
        f.name = 'myfile.txt'
        request = self.factory.post(self.invisible_path, data={'file': f, 'name': 'my-file'})
        request.META['HTTP_AUTHORIZATION'] = 'Basic ' + base64.b64encode(':'.join([self.owner.username, '123']))
        response = self.view(request, **self.invisible_request_kwargs)
        self.assertStatusCode(response, 400, response.render())

        # --------------------------------------------------

        #
        # Can write when logged in as owner.
        #
        f = StringIO('This is test content in a "file"')
        f.name = 'myfile.txt'
        request = self.factory.post(self.invisible_path + '?include_invisible', data={'file': f, 'name': 'my-file'})
        request.META['HTTP_AUTHORIZATION'] = 'Basic ' + base64.b64encode(':'.join([self.owner.username, '123']))
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

        self.visible_set = SubmissionSet.objects.create(place=self.visible_place, name='vis')
        self.invisible_set = SubmissionSet.objects.create(place=self.invisible_place, name='invis')

        self.visible_submission = Submission.objects.create(dataset=self.dataset, parent=self.visible_set)
        self.invisible_submission = Submission.objects.create(dataset=self.dataset, parent=self.invisible_set)
        self.invisible_submission2 = Submission.objects.create(dataset=self.dataset, parent=self.visible_set, visible=False)

        self.actions = [
            # Get existing activity for visible things that have been created
            Action.objects.get(thing=self.visible_place),
            Action.objects.get(thing=self.visible_submission),

            # Create some more activities for visible things
            Action.objects.create(thing=self.visible_place.submittedthing_ptr, action='update'),
            Action.objects.create(thing=self.visible_place.submittedthing_ptr, action='delete'),
        ]

        self.apikey = ApiKey.objects.create(key='abc')
        self.apikey.datasets.add(self.dataset)

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
        request.META['HTTP_AUTHORIZATION'] = 'Basic ' + base64.b64encode(':'.join([self.owner.username, '123']))
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


# ----------------------------------------------------------------------


# from django.test import TestCase
# from django.test.client import Client
# from django.test.client import RequestFactory
# from django.contrib.auth.models import User
# from django.core.urlresolvers import reverse
# from django.core.cache import cache
# from djangorestframework.response import ErrorResponse
# from mock import patch
# from nose.tools import (istest, assert_equal, assert_not_equal, assert_in,
#                         assert_raises, assert_is_not_none, assert_not_in, ok_)
# from ..models import DataSet, Place, Submission, SubmissionSet, Attachment
# from ..models import SubmittedThing, Activity
# from ..views import SubmissionCollectionView
# from ..views import raise_error_if_not_authenticated
# from ..views import ApiKeyCollectionView
# from ..views import OwnerPasswordView
# import json
# import mock


# class TestAuthFunctions(object):

#     class DummyView(object):

#         def post(self, request):
#             raise_error_if_not_authenticated(self, request)
#             return 'ok'

#     @istest
#     def test_auth_required_without_a_user(self):
#         request = RequestFactory().post('/foo')
#         assert_raises(ErrorResponse, self.DummyView().post, request)

#     @istest
#     def test_auth_required_with_logged_out_user(self):
#         request = RequestFactory().post('/foo')
#         request.user = mock.Mock(**{'is_authenticated.return_value': False})
#         assert_raises(ErrorResponse, self.DummyView().post, request)

#     @istest
#     def test_auth_required_with_logged_in_user(self):
#         request = RequestFactory().post('/foo')
#         request.user = mock.Mock(**{'is_authenticated.return_value': True,
#                                     'username': 'bob'})
#         # No exceptions, don't care about return value.
#         self.DummyView().post(request)

#     @istest
#     def test_isownerorsuperuser__anonymous_not_allowed(self):
#         user = mock.Mock(**{'is_authenticated.return_value': False,
#                             'is_superuser': False})
#         view = mock.Mock(request=RequestFactory().get(''))
#         from ..views import IsOwnerOrSuperuser
#         assert_raises(ErrorResponse,
#                       IsOwnerOrSuperuser(view).check_permission, user)

#     @istest
#     def test_isownerorsuperuser__wrong_user_not_allowed(self):
#         view = mock.Mock(username='bob',
#                          request=RequestFactory().get(''))
#         user = mock.Mock(is_superuser=False, username='not bob')
#         from ..views import IsOwnerOrSuperuser
#         assert_raises(ErrorResponse,
#                       IsOwnerOrSuperuser(view).check_permission, user)

#     @istest
#     def test_isownerorsuperuser__superuser_is_allowed(self):
#         user = mock.Mock(is_superuser=True)
#         view = mock.Mock(request=RequestFactory().get(''))

#         from ..views import IsOwnerOrSuperuser
#         # No exceptions == good.
#         IsOwnerOrSuperuser(view).check_permission(user)

#     @istest
#     def test_isownerorsuperuser__owner_is_allowed(self):
#         view = mock.Mock(allowed_username='bob',
#                          request=RequestFactory().get(''))
#         user = mock.Mock(is_superuser=False, username='bob')
#         from ..views import IsOwnerOrSuperuser
#         # If not exceptions, we're OK.
#         IsOwnerOrSuperuser(view).check_permission(user)

#     @istest
#     def test_isownerorsuperuser__no_api_key(self):
#         view = mock.Mock(allowed_username='bob',
#                          request=RequestFactory().get(''))
#         user = mock.Mock(is_superuser=False, username='bob')
#         from ..views import IsOwnerOrSuperuserWithoutApiKey
#         # If not exceptions, we're OK.
#         IsOwnerOrSuperuserWithoutApiKey(view).check_permission(user)
#         # If API key, not allowed.
#         from ..apikey.auth import KEY_HEADER
#         view.request = RequestFactory().get('', **{KEY_HEADER: 'oh no'})
#         assert_raises(ErrorResponse,
#                       IsOwnerOrSuperuserWithoutApiKey(view).check_permission,
#                       user)


# class TestDataSetCollectionView(TestCase):
#     def setUp(self):
#         from ..apikey.models import ApiKey
#         DataSet.objects.all().delete()
#         ApiKey.objects.all().delete()
#         User.objects.all().delete()

#         cache_buffer.reset()
#         django_cache.clear()

#     @istest
#     def post_without_permission_does_not_invalidate_cache(self):
#         from ..views import DataSetCollectionView

#         user = User.objects.create(username='bob')
#         factory = RequestFactory()
#         view = DataSetCollectionView.as_view()

#         kwargs = {'owner__username': user.username}
#         url = reverse('dataset_collection_by_user', kwargs=kwargs)

#         get_request = factory.get(url, content_type='application/json',  headers={'Accept': 'application/json'})
#         get_request.user = user
#         get_request.META['HTTP_ACCEPT'] = 'application/json'

#         with self.assertNumQueries(1):
#             response1 = view(get_request, **kwargs)
#         with self.assertNumQueries(0):
#             response2 = view(get_request, **kwargs)
#         self.assertEqual(response1.content, response2.content)

#         data = {
#             'display_name': 'Test DataSet',
#             'slug': 'test-dataset',
#         }

#         post_request = factory.post(url, data=json.dumps(data), content_type='application/json', headers={'Accept': 'application/json'})
#         post_request.META['HTTP_ACCEPT'] = 'application/json'
#         view(post_request, **kwargs)

#         with self.assertNumQueries(0):
#             response3 = view(get_request, **kwargs)
#         self.assertEqual(response1.content, response3.content)


#     @istest
#     def post_with_permission_invalidates_cache(self):
#         from ..views import DataSetCollectionView

#         user = User.objects.create(username='bob')
#         factory = RequestFactory()
#         view = DataSetCollectionView.as_view()

#         kwargs = {'owner__username': user.username}
#         url = reverse('dataset_collection_by_user', kwargs=kwargs)

#         get_request = factory.get(url, content_type='application/json')
#         get_request.user = user
#         get_request.META['HTTP_ACCEPT'] = 'application/json'

#         with self.assertNumQueries(1):
#             response1 = view(get_request, **kwargs)
#         with self.assertNumQueries(0):
#             response2 = view(get_request, **kwargs)
#         self.assertEqual(response1.content, response2.content)

#         data = {
#             'display_name': 'Test DataSet',
#             'slug': 'test-dataset',
#         }

#         post_request = factory.post(url, data=json.dumps(data), content_type='application/json')
#         post_request.user = user
#         post_request.META['HTTP_ACCEPT'] = 'application/json'
#         view(post_request, **kwargs)

#         # We make more queries here because the dataset collection is non-empty
#         # and we have to join with places and such.
#         with self.assertNumQueries(3):
#             response3 = view(get_request, **kwargs)
#         self.assertNotEqual(response1.content, response3.content)


#     @istest
#     def post_creates_an_api_key(self):
#         user = User.objects.create(username='bob')

#         kwargs = {'owner__username': user.username}
#         url = reverse('dataset_collection_by_user', kwargs=kwargs)
#         data = {
#             'display_name': 'Test DataSet',
#             'slug': 'test-dataset',
#         }

#         from ..views import DataSetCollectionView

#         request = RequestFactory().post(url, data=json.dumps(data),
#                                         content_type='application/json')
#         request.user = user
#         view = DataSetCollectionView().as_view()
#         # Have to pass kwargs explicitly if not using
#         # urlresolvers.resolve() etc.
#         response = view(request, **kwargs)

#         assert_equal(response.status_code, 201)
#         assert_in(url + 'test-dataset', response.get('Location'))

#         response_data = json.loads(response.content)
#         assert_equal(response_data['display_name'], 'Test DataSet')
#         assert_equal(response_data['slug'], 'test-dataset')


# class TestDataSetInstanceView(TestCase):

#     def setUp(self):
#         DataSet.objects.all().delete()
#         User.objects.all().delete()
#         user = User.objects.create(username='bob')
#         self.dataset = DataSet.objects.create(slug='dataset',
#                                               display_name='dataset',
#                                               owner=user)

#     @istest
#     def put_with_slug_gives_a_new_location(self):
#         kwargs = dict(owner__username='bob', slug='dataset')
#         url = reverse('dataset_instance_by_user', kwargs=kwargs)
#         data = {'slug': 'new-name', 'display_name': 'dataset'}
#         request = RequestFactory().put(url, data=json.dumps(data),
#                                        content_type='application/json'
#                                        )
#         request.user = mock.Mock(**{'is_authenticated.return_value': True})
#         from ..views import DataSetInstanceView
#         view = DataSetInstanceView().as_view()
#         response = view(request, **kwargs)
#         assert_equal(response.status_code, 303)
#         assert_in('/new-name', response['Location'])

#     @istest
#     def put_with_wrong_user_is_not_allowed(self):
#         # Regression test for https://www.pivotaltracker.com/story/show/34080763
#         kwargs = dict(owner__username='bob', slug='dataset')
#         url = reverse('dataset_instance_by_user', kwargs=kwargs)
#         data = {'slug': 'dataset', 'display_name': 'New Title'}
#         request = RequestFactory().put(url, data=json.dumps(data),
#                                        content_type='application/json'
#                                        )
#         request.user = mock.Mock(**{'is_authenticated.return_value': True,
#                                     'is_superuser': False,
#                                     'username': 'NOT BOB!'})
#         from ..views import DataSetInstanceView
#         view = DataSetInstanceView().as_view()
#         response = view(request, **kwargs)
#         assert_equal(response.status_code, 403)


# class TestMakingAGetRequestToASubmissionTypeCollectionUrl (TestCase):

#     @istest
#     def should_call_view_with_place_id_and_submission_type_name(self):
#         client = Client()

#         with patch('sa_api_v2.views.SubmissionCollectionView.get') as getter:
#             client.get('/api/v1/datasets/somebody/something/places/1/comments/',
#                        HTTP_ACCEPT='application/json')
#             args, kwargs = getter.call_args
#             assert_equal(
#                 kwargs,
#                 {'place_id': u'1',
#                  'submission_type': u'comments',
#                  'dataset__owner__username': 'somebody',
#                  'dataset__slug': 'something',
#                  }
#             )

#     @istest
#     def should_return_a_list_of_submissions_of_the_type_for_the_place(self):
#         User.objects.all().delete()
#         DataSet.objects.all().delete()
#         Place.objects.all().delete()
#         Submission.objects.all().delete()
#         SubmissionSet.objects.all().delete()

#         owner = User.objects.create(username='user')
#         dataset = DataSet.objects.create(slug='data', owner_id=owner.id)
#         place = Place.objects.create(location='POINT(0 0)', dataset_id=dataset.id)
#         comments = SubmissionSet.objects.create(place_id=place.id, submission_type='comments')
#         Submission.objects.create(parent_id=comments.id, dataset_id=dataset.id)
#         Submission.objects.create(parent_id=comments.id, dataset_id=dataset.id)

#         request = RequestFactory().get('/places/%d/comments/' % place.id)
#         request.user = mock.Mock(**{'is_authenticated.return_value': False,
#                                     'is_superuser': False})
#         request.META['HTTP_ACCEPT'] = 'application/json'
#         view = SubmissionCollectionView.as_view()

#         response = view(request, place_id=place.id,
#                         submission_type='comments',
#                         dataset__owner__username=owner.username,
#                         dataset__slug=dataset.slug,
#                         )
#         data = json.loads(response.content)
#         assert_equal(len(data), 2)

#     @istest
#     def should_return_an_empty_list_if_the_place_has_no_submissions_of_the_type(self):
#         User.objects.all().delete()
#         DataSet.objects.all().delete()
#         Place.objects.all().delete()
#         Submission.objects.all().delete()

#         owner = User.objects.create(username='user')
#         dataset = DataSet.objects.create(slug='data', owner_id=owner.id)
#         place = Place.objects.create(location='POINT(0 0)', dataset_id=dataset.id)
#         comments = SubmissionSet.objects.create(place_id=place.id, submission_type='comments')
#         Submission.objects.create(parent_id=comments.id, dataset_id=dataset.id)
#         Submission.objects.create(parent_id=comments.id, dataset_id=dataset.id)

#         request = RequestFactory().get('/places/%d/votes/' % place.id)
#         request.user = mock.Mock(**{'is_authenticated.return_value': False,
#                                     'is_superuser': False})
#         request.META['HTTP_ACCEPT'] = 'application/json'
#         view = SubmissionCollectionView.as_view()

#         response = view(request, place_id=place.id,
#                         submission_type='votes',
#                         dataset__owner__username=owner.username,
#                         )
#         data = json.loads(response.content)
#         assert_equal(len(data), 0)


# class TestMakingAPostRequestToASubmissionTypeCollectionUrl (TestCase):

#     @istest
#     def should_create_a_new_submission_of_the_given_type_on_the_place(self):
#         User.objects.all().delete()
#         DataSet.objects.all().delete()
#         Place.objects.all().delete()
#         Submission.objects.all().delete()
#         SubmissionSet.objects.all().delete()

#         owner = User.objects.create(username='user')
#         dataset = DataSet.objects.create(slug='data',
#                                               owner_id=owner.id)
#         place = Place.objects.create(location='POINT(0 0)',
#                                      dataset_id=dataset.id)
#         comments = SubmissionSet.objects.create(place_id=place.id, submission_type='comments')

#         data = {
#             'submitter_name': 'Mjumbe Poe',
#             'age': 12,
#             'comment': 'This is rad!',
#         }
#         request = RequestFactory().post('/places/%d/comments/' % place.id,
#                                         data=json.dumps(data), content_type='application/json')
#         request.user = mock.Mock(**{'is_authenticated.return_value': True})
#         view = SubmissionCollectionView.as_view()

#         response = view(request, place_id=place.id,
#                         submission_type='comments',
#                         dataset__owner__username=owner.username,
#                         )
#         data = json.loads(response.content)
#         #print response
#         assert_equal(response.status_code, 201)
#         assert_in('age', data)


# class TestSubmissionInstanceAPI (TestCase):

#     def setUp(self):
#         from sa_api_v2.apikey.models import ApiKey

#         User.objects.all().delete()
#         DataSet.objects.all().delete()
#         Place.objects.all().delete()
#         Submission.objects.all().delete()
#         SubmissionSet.objects.all().delete()
#         ApiKey.objects.all().delete()

#         cache_buffer.reset()
#         django_cache.clear()

#         self.owner = User.objects.create(username='user')
#         self.apikey = ApiKey.objects.create(user_id=self.owner.id, key='abcd1234')
#         self.dataset = DataSet.objects.create(slug='data',
#                                               owner_id=self.owner.id)
#         self.place = Place.objects.create(location='POINT(0 0)',
#                                           dataset_id=self.dataset.id)
#         self.comments = SubmissionSet.objects.create(place_id=self.place.id,
#                                                      submission_type='comments')
#         self.submission = Submission.objects.create(parent_id=self.comments.id,
#                                                     dataset_id=self.dataset.id)
#         self.url = reverse('submission_instance_by_dataset',
#                            kwargs=dict(place_id=self.place.id,
#                                        pk=self.submission.id,
#                                        submission_type='comments',
#                                        dataset__owner__username=self.owner.username,
#                                        dataset__slug=self.dataset.slug,
#                                        ))
#         self.place_url = reverse('place_instance_by_dataset',
#                                  kwargs=dict(pk=self.place.id,
#                                              dataset__owner__username=self.owner.username,
#                                              dataset__slug=self.dataset.slug,
#                                              ))
#         from ..views import SubmissionInstanceView, PlaceInstanceView
#         self.view = SubmissionInstanceView.as_view()
#         self.place_view = PlaceInstanceView.as_view()

#     @istest
#     def put_request_should_modify_instance(self):
#         data = {
#             'submitter_name': 'Paul Winkler',
#             'age': 99,
#             'comment': 'Get off my lawn!',
#         }

#         request = RequestFactory().put(self.url, data=json.dumps(data),
#                                        content_type='application/json')
#         request.user = self.owner
#         response = self.view(request, place_id=self.place.id,
#                              pk=self.submission.id,
#                              submission_type='comments',
#                              dataset__owner__username=self.owner.username,
#                              dataset__slug=self.dataset.slug,
#                              )

#         response_data = json.loads(response.content)
#         assert_equal(response.status_code, 200)
#         self.assertDictContainsSubset(data, response_data)

#     @istest
#     def put_request_should_invalidate_cache(self):
#         get_request = RequestFactory().get(self.url, content_type='application/json')
#         get_request.user = self.owner
#         get_request.META['HTTP_ACCEPT'] = 'application/json'
#         kwargs = dict(place_id=self.place.id,
#                        pk=self.submission.id,
#                        submission_type='comments',
#                        dataset__owner__username=self.owner.username,
#                        dataset__slug=self.dataset.slug,
#                       )

#         with self.assertNumQueries(2):
#             response1 = self.view(get_request, **kwargs)
#         with self.assertNumQueries(0):
#             response2 = self.view(get_request, **kwargs)
#         self.assertEqual(response1.content, response2.content)

#         data = {
#             'submitter_name': 'Paul Winkler',
#             'age': 99,
#             'comment': 'Get off my lawn!',
#         }

#         put_request = RequestFactory().put(self.url, data=json.dumps(data),
#                                            content_type='application/json')
#         put_request.user = self.owner
#         self.view(put_request, **kwargs)

#         with self.assertNumQueries(1):
#             response3 = self.view(get_request, **kwargs)
#         self.assertNotEqual(response1.content, response3.content)

#     @istest
#     def put_request_should_invalidate_place_cache(self):
#         get_request = RequestFactory().get(self.place_url + '?include_submissions=true', content_type='application/json')
#         get_request.user = self.owner
#         get_request.META['HTTP_ACCEPT'] = 'application/json'
#         place_kwargs = dict(pk=self.place.id,
#                        dataset__owner__username=self.owner.username,
#                        dataset__slug=self.dataset.slug,
#                       )
#         submission_kwargs = dict(place_id=self.place.id,
#                        pk=self.submission.id,
#                        submission_type='comments',
#                        dataset__owner__username=self.owner.username,
#                        dataset__slug=self.dataset.slug,
#                       )

#         with self.assertNumQueries(3):
#             response1 = self.place_view(get_request, **place_kwargs)
#         with self.assertNumQueries(0):
#             response2 = self.place_view(get_request, **place_kwargs)
#         self.assertEqual(response1.content, response2.content)
#         self.assertEqual(response1.status_code, 200)

#         data = {
#             'submitter_name': 'Paul Winkler',
#             'age': 99,
#             'comment': 'Get off my lawn!',
#         }

#         put_request = RequestFactory().put(self.url, data=json.dumps(data),
#                                            content_type='application/json')
#         put_request.user = self.owner
#         self.view(put_request, **submission_kwargs)

#         with self.assertNumQueries(2):
#             response3 = self.place_view(get_request, **place_kwargs)
#         self.assertNotEqual(response1.content, response3.content)

#     @istest
#     def delete_request_should_delete_submission(self):
#         request = RequestFactory().delete(self.url)
#         request.user = self.owner
#         response = self.view(request, place_id=self.place.id,
#                              pk=self.submission.id,
#                              submission_type='comments',
#                              dataset__owner__username=self.owner.username,
#                              dataset__slug=self.dataset.slug,
#                              )

#         assert_equal(response.status_code, 204)
#         assert_equal(Submission.objects.all().count(), 0)

#     @istest
#     def submission_get_request_retrieves_data(self):
#         self.submission.data = json.dumps({'animal': 'tree frog', 'private-email': 'admin@example.com'})
#         self.submission.save()
#         request = RequestFactory().get(self.url)
#         # Anonymous is OK.
#         request.user = mock.Mock(**{'is_authenticated.return_value': False,
#                                     'is_superuser': False,
#                                     })
#         request.META['HTTP_ACCEPT'] = 'application/json'
#         response = self.view(request, place_id=self.place.id,
#                              pk=self.submission.id,
#                              submission_type='comments',
#                              dataset__owner__username=self.owner.username,
#                              dataset__slug=self.dataset.slug,
#                              )
#         assert_equal(response.status_code, 200)
#         data = json.loads(response.content)
#         assert_equal(data['animal'], 'tree frog')
#         assert_not_in('private-email', data)

#     @istest
#     def submission_get_request_retrieves_data_when_directly_authenticated_as_superuser(self):
#         self.submission.data = json.dumps({'animal': 'tree frog', 'private-email': 'admin@example.com'})
#         self.submission.save()
#         request = RequestFactory().get(self.url + '?include_private_data=on')
#         request.user = mock.Mock(**{'is_authenticated.return_value': True,
#                                     'is_superuser': True,
#                                     })
#         request.META['HTTP_ACCEPT'] = 'application/json'
#         response = self.view(request, place_id=self.place.id,
#                              pk=self.submission.id,
#                              submission_type='comments',
#                              dataset__owner__username=self.owner.username,
#                              dataset__slug=self.dataset.slug,
#                              )
#         assert_equal(response.status_code, 200)
#         data = json.loads(response.content)
#         assert_equal(data['animal'], 'tree frog')
#         assert_equal(data.get('private-email'), 'admin@example.com')

#     @istest
#     def submission_get_request_hides_private_data_when_authenticated_with_key(self):
#         from django.contrib.sessions.models import SessionStore
#         from sa_api_v2.apikey.auth import KEY_HEADER

#         self.submission.data = json.dumps({'animal': 'tree frog', 'private-email': 'admin@example.com'})
#         self.submission.save()
#         request = RequestFactory().get(self.url + '?include_private_data=on')
#         request.session = SessionStore()

#         request.META['HTTP_ACCEPT'] = 'application/json'
#         request.META[KEY_HEADER] = self.apikey.key
#         response = self.view(request, place_id=self.place.id,
#                              pk=self.submission.id,
#                              submission_type='comments',
#                              dataset__owner__username=self.owner.username,
#                              dataset__slug=self.dataset.slug,
#                              )
#         assert_equal(response.status_code, 403)

#     @istest
#     def submission_get_request_retrieves_private_data_when_authenticated_as_owner(self):
#         self.submission.data = json.dumps({'animal': 'tree frog', 'private-email': 'admin@example.com'})
#         self.submission.save()
#         request = RequestFactory().get(self.url + '?include_private_data=on')
#         request.user = self.submission.dataset.owner

#         request.META['HTTP_ACCEPT'] = 'application/json'
#         response = self.view(request, place_id=self.place.id,
#                              pk=self.submission.id,
#                              submission_type='comments',
#                              dataset__owner__username=self.owner.username,
#                              dataset__slug=self.dataset.slug,
#                              )
#         assert_equal(response.status_code, 200)
#         data = json.loads(response.content)
#         assert_equal(data.get('animal'), 'tree frog')
#         assert_equal(data.get('private-email'), 'admin@example.com')

#     @istest
#     def permissions_take_precedence_over_cache(self):
#         self.submission.data = json.dumps({'animal': 'tree frog', 'private-email': 'admin@example.com'})
#         self.submission.save()

#         # Anonymous user
#         request = RequestFactory().get(self.url + '?include_private_data=on')
#         request.user = mock.Mock(**{'is_authenticated.return_value': False,
#                                     'is_superuser': False,
#                                     })
#         request.META['HTTP_ACCEPT'] = 'application/json'
#         response = self.view(request, place_id=self.place.id,
#                              pk=self.submission.id,
#                              submission_type='comments',
#                              dataset__owner__username=self.owner.username,
#                              dataset__slug=self.dataset.slug,
#                              )
#         assert_equal(response.status_code, 403)

#         # Directly authenticated owner
#         request = RequestFactory().get(self.url + '?include_private_data=on')
#         request.user = self.submission.dataset.owner
#         request.META['HTTP_ACCEPT'] = 'application/json'
#         response = self.view(request, place_id=self.place.id,
#                              pk=self.submission.id,
#                              submission_type='comments',
#                              dataset__owner__username=self.owner.username,
#                              dataset__slug=self.dataset.slug,
#                              )
#         assert_equal(response.status_code, 200)

#         # Anonymous user again
#         request = RequestFactory().get(self.url + '?include_private_data=on')
#         request.user = mock.Mock(**{'is_authenticated.return_value': False,
#                                     'is_superuser': False,
#                                     })
#         request.META['HTTP_ACCEPT'] = 'application/json'
#         response = self.view(request, place_id=self.place.id,
#                              pk=self.submission.id,
#                              submission_type='comments',
#                              dataset__owner__username=self.owner.username,
#                              dataset__slug=self.dataset.slug,
#                              )
#         assert_equal(response.status_code, 403)



# class TestSubmissionCollectionView(TestCase):

#     def setUp(self):
#         User.objects.all().delete()
#         DataSet.objects.all().delete()
#         Place.objects.all().delete()
#         Submission.objects.all().delete()
#         SubmittedThing.objects.all().delete()
#         Activity.objects.all().delete()

#         self.owner = User.objects.create(username='myuser')
#         self.dataset = DataSet.objects.create(slug='data',
#                                               owner_id=self.owner.id)
#         self.visible_place = Place.objects.create(dataset_id=self.dataset.id, location='POINT (0 0)', visible=True)
#         self.visible_set = SubmissionSet.objects.create(place_id=self.visible_place.id, submission_type='vis')

#     @istest
#     def get_queryset_checks_visibility(self):
#         from ..views import SubmissionCollectionView
#         view = SubmissionCollectionView()

#         # Create two submissions, one visisble, one invisible.
#         visible_submission = Submission.objects.create(dataset_id=self.dataset.id, parent_id=self.visible_set.id, visible=True)
#         invisible_submission = Submission.objects.create(dataset_id=self.dataset.id, parent_id=self.visible_set.id, visible=False)

#         # Only visible Submissions by default...
#         view.request = mock.Mock(GET={})
#         qs = view.get_queryset()
#         assert_equal(qs.count(), 1)

#         # Or, all of them.
#         view.request = mock.Mock(GET={'include_invisible': 'on'})
#         qs = view.get_queryset()
#         assert_equal(qs.count(), 2)

#     @istest
#     def get_request_from_owner_should_return_private_data_for_all(self):
#         from ..views import SubmissionCollectionView
#         view = SubmissionCollectionView.as_view()

#         request_kwargs = {
#             'place_id': self.visible_place.id,
#             'submission_type': self.visible_set.submission_type,
#             'dataset__owner__username': self.owner.username,
#             'dataset__slug': self.dataset.slug,
#         }

#         # Create two submissions, one visisble, one invisible.
#         visible_submission = Submission.objects.create(dataset_id=self.dataset.id, parent_id=self.visible_set.id, visible=True,
#                                                        data=json.dumps({'x': 1, 'private-y': 2}))
#         invisible_submission = Submission.objects.create(dataset_id=self.dataset.id, parent_id=self.visible_set.id, visible=False,
#                                                          data=json.dumps({'x': 3, 'private-y': 4}))

#         request = RequestFactory().get(
#             reverse('submission_collection_by_dataset', kwargs=request_kwargs) + '?include_invisible=true&include_private_data=true',
#             content_type='application/json')
#         request.user = self.owner
#         request.META['HTTP_ACCEPT'] = 'application/json'

#         response = view(request, **request_kwargs)

#         assert_equal(response.status_code, 200)
#         response_data = json.loads(response.content)
#         assert_equal(len(response_data), 2)
#         assert_in('private-y', response_data[0])

#     @istest
#     def get_request_should_disallow_private_data_access(self):
#         from ..views import SubmissionCollectionView
#         view = SubmissionCollectionView.as_view()

#         request_kwargs = {
#             'place_id': self.visible_place.id,
#             'submission_type': self.visible_set.submission_type,
#             'dataset__owner__username': self.owner.username,
#             'dataset__slug': self.dataset.slug,
#         }

#         # Create two submissions, one visisble, one invisible.
#         visible_submission = Submission.objects.create(dataset_id=self.dataset.id, parent_id=self.visible_set.id, visible=True,
#                                                        data=json.dumps({'x': 1, 'private-y': 2}))
#         invisible_submission = Submission.objects.create(dataset_id=self.dataset.id, parent_id=self.visible_set.id, visible=False,
#                                                          data=json.dumps({'x': 3, 'private-y': 4}))

#         request = RequestFactory().get(
#             reverse('submission_collection_by_dataset', kwargs=request_kwargs) + '?include_invisible=true&include_private_data=true',
#             content_type='application/json')
#         request.META['HTTP_ACCEPT'] = 'application/json'

#         response = view(request, **request_kwargs)

#         assert_equal(response.status_code, 403)


# class TestActivityView(TestCase):

#     def setUp(self):
#         User.objects.all().delete()
#         DataSet.objects.all().delete()
#         Place.objects.all().delete()
#         Submission.objects.all().delete()
#         SubmittedThing.objects.all().delete()
#         Activity.objects.all().delete()

#         self.owner = User.objects.create(username='myuser')
#         self.dataset = DataSet.objects.create(slug='data',
#                                               owner_id=self.owner.id)
#         self.visible_place = Place.objects.create(dataset_id=self.dataset.id, location='POINT (0 0)', visible=True)
#         self.invisible_place = Place.objects.create(dataset_id=self.dataset.id, location='POINT (0 0)', visible=False)

#         self.visible_set = SubmissionSet.objects.create(place_id=self.visible_place.id, submission_type='vis')
#         self.invisible_set = SubmissionSet.objects.create(place_id=self.invisible_place.id, submission_type='invis')

#         self.visible_submission = Submission.objects.create(dataset_id=self.dataset.id, parent_id=self.visible_set.id)
#         self.invisible_submission = Submission.objects.create(dataset_id=self.dataset.id, parent_id=self.invisible_set.id)
#         self.invisible_submission2 = Submission.objects.create(dataset_id=self.dataset.id, parent_id=self.visible_set.id, visible=False)

#         # Note this implicitly creates an Activity.
#         visible_place_activity = Activity.objects.get(data_id=self.visible_place.id)
#         visible_submission_activity = Activity.objects.get(data_id=self.visible_submission.id)

#         self.activities = [
#             visible_place_activity,
#             visible_submission_activity,
#             Activity.objects.create(data=self.visible_place, action='update'),
#             Activity.objects.create(data=self.visible_place, action='delete'),
#         ]

#         kwargs = dict(data__dataset__owner__username=self.owner.username, data__dataset__slug='data')
#         self.url = reverse('activity_collection_by_dataset', kwargs=kwargs)

#         # This was here first and marked as deprecated, but above doesn't
#         # work either.
#         # self.url = reverse('activity_collection')

#     @istest
#     def get_queryset_no_params_returns_visible(self):
#         from ..views import ActivityView
#         view = ActivityView()
#         view.request = RequestFactory().get(self.url)
#         qs = view.get_queryset()
#         self.assertEqual(qs.count(), len(self.activities))

#     @istest
#     def get_queryset_with_visible_all_returns_all(self):
#         from ..views import ActivityView
#         view = ActivityView()
#         view.request = RequestFactory().get(self.url + '?visible=all')
#         qs = view.get_queryset()
#         self.assertEqual(qs.count(), 7)

#     @istest
#     def get_queryset_before(self):
#         from ..views import ActivityView
#         view = ActivityView()
#         ids = sorted([a.id for a in self.activities])
#         view.request = RequestFactory().get(self.url + '?before=%d' % ids[0])
#         self.assertEqual(view.get_queryset().count(), 1)
#         view.request = RequestFactory().get(self.url + '?before=%d' % ids[-1])
#         self.assertEqual(view.get_queryset().count(), len(self.activities))

#     @istest
#     def get_queryset_after(self):
#         from ..views import ActivityView
#         view = ActivityView()
#         ids = sorted([a.id for a in self.activities])
#         view.request = RequestFactory().get(self.url + '?after=%d' % (ids[0] - 1))
#         self.assertEqual(view.get_queryset().count(), 4)
#         view.request = RequestFactory().get(self.url + '?after=%d' % ids[0])
#         self.assertEqual(view.get_queryset().count(), 3)
#         view.request = RequestFactory().get(self.url + '?after=%d' % ids[-1])
#         self.assertEqual(view.get_queryset().count(), 0)

#     @istest
#     def get_with_limit(self):
#         from ..views import ActivityView
#         view = ActivityView()
#         view.request = RequestFactory().get(self.url + '?limit')
#         self.assertEqual(view.get(view.request).count(), len(self.activities))

#         view.request = RequestFactory().get(self.url + '?limit=99')
#         self.assertEqual(view.get(view.request).count(), len(self.activities))

#         view.request = RequestFactory().get(self.url + '?limit=0')
#         self.assertEqual(view.get(view.request).count(), 0)

#         view.request = RequestFactory().get(self.url + '?limit=1')
#         self.assertEqual(view.get(view.request).count(), 1)

#     @istest
#     def returns_from_cache_based_on_params(self):
#         from ..views import ActivityView
#         no_params = RequestFactory().get(self.url)
#         vis_param = RequestFactory().get(self.url + '?visible=all')
#         no_params.user = self.owner
#         vis_param.user = self.owner
#         no_params.META['HTTP_ACCEPT'] = 'application/json'
#         vis_param.META['HTTP_ACCEPT'] = 'application/json'

#         view = ActivityView.as_view()
#         view(no_params, data__dataset__owner__username='myuser', data__dataset__slug='data')
#         view(vis_param, data__dataset__owner__username='myuser', data__dataset__slug='data')

#         # Both requests should be made without hitting the database...
#         with self.assertNumQueries(0):
#             no_params_response = view(no_params, data__dataset__owner__username='myuser', data__dataset__slug='data')
#             vis_param_response = view(vis_param, data__dataset__owner__username='myuser', data__dataset__slug='data')

#         # But they should each correspond to different cached values.
#         self.assertNotEqual(no_params_response.content, vis_param_response.content)

#     @istest
#     def returns_from_db_when_object_changes(self):
#         from ..views import ActivityView
#         request = RequestFactory().get(self.url + '?visible=all')
#         request.user = self.owner
#         request.META['HTTP_ACCEPT'] = 'application/json'

#         view = ActivityView.as_view()
#         view(request, data__dataset__owner__username='myuser', data__dataset__slug='data')

#         # Next requests should be made without hitting the database...
#         with self.assertNumQueries(0):
#             response1 = view(request, data__dataset__owner__username='myuser', data__dataset__slug='data')

#         # But cache should be invalidated after changing a place.
#         self.visible_place.location.x = 1
#         self.visible_place.save()
#         response2 = view(request, data__dataset__owner__username='myuser', data__dataset__slug='data')

#         self.assertNotEqual(response1.content, response2.content)


# class TestAbsUrlMixin (object):

#     @istest
#     def test_process_urls(self):
#         data = {
#             'url': '/foo/bar',
#             'x': 'y',
#             'children': [{'x': 'y', 'url': '/hello/cats'},
#                          {'a': 'b', 'url': 'bye/../dogs'},
#                          ]
#         }
#         from ..views import AbsUrlMixin
#         aum = AbsUrlMixin()
#         aum.request = RequestFactory().get('/path_is_irrelevant')
#         aum.process_urls(data)
#         assert_equal(data['url'], 'http://testserver/foo/bar')
#         assert_equal(data['children'][0]['url'],
#                      'http://testserver/hello/cats')
#         assert_equal(data['children'][1]['url'],
#                      'http://testserver/dogs')


# class TestPlaceCollectionView(TestCase):

#     def _cleanup(self):
#         from sa_api_v2 import models
#         models.Submission.objects.all().delete()
#         models.SubmissionSet.objects.all().delete()
#         models.Place.objects.all().delete()
#         models.DataSet.objects.all().delete()
#         models.Activity.objects.all().delete()
#         User.objects.all().delete()

#         cache_buffer.reset()
#         django_cache.clear()

#     def setUp(self):
#         self._cleanup()

#     def tearDown(self):
#         self._cleanup()

#     @istest
#     def post_with_permission_invalidates_cache(self):
#         from ..views import PlaceCollectionView, models
#         view = PlaceCollectionView().as_view()
#         # Need an existing DataSet.
#         user = User.objects.create(username='test-user')
#         ds = models.DataSet.objects.create(owner=user, id=789,
#                                            slug='stuff')
#         #place = models.Place.objects.create(dataset=ds, id=123)
#         uri_args = {
#             'dataset__owner__username': user.username,
#             'dataset__slug': ds.slug,
#         }
#         uri = reverse('place_collection_by_dataset', kwargs=uri_args)
#         factory = RequestFactory()

#         get_request = factory.get(uri, content_type='application/json')
#         get_request.user = user
#         get_request.META['HTTP_ACCEPT'] = 'application/json'

#         with self.assertNumQueries(1):
#             response1 = view(get_request, **uri_args)
#         with self.assertNumQueries(0):
#             response2 = view(get_request, **uri_args)
#         self.assertEqual(response1.content, response2.content)

#         data = {'location': {'lat': 39.94494, 'lng': -75.06144},
#                 'description': 'hello', 'location_type': 'School',
#                 'name': 'Ward Melville HS',
#                 'submitter_name': 'Joe',
#                 'visible': True,
#                 }

#         post_request = factory.post(uri, data=json.dumps(data),
#                                     content_type='application/json')
#         post_request.user = user
#         post_request.META['HTTP_ACCEPT'] = 'application/json'

#         self.assertEqual(models.Place.objects.count(), 0)
#         res = view(post_request, **uri_args)
#         print res.content
#         self.assertEqual(models.Place.objects.count(), 1)

#         with self.assertNumQueries(1):
#             response3 = view(get_request, **uri_args)
#         assert_not_equal(response1.content, response3.content)

#     @istest
#     def missing_cache_metakey_invalidates_cache(self):
#         from ..views import PlaceCollectionView, models
#         view = PlaceCollectionView().as_view()
#         # Need an existing DataSet.
#         user = User.objects.create(username='test-user')
#         ds = models.DataSet.objects.create(owner=user, id=789,
#                                            slug='stuff')
#         #place = models.Place.objects.create(dataset=ds, id=123)
#         uri_args = {
#             'dataset__owner__username': user.username,
#             'dataset__slug': ds.slug,
#         }
#         uri = reverse('place_collection_by_dataset', kwargs=uri_args)
#         factory = RequestFactory()

#         get_request = factory.get(uri, content_type='application/json')
#         get_request.user = user
#         get_request.META['HTTP_ACCEPT'] = 'application/json'

#         with self.assertNumQueries(1):
#             response1 = view(get_request, **uri_args)
#         with self.assertNumQueries(0):
#             response2 = view(get_request, **uri_args)
#         self.assertEqual(response1.content, response2.content)

#         temp_collection_view = PlaceCollectionView()
#         temp_collection_view.request = get_request
#         metakey = temp_collection_view.get_cache_metakey()
#         cache.delete(metakey)

#         # Without the metakey, the cache for the request should be assumed
#         # invalid.
#         with self.assertNumQueries(1):
#             response3 = view(get_request, **uri_args)
#         assert_equal(response1.content, response3.content)

#     @istest
#     def post_creates_a_place(self):
#         from ..views import PlaceCollectionView, models
#         view = PlaceCollectionView().as_view()
#         # Need an existing DataSet.
#         user = User.objects.create(username='test-user')
#         ds = models.DataSet.objects.create(owner=user, id=789,
#                                            slug='stuff')
#         #place = models.Place.objects.create(dataset=ds, id=123)
#         uri_args = {
#             'dataset__owner__username': user.username,
#             'dataset__slug': ds.slug,
#         }
#         uri = reverse('place_collection_by_dataset', kwargs=uri_args)
#         data = {'location': {'lat': 39.94494, 'lng': -75.06144},
#                 'description': 'hello', 'location_type': 'School',
#                 'name': 'Ward Melville HS',
#                 'submitter_name': 'Joe',
#                 }
#         request = RequestFactory().post(uri, data=json.dumps(data),
#                                         content_type='application/json')
#         request.user = user
#         # Ready to post. Verify there are no Places yet...
#         assert_equal(models.Place.objects.count(), 0)
#         assert_equal(models.Activity.objects.count(), 0)

#         response = view(request, **uri_args)

#         # We got a Created status...
#         assert_equal(response.status_code, 201)
#         assert_in(uri, response.get('Location'))

#         # And we have a place:
#         assert_equal(models.Place.objects.count(), 1)

#         # And we have activity:
#         assert_equal(models.Activity.objects.count(), 1)

#         # And that place is visible. See story #38212759
#         # assert_equal(models.Place.objects.all()[0].visible, True)
#         # assert_equal(response.cleaned_content['visible'], True)

#     @istest
#     def post_with_silent_header_creates_no_activity(self):
#         from ..views import PlaceCollectionView, models
#         view = PlaceCollectionView().as_view()
#         # Need an existing DataSet.
#         user = User.objects.create(username='test-user')
#         ds = models.DataSet.objects.create(owner=user, id=789,
#                                            slug='stuff')
#         #place = models.Place.objects.create(dataset=ds, id=123)
#         uri_args = {
#             'dataset__owner__username': user.username,
#             'dataset__slug': ds.slug,
#         }
#         uri = reverse('place_collection_by_dataset', kwargs=uri_args)
#         data = {'location': {'lat': 39.94494, 'lng': -75.06144},
#                 'description': 'hello', 'location_type': 'School',
#                 'name': 'Ward Melville HS',
#                 'submitter_name': 'Joe',
#                 }
#         request = RequestFactory().post(uri, data=json.dumps(data),
#                                         content_type='application/json',
#                                         HTTP_X_SHAREABOUTS_SILENT='True')

#         request.user = user
#         # Ready to post. Verify there is no Activity yet...
#         assert_equal(models.Activity.objects.count(), 0)

#         response = view(request, **uri_args)

#         # We got a Created status...
#         assert_equal(response.status_code, 201)
#         assert_in(uri, response.get('Location'))

#         # And we have no activity:
#         assert_equal(models.Activity.objects.count(), 0)

#     @istest
#     def get_queryset_checks_visibility(self):
#         from ..views import PlaceCollectionView, models
#         user = User.objects.create(username='test-user')
#         ds = models.DataSet.objects.create(owner=user, id=789,
#                                            slug='stuff')
#         location = 'POINT (0.0 0.0)'
#         models.Place.objects.create(dataset=ds, id=123, location=location,
#                                     visible=True)
#         models.Place.objects.create(dataset=ds, id=124, location=location,
#                                     visible=True)
#         models.Place.objects.create(dataset=ds, id=456, location=location,
#                                     visible=False)
#         models.Place.objects.create(dataset=ds, id=457, location=location,
#                                     visible=False)
#         view = PlaceCollectionView()

#         # Only visible Places by default...
#         view.request = mock.Mock(GET={})
#         view.calculate_flags(view.request)
#         qs = view.get_queryset()
#         assert_equal(qs.count(), 2)
#         ids = set([place.id for place in qs])
#         assert_equal(ids, set([123, 124]))

#         # Or, all of them.
#         view.request = mock.Mock(GET={'include_invisible': 'on'})
#         view.calculate_flags(view.request)
#         qs = view.get_queryset()
#         assert_equal(qs.count(), 4)
#         ids = set([place.id for place in qs])
#         assert_equal(ids, set([123, 124, 456, 457]))

#     @istest
#     def order_by_proximity_to_a_point(self):
#         from ..views import PlaceCollectionView, models

#         user = User.objects.create(username='test-user')
#         ds = models.DataSet.objects.create(owner=user, id=789,
#                                            slug='stuff')
#         location = 'POINT (0.0 0.0)'
#         models.Place.objects.create(dataset=ds, id=123, location='POINT (1 1)', visible=True, data=json.dumps({'favorite_food': 'pizza', 'favorite_color': 'red'}))
#         models.Place.objects.create(dataset=ds, id=124, location='POINT (0 0)', visible=True, data=json.dumps({'favorite_food': 'asparagus', 'favorite_color': 'green'}))
#         models.Place.objects.create(dataset=ds, id=125, location='POINT (0 2)', visible=True, data=json.dumps({'favorite_food': 'pizza', 'favorite_color': 'blue'}))
#         models.Place.objects.create(dataset=ds, id=126, location='POINT (1 0.5)', visible=True, data=json.dumps({'favorite_food': 'chili', 'favorite_color': 'yellow'}))
#         view = PlaceCollectionView.as_view()

#         request = RequestFactory().get('/api/v1/test-user/datasets/stuff/places/?near=0.5,1.0')
#         request.user = user
#         request.META['HTTP_ACCEPT'] = 'application/json'

#         response = view(request,
#                         dataset__owner__username='test-user',
#                         dataset__slug='stuff')

#         places = json.loads(response.content)
#         ids = [place['id'] for place in places]
#         assert_equal(ids, [126, 123, 124, 125])

#     @istest
#     def enforces_valid_near_parameter(self):
#         from ..views import PlaceCollectionView, models
#         view = PlaceCollectionView.as_view()

#         # Single number
#         request = RequestFactory().get('/api/v1/test-user/datasets/stuff/places/?near=0.5')
#         request.META['HTTP_ACCEPT'] = 'application/json'
#         response = view(request, dataset__owner__username='test-user', dataset__slug='stuff')
#         assert_equal(response.status_code, 400)

#         # Two items, non-numeric
#         request = RequestFactory().get('/api/v1/test-user/datasets/stuff/places/?near=0.5,hello')
#         request.META['HTTP_ACCEPT'] = 'application/json'
#         response = view(request, dataset__owner__username='test-user', dataset__slug='stuff')
#         assert_equal(response.status_code, 400)

#         # More than two numbers
#         request = RequestFactory().get('/api/v1/test-user/datasets/stuff/places/?near=1,1,1')
#         request.META['HTTP_ACCEPT'] = 'application/json'
#         response = view(request, dataset__owner__username='test-user', dataset__slug='stuff')
#         assert_equal(response.status_code, 400)

#     @istest
#     def get_filters_on_data_fields(self):
#         from ..views import PlaceCollectionView, models

#         user = User.objects.create(username='test-user')
#         ds = models.DataSet.objects.create(owner=user, id=789,
#                                            slug='stuff')
#         location = 'POINT (0.0 0.0)'
#         models.Place.objects.create(dataset=ds, id=123, location=location, visible=True, data=json.dumps({'favorite_food': 'pizza', 'favorite_color': 'red'}))
#         models.Place.objects.create(dataset=ds, id=124, location=location, visible=True, data=json.dumps({'favorite_food': 'asparagus', 'favorite_color': 'green'}))
#         models.Place.objects.create(dataset=ds, id=125, location=location, visible=True, data=json.dumps({'favorite_food': 'pizza', 'favorite_color': 'blue'}))
#         models.Place.objects.create(dataset=ds, id=126, location=location, visible=True, data=json.dumps({'favorite_food': 'chili', 'favorite_color': 'yellow'}))
#         view = PlaceCollectionView()

#         # Only visible Places with favorite food 'pizza'...
#         request = RequestFactory().get('/api/v1/datasets/test-user/stuff/places/?favorite_food=pizza')
#         request.user = user
#         request.META['HTTP_ACCEPT'] = 'application/json'
#         view.request = request
#         response = view.dispatch(request,
#                             dataset__owner__username='test-user',
#                             dataset__slug='stuff')

#         places = json.loads(response.content)

#         assert_equal(len(places), 2)
#         ids = set([place['id'] for place in places])
#         assert_equal(ids, set([123, 125]))

#         # Only visible Places with favorite color 'red' or 'yellow'...
#         request = RequestFactory().get('/api/v1/datasets/test-user/stuff/places/?favorite_color=red&favorite_color=yellow')
#         request.user = user
#         request.META['HTTP_ACCEPT'] = 'application/json'
#         view.request = request
#         response = view.dispatch(request,
#                             dataset__owner__username='test-user',
#                             dataset__slug='stuff')

#         places = json.loads(response.content)


#         assert_equal(len(places), 2)
#         ids = set([place['id'] for place in places])
#         assert_equal(ids, set([123, 126]))

#         # Only visible Places with favorite color 'red' or 'yellow'...
#         request = RequestFactory().get('/api/v1/datasets/test-user/stuff/places/?favorite_color=red&favorite_color=yellow&favorite_food=pizza')
#         request.user = user
#         request.META['HTTP_ACCEPT'] = 'application/json'
#         view.request = request
#         response = view.dispatch(request,
#                             dataset__owner__username='test-user',
#                             dataset__slug='stuff')

#         places = json.loads(response.content)


#         assert_equal(len(places), 1)
#         ids = set([place['id'] for place in places])
#         assert_equal(ids, set([123]))

#     @istest
#     def get_request_from_owner_should_return_private_data_for_all(self):
#         from ..views import PlaceCollectionView
#         view = PlaceCollectionView.as_view()

#         owner = User.objects.create(username='superman')
#         dataset = DataSet.objects.create(owner=owner, slug='moth')

#         request_kwargs = {
#             'dataset__owner__username': owner.username,
#             'dataset__slug': dataset.slug,
#         }

#         # Create two places, one visisble, one invisible.
#         visible_place = Place.objects.create(dataset_id=dataset.id, location='POINT(0 0)', visible=True,
#                                              data=json.dumps({'x': 1, 'private-y': 2}))
#         invisible_place = Place.objects.create(dataset_id=dataset.id, location='POINT(0 0)', visible=False,
#                                                data=json.dumps({'x': 3, 'private-y': 4}))

#         request = RequestFactory().get(
#             reverse('place_collection_by_dataset', kwargs=request_kwargs) + '?include_invisible=true&include_private_data=true',
#             content_type='application/json')
#         request.user = owner
#         request.META['HTTP_ACCEPT'] = 'application/json'

#         response = view(request, **request_kwargs)

#         assert_equal(response.status_code, 200)
#         response_data = json.loads(response.content)
#         assert_equal(len(response_data), 2)
#         assert_in('private-y', response_data[0])

#         # Check for nested submissions
#         ss = SubmissionSet.objects.create(place=visible_place, submission_type="witnesses")
#         submission = Submission.objects.create(dataset_id=dataset.id, parent_id=ss.id, data=json.dumps({'x': 5, 'private-y': 6}))

#         # ... first without private data flag
#         request = RequestFactory().get(
#             reverse('place_collection_by_dataset', kwargs=request_kwargs) + '?include_private_data=false&include_submissions=true',
#             content_type='application/json')
#         request.user = owner
#         request.META['HTTP_ACCEPT'] = 'application/json'

#         response = view(request, **request_kwargs)

#         assert_equal(response.status_code, 200)
#         response_data = json.loads(response.content)
#         submission_set = response_data[0]['submissions'][0]
#         assert_equal(type(response_data), list)
#         assert_not_in('private-y', submission_set[0])

#         # ... and then with private data flag
#         request = RequestFactory().get(
#             reverse('place_collection_by_dataset', kwargs=request_kwargs) + '?include_private_data=true&include_submissions=true',
#             content_type='application/json')
#         request.user = owner
#         request.META['HTTP_ACCEPT'] = 'application/json'

#         response = view(request, **request_kwargs)

#         assert_equal(response.status_code, 200)
#         response_data = json.loads(response.content)
#         submission_set = response_data[0]['submissions'][0]
#         assert_equal(type(response_data), list)
#         assert_in('private-y', submission_set[0])



#     @istest
#     def get_request_should_disallow_private_data_access(self):
#         from ..views import PlaceCollectionView
#         view = PlaceCollectionView.as_view()

#         owner = User.objects.create(username='superman')
#         dataset = DataSet.objects.create(owner=owner, slug='moth')

#         request_kwargs = {
#             'dataset__owner__username': owner.username,
#             'dataset__slug': dataset.slug,
#         }

#         # Create two submissions, one visisble, one invisible.
#         visible_place = Place.objects.create(dataset_id=dataset.id, location='POINT(0 0)', visible=True,
#                                              data=json.dumps({'x': 1, 'private-y': 2}))
#         invisible_place = Place.objects.create(dataset_id=dataset.id, location='POINT(0 0)', visible=False,
#                                                data=json.dumps({'x': 3, 'private-y': 4}))

#         request = RequestFactory().get(
#             reverse('place_collection_by_dataset', kwargs=request_kwargs) + '?include_invisible=true&include_private_data=true',
#             content_type='application/json')
#         request.META['HTTP_ACCEPT'] = 'application/json'

#         response = view(request, **request_kwargs)

#         assert_equal(response.status_code, 403)


# class TestApiKeyCollectionView(TestCase):

#     def _cleanup(self):
#         from sa_api_v2 import models
#         from sa_api_v2.apikey.models import ApiKey
#         models.DataSet.objects.all().delete()
#         User.objects.all().delete()
#         ApiKey.objects.all().delete()

#     def setUp(self):
#         self._cleanup()
#         # Need an existing DataSet.
#         user = User.objects.create(username='test-user')
#         self.dataset = DataSet.objects.create(owner=user, id=789,
#                                               slug='stuff')
#         self.uri_args = {
#             'datasets__owner__username': user.username,
#             'datasets__slug': self.dataset.slug,
#         }
#         uri = reverse('api_key_collection_by_dataset',
#                       kwargs=self.uri_args)
#         self.request = RequestFactory().get(uri)
#         self.view = ApiKeyCollectionView().as_view()

#     def tearDown(self):
#         self._cleanup()

#     @istest
#     def get__not_allowed_anonymous(self):
#         self.request.user = mock.Mock(**{'is_authenticated.return_value': False,
#                                          'is_superuser': False})
#         response = self.view(self.request, **self.uri_args)
#         assert_equal(response.status_code, 403)

#     @istest
#     def get_is_allowed_if_admin(self):
#         self.request.user = mock.Mock(**{'is_authenticated.return_value': True,
#                                          'is_superuser': True})
#         response = self.view(self.request, **self.uri_args)
#         assert_equal(response.status_code, 200)

#     @istest
#     def get_is_allowed_if_owner(self):
#         self.request.user = self.dataset.owner
#         response = self.view(self.request, **self.uri_args)
#         assert_equal(response.status_code, 200)

#     @istest
#     def get_not_allowed_with_api_key(self):
#         from ..apikey.auth import KEY_HEADER
#         self.request.META[KEY_HEADER] = 'test'
#         # ... Even if the user is good, the API key makes us
#         # distrust this request.
#         self.request.user = self.dataset.owner
#         response = self.view(self.request, **self.uri_args)
#         assert_equal(response.status_code, 403)

#     @istest
#     def get_not_allowed_with_wrong_user(self):
#         self.request.user = mock.Mock(**{'is_authenticated.return_value': True,
#                                          'username': 'A really shady person',
#                                          'is_superuser': False,
#                                          })
#         response = self.view(self.request, **self.uri_args)
#         assert_equal(response.status_code, 403)

# class TestOwnerPasswordView(TestCase):

#     def _cleanup(self):
#         User.objects.all().delete()

#     def setUp(self):
#         self._cleanup()
#         self.user1 = User.objects.create(username='test-user1', password='abc')
#         self.user2 = User.objects.create(username='test-user2', password='123')

#         self.uri_args = {
#             'owner__username': self.user1.username,
#         }
#         self.uri = reverse('owner_password',
#                            kwargs=self.uri_args)
#         self.request = RequestFactory().get(self.uri)
#         self.view = OwnerPasswordView().as_view()

#     def tearDown(self):
#         self._cleanup()

#     @istest
#     def put_changes_password_if_user_is_authenticated(self):
#         request = RequestFactory().put(self.uri, data='new-password', content_type="text/plain")

#         user1 = User.objects.get(username='test-user1')
#         current_password = user1.password

#         request.user = user1
#         self.view(request, owner__username='test-user1')

#         user1 = User.objects.get(username='test-user1')
#         new_password = user1.password

#         assert_not_equal(current_password, new_password)

#     @istest
#     def put_403s_if_user_is_unauthenticated(self):
#         request = RequestFactory().put(self.uri, data='new-password', content_type="text/plain")

#         user1 = User.objects.get(username='test-user1')
#         current_password = user1.password

#         response = self.view(request, owner__username='test-user1')

#         user1 = User.objects.get(username='test-user1')
#         new_password = user1.password

#         assert_equal(current_password, new_password)
#         assert_equal(response.status_code, 403)

#     @istest
#     def put_403s_if_wrong_user_is_authenticated(self):
#         request = RequestFactory().put(self.uri, data='new-password', content_type="text/plain")

#         user1 = User.objects.get(username='test-user1')
#         user2 = User.objects.get(username='test-user2')
#         current_password = user1.password

#         request.user = user2
#         response = self.view(request, owner__username='test-user1')

#         user1 = User.objects.get(username='test-user1')
#         new_password = user1.password

#         assert_equal(current_password, new_password)
#         assert_equal(response.status_code, 403)


# class TestAttachmentView (TestCase):
#     def setUp(self):
#         User.objects.all().delete()
#         DataSet.objects.all().delete()
#         Place.objects.all().delete()
#         Attachment.objects.all().delete()

#         self.owner = User.objects.create_user('user', password='password')
#         self.dataset = DataSet.objects.create(slug='data',
#                                               owner_id=self.owner.id)
#         self.place = Place.objects.create(location='POINT(0 0)',
#                                           dataset_id=self.dataset.id)
#         self.submission_set = SubmissionSet.objects.create(place=self.place,
#                                                            submission_type='comments')
#         self.submission = Submission.objects.create(parent=self.submission_set,
#                                                     dataset_id=self.dataset.id)
#         self.place_url = reverse('place_attachment_by_dataset', args=['user', 'data', self.place.id])
#         self.submission_url = reverse('submission_attachment_by_dataset',
#                                       args=['user', 'data', self.place.id, 'comments', self.submission.id])

#     @istest
#     def creates_attachment_for_a_place(self):
#         client = Client()

#         # Set up a dummy file
#         from StringIO import StringIO
#         import re
#         f = StringIO('This is test content in a "file"')
#         f.name = 'myfile.txt'

#         # Send the request
#         assert client.login(username='user', password='password')
#         response = client.post(self.place_url, {'name': 'test_attachment', 'file': f})

#         assert_equal(response.status_code, 201)

#         a = self.place.attachments.all()[0]
#         file_prefix_pattern = r'^attachments/\w+-'
#         assert_equal(a.name, 'test_attachment')
#         assert_is_not_none(re.match(file_prefix_pattern + 'myfile.txt$', a.file.name))
#         assert_equal(a.file.read(), 'This is test content in a "file"')

#     @istest
#     def creates_attachment_for_a_submission(self):
#         client = Client()

#         # Set up a dummy file
#         from StringIO import StringIO
#         f = StringIO('This is test content in a "file"')
#         f.name = 'myfile.txt'

#         # Send the request
#         assert client.login(username='user', password='password')
#         response = client.post(self.submission_url, {'name': 'test_attachment', 'file': f})

#         assert_equal(response.status_code, 201)

#         a = self.submission.attachments.all()[0]
#         assert_equal(a.name, 'test_attachment')
#         assert_equal(a.file.read(), 'This is test content in a "file"')
