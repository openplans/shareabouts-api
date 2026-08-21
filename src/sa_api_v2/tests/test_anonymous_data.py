from django.test import TestCase
from django.test.client import RequestFactory
from django.urls import reverse
import json
from sa_api_v2.models import User, DataSet, Place, Submission, AnonymousValues, DataSetPermission
from sa_api_v2.apikey.models import ApiKey
from sa_api_v2.apikey.auth import KEY_HEADER
from sa_api_v2.views import (
    PlaceListView, PlaceInstanceView, SubmissionListView, SubmissionInstanceView,
    DataSetSubmissionListView, DataSetInstanceView,
    PlaceAnonymousDataListView, SubmissionSetAnonymousDataListView
)


class APITestMixin (object):
    def assertStatusCode(self, response, *expected):
        self.assertIn(response.status_code, expected,
            'Status code not in %s response: (%s) %s' %
            (expected, response.status_code, getattr(response, 'rendered_content', b'')))


class TestAnonymousDataViews (APITestMixin, TestCase):
    def setUp(self):
        User.objects.all().delete()
        DataSet.objects.all().delete()
        Place.objects.all().delete()
        Submission.objects.all().delete()
        AnonymousValues.objects.all().delete()

        self.factory = RequestFactory()
        self.owner = User.objects.create_user(username='datasetowner', email='owner@example.com')
        self.other_user = User.objects.create_user(username='otheruser', email='other@example.com')

        self.dataset = DataSet.objects.create(slug='my-ds', owner=self.owner)

        self.place1 = Place.objects.create(dataset=self.dataset, geometry='POINT(1 1)')
        self.place2 = Place.objects.create(dataset=self.dataset, geometry='POINT(2 2)')

        self.comment1 = Submission.objects.create(dataset=self.dataset, place=self.place1, set_name='comments')
        self.comment2 = Submission.objects.create(dataset=self.dataset, place=self.place2, set_name='comments')

        # Create anonymous data records
        self.anon_place1 = AnonymousValues.objects.create(
            dataset=self.dataset, set_name='places', data={'age': '25-34', 'race': 'Asian'}
        )
        self.anon_place2 = AnonymousValues.objects.create(
            dataset=self.dataset, set_name='places', data={'age': '35-44', 'race': 'White'}
        )
        self.anon_comment1 = AnonymousValues.objects.create(
            dataset=self.dataset, set_name='comments', data={'rating': 5, 'sentiment': 'positive'}
        )
        self.anon_ballot1 = AnonymousValues.objects.create(
            dataset=self.dataset, set_name='ballots', data={'proposals': ['p1', 'p2']}
        )

        # API key for owner
        self.owner_apikey = ApiKey.objects.create(dataset=self.dataset, key='ownerkey')
        self.owner_apikey.permissions.add_permission('places', True, True, True, True, can_access_protected=True)
        self.owner_apikey.permissions.add_permission('comments', True, True, True, True, can_access_protected=True)
        self.owner_apikey.permissions.add_permission('ballots', True, True, True, True, can_access_protected=True)

        # API key for public (no protected access)
        self.public_apikey = ApiKey.objects.create(dataset=self.dataset, key='publickey')
        self.public_apikey.permissions.add_permission('places', True, True, False, False, can_access_protected=False)
        self.public_apikey.permissions.add_permission('comments', True, True, False, False, can_access_protected=False)

    # -------------------------------------------------------------------------
    # Dataset Detail View Summaries
    # -------------------------------------------------------------------------

    def test_dataset_detail_without_include_anonymous(self):
        view = DataSetInstanceView.as_view()
        path = reverse('dataset-detail', kwargs={'owner_username': self.owner.username, 'dataset_slug': self.dataset.slug})
        request = self.factory.get(path)
        request.user = self.owner
        response = view(request, owner_username=self.owner.username, dataset_slug=self.dataset.slug)
        self.assertStatusCode(response, 200)

        data = json.loads(response.rendered_content)
        self.assertNotIn('anonymous_data', data['places'])
        for set_name, set_summary in data['submission_sets'].items():
            self.assertNotIn('anonymous_data', set_summary)

    def test_dataset_detail_with_include_anonymous(self):
        view = DataSetInstanceView.as_view()
        path = reverse('dataset-detail', kwargs={'owner_username': self.owner.username, 'dataset_slug': self.dataset.slug})
        request = self.factory.get(path + '?include_anonymous')
        request.user = self.owner
        response = view(request, owner_username=self.owner.username, dataset_slug=self.dataset.slug)
        self.assertStatusCode(response, 200)

        data = json.loads(response.rendered_content)
        # Places summary should have anonymous_data
        self.assertIn('anonymous_data', data['places'])
        self.assertEqual(data['places']['anonymous_data']['length'], 2)
        self.assertTrue(data['places']['anonymous_data']['url'].endswith('/places/anonymous'))

        # Comments summary should have anonymous_data
        self.assertIn('comments', data['submission_sets'])
        self.assertIn('anonymous_data', data['submission_sets']['comments'])
        self.assertEqual(data['submission_sets']['comments']['anonymous_data']['length'], 1)
        self.assertTrue(data['submission_sets']['comments']['anonymous_data']['url'].endswith('/comments/anonymous'))

    # -------------------------------------------------------------------------
    # Place List View Summaries
    # -------------------------------------------------------------------------

    def test_place_list_without_include_anonymous(self):
        view = PlaceListView.as_view()
        path = reverse('place-list', kwargs={'owner_username': self.owner.username, 'dataset_slug': self.dataset.slug})
        request = self.factory.get(path)
        request.user = self.owner
        response = view(request, owner_username=self.owner.username, dataset_slug=self.dataset.slug)
        self.assertStatusCode(response, 200)

        data = json.loads(response.rendered_content)
        self.assertNotIn('anonymous_data', data)

    def test_place_list_with_include_anonymous(self):
        view = PlaceListView.as_view()
        path = reverse('place-list', kwargs={'owner_username': self.owner.username, 'dataset_slug': self.dataset.slug})
        request = self.factory.get(path + '?include_anonymous')
        request.user = self.owner
        response = view(request, owner_username=self.owner.username, dataset_slug=self.dataset.slug)
        self.assertStatusCode(response, 200)

        data = json.loads(response.rendered_content)
        self.assertIn('anonymous_data', data)
        self.assertEqual(data['anonymous_data']['length'], 2)
        self.assertTrue(data['anonymous_data']['url'].endswith('/places/anonymous'))

        # Check that individual features' submission_sets do NOT contain anonymous_data
        for feature in data['features']:
            submission_sets = feature['properties'].get('submission_sets', {})
            for set_name, set_info in submission_sets.items():
                self.assertNotIn('anonymous_data', set_info)

    # -------------------------------------------------------------------------
    # Dataset-level Submission Set List View Summaries
    # -------------------------------------------------------------------------

    def test_dataset_submission_list_with_include_anonymous(self):
        view = DataSetSubmissionListView.as_view()
        path = reverse('dataset-submission-list', kwargs={
            'owner_username': self.owner.username,
            'dataset_slug': self.dataset.slug,
            'submission_set_name': 'comments'
        })
        request = self.factory.get(path + '?include_anonymous')
        request.user = self.owner
        response = view(request, owner_username=self.owner.username, dataset_slug=self.dataset.slug, submission_set_name='comments')
        self.assertStatusCode(response, 200)

        data = json.loads(response.rendered_content)
        self.assertIn('anonymous_data', data)
        self.assertEqual(data['anonymous_data']['length'], 1)
        self.assertTrue(data['anonymous_data']['url'].endswith('/comments/anonymous'))

    def test_dataset_submission_list_without_include_anonymous(self):
        view = DataSetSubmissionListView.as_view()
        path = reverse('dataset-submission-list', kwargs={
            'owner_username': self.owner.username,
            'dataset_slug': self.dataset.slug,
            'submission_set_name': 'comments'
        })
        request = self.factory.get(path)
        request.user = self.owner
        response = view(request, owner_username=self.owner.username, dataset_slug=self.dataset.slug, submission_set_name='comments')
        self.assertStatusCode(response, 200)

        data = json.loads(response.rendered_content)
        self.assertNotIn('anonymous_data', data)

    # -------------------------------------------------------------------------
    # Place-specific Submission List View Summaries
    # -------------------------------------------------------------------------

    def test_place_submission_list_with_include_anonymous(self):
        view = SubmissionListView.as_view()
        path = reverse('submission-list', kwargs={
            'owner_username': self.owner.username,
            'dataset_slug': self.dataset.slug,
            'place_id': self.place1.pk,
            'submission_set_name': 'comments'
        })
        request = self.factory.get(path + '?include_anonymous')
        request.user = self.owner
        response = view(request, owner_username=self.owner.username, dataset_slug=self.dataset.slug,
                        place_id=self.place1.pk, submission_set_name='comments')
        self.assertStatusCode(response, 200)

        data = json.loads(response.rendered_content)
        self.assertIn('anonymous_data', data)
        self.assertEqual(data['anonymous_data']['length'], 1)
        # URL must point to dataset-level anonymous endpoint, not place-specific
        self.assertTrue(data['anonymous_data']['url'].endswith('/comments/anonymous'))
        self.assertNotIn(f'/places/{self.place1.pk}/', data['anonymous_data']['url'])

    # -------------------------------------------------------------------------
    # Detail Views Ignore include_anonymous
    # -------------------------------------------------------------------------

    def test_place_detail_ignores_include_anonymous(self):
        view = PlaceInstanceView.as_view()
        path = reverse('place-detail', kwargs={
            'owner_username': self.owner.username,
            'dataset_slug': self.dataset.slug,
            'place_id': self.place1.pk
        })
        request = self.factory.get(path + '?include_anonymous')
        request.user = self.owner
        response = view(request, owner_username=self.owner.username, dataset_slug=self.dataset.slug,
                        place_id=self.place1.pk)
        self.assertStatusCode(response, 200)

        data = json.loads(response.rendered_content)
        self.assertNotIn('anonymous_data', data)
        self.assertNotIn('anonymous_data', data.get('properties', {}))

    def test_submission_detail_ignores_include_anonymous(self):
        view = SubmissionInstanceView.as_view()
        path = reverse('submission-detail', kwargs={
            'owner_username': self.owner.username,
            'dataset_slug': self.dataset.slug,
            'place_id': self.place1.pk,
            'submission_set_name': 'comments',
            'submission_id': self.comment1.pk
        })
        request = self.factory.get(path + '?include_anonymous')
        request.user = self.owner
        response = view(request, owner_username=self.owner.username, dataset_slug=self.dataset.slug,
                        place_id=self.place1.pk, submission_set_name='comments',
                        submission_id=self.comment1.pk)
        self.assertStatusCode(response, 200)

        data = json.loads(response.rendered_content)
        self.assertNotIn('anonymous_data', data)

    # -------------------------------------------------------------------------
    # Permission Enforcement for include_anonymous
    # -------------------------------------------------------------------------

    def test_include_anonymous_unauthenticated_returns_401(self):
        view = PlaceListView.as_view()
        path = reverse('place-list', kwargs={'owner_username': self.owner.username, 'dataset_slug': self.dataset.slug})
        request = self.factory.get(path + '?include_anonymous')
        response = view(request, owner_username=self.owner.username, dataset_slug=self.dataset.slug)
        self.assertStatusCode(response, 401)

    def test_include_anonymous_unauthorized_user_returns_403(self):
        view = PlaceListView.as_view()
        path = reverse('place-list', kwargs={'owner_username': self.owner.username, 'dataset_slug': self.dataset.slug})
        request = self.factory.get(path + '?include_anonymous')
        request.user = self.other_user
        response = view(request, owner_username=self.owner.username, dataset_slug=self.dataset.slug)
        self.assertStatusCode(response, 403)

    def test_include_anonymous_apikey_without_protected_returns_403(self):
        view = PlaceListView.as_view()
        path = reverse('place-list', kwargs={'owner_username': self.owner.username, 'dataset_slug': self.dataset.slug})
        request = self.factory.get(path + '?include_anonymous')
        request.META[KEY_HEADER] = self.public_apikey.key
        response = view(request, owner_username=self.owner.username, dataset_slug=self.dataset.slug)
        self.assertStatusCode(response, 403)

    def test_include_anonymous_apikey_with_protected_returns_200(self):
        view = PlaceListView.as_view()
        path = reverse('place-list', kwargs={'owner_username': self.owner.username, 'dataset_slug': self.dataset.slug})
        request = self.factory.get(path + '?include_anonymous')
        request.META[KEY_HEADER] = self.owner_apikey.key
        response = view(request, owner_username=self.owner.username, dataset_slug=self.dataset.slug)
        self.assertStatusCode(response, 200)

        data = json.loads(response.rendered_content)
        self.assertIn('anonymous_data', data)

    # -------------------------------------------------------------------------
    # Dedicated Anonymous Data Endpoints
    # -------------------------------------------------------------------------

    def test_places_anonymous_endpoint_as_owner(self):
        view = PlaceAnonymousDataListView.as_view()
        path = reverse('place-anonymous-data-list', kwargs={'owner_username': self.owner.username, 'dataset_slug': self.dataset.slug})
        request = self.factory.get(path)
        request.user = self.owner
        response = view(request, owner_username=self.owner.username, dataset_slug=self.dataset.slug)
        self.assertStatusCode(response, 200)

        data = json.loads(response.rendered_content)
        self.assertIn('metadata', data)
        self.assertIn('results', data)
        self.assertEqual(data['metadata']['length'], 2)
        self.assertEqual(len(data['results']), 2)
        # Results are raw JSON objects
        self.assertIn({'age': '25-34', 'race': 'Asian'}, data['results'])
        self.assertIn({'age': '35-44', 'race': 'White'}, data['results'])

    def test_submission_set_anonymous_endpoint_as_owner(self):
        view = SubmissionSetAnonymousDataListView.as_view()
        path = reverse('submission-set-anonymous-data-list', kwargs={
            'owner_username': self.owner.username,
            'dataset_slug': self.dataset.slug,
            'submission_set_name': 'comments'
        })
        request = self.factory.get(path)
        request.user = self.owner
        response = view(request, owner_username=self.owner.username, dataset_slug=self.dataset.slug, submission_set_name='comments')
        self.assertStatusCode(response, 200)

        data = json.loads(response.rendered_content)
        self.assertEqual(data['metadata']['length'], 1)
        self.assertEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0], {'rating': 5, 'sentiment': 'positive'})

    def test_ballots_anonymous_endpoint_with_complex_data(self):
        view = SubmissionSetAnonymousDataListView.as_view()
        path = reverse('submission-set-anonymous-data-list', kwargs={
            'owner_username': self.owner.username,
            'dataset_slug': self.dataset.slug,
            'submission_set_name': 'ballots'
        })
        request = self.factory.get(path)
        request.user = self.owner
        response = view(request, owner_username=self.owner.username, dataset_slug=self.dataset.slug, submission_set_name='ballots')
        self.assertStatusCode(response, 200)

        data = json.loads(response.rendered_content)
        self.assertEqual(data['metadata']['length'], 1)
        self.assertEqual(data['results'][0], {'proposals': ['p1', 'p2']})

    def test_anonymous_endpoint_unauthorized_returns_401_or_403(self):
        view = PlaceAnonymousDataListView.as_view()
        path = reverse('place-anonymous-data-list', kwargs={'owner_username': self.owner.username, 'dataset_slug': self.dataset.slug})

        # Unauthenticated
        request = self.factory.get(path)
        response = view(request, owner_username=self.owner.username, dataset_slug=self.dataset.slug)
        self.assertStatusCode(response, 401)

        # Authenticated without permission
        request = self.factory.get(path)
        request.user = self.other_user
        response = view(request, owner_username=self.owner.username, dataset_slug=self.dataset.slug)
        self.assertStatusCode(response, 403)

        # Public API key without can_access_protected
        request = self.factory.get(path)
        request.META[KEY_HEADER] = self.public_apikey.key
        response = view(request, owner_username=self.owner.username, dataset_slug=self.dataset.slug)
        self.assertStatusCode(response, 403)

    def test_anonymous_endpoint_with_protected_apikey_returns_200(self):
        view = PlaceAnonymousDataListView.as_view()
        path = reverse('place-anonymous-data-list', kwargs={'owner_username': self.owner.username, 'dataset_slug': self.dataset.slug})
        request = self.factory.get(path)
        request.META[KEY_HEADER] = self.owner_apikey.key
        response = view(request, owner_username=self.owner.username, dataset_slug=self.dataset.slug)
        self.assertStatusCode(response, 200)

        data = json.loads(response.rendered_content)
        self.assertEqual(data['metadata']['length'], 2)

    def test_anonymous_endpoint_disallows_post_put_delete(self):
        view = PlaceAnonymousDataListView.as_view()
        path = reverse('place-anonymous-data-list', kwargs={'owner_username': self.owner.username, 'dataset_slug': self.dataset.slug})

        for method in ['post', 'put', 'patch', 'delete']:
            req_fn = getattr(self.factory, method)
            request = req_fn(path, data={'data': {'age': '20'}}, content_type='application/json')
            request.user = self.owner
            response = view(request, owner_username=self.owner.username, dataset_slug=self.dataset.slug)
            self.assertStatusCode(response, 405)

    def test_anonymous_endpoint_empty_dataset(self):
        new_ds = DataSet.objects.create(slug='empty-ds', owner=self.owner)
        view = PlaceAnonymousDataListView.as_view()
        path = reverse('place-anonymous-data-list', kwargs={'owner_username': self.owner.username, 'dataset_slug': new_ds.slug})
        request = self.factory.get(path)
        request.user = self.owner
        response = view(request, owner_username=self.owner.username, dataset_slug=new_ds.slug)
        self.assertStatusCode(response, 200)

        data = json.loads(response.rendered_content)
        self.assertEqual(data['metadata']['length'], 0)
        self.assertEqual(data['results'], [])

    def test_anonymous_endpoint_pagination(self):
        # Create additional anonymous records to test pagination
        for i in range(10):
            AnonymousValues.objects.create(
                dataset=self.dataset, set_name='comments', data={'index': i}
            )

        view = SubmissionSetAnonymousDataListView.as_view()
        path = reverse('submission-set-anonymous-data-list', kwargs={
            'owner_username': self.owner.username,
            'dataset_slug': self.dataset.slug,
            'submission_set_name': 'comments'
        })
        request = self.factory.get(path + '?page_size=5&page=1')
        request.user = self.owner
        response = view(request, owner_username=self.owner.username, dataset_slug=self.dataset.slug, submission_set_name='comments')
        self.assertStatusCode(response, 200)

        data = json.loads(response.rendered_content)
        self.assertEqual(data['metadata']['length'], 11)  # 1 initial + 10 created
        self.assertEqual(data['metadata']['page'], 1)
        self.assertEqual(data['metadata']['num_pages'], 3)
        self.assertEqual(len(data['results']), 5)
        self.assertIsNotNone(data['metadata']['next'])
