import json
from django.test import TestCase
from django.test.client import RequestFactory
from django.urls import reverse
from django.core.cache import cache as django_cache
from unittest import mock

from ..models import User, DataSet, Place, DataSnapshotRequest, DataSnapshot
from ..cache import cache_buffer
from ..apikey.models import ApiKey
from ..views import DataSnapshotRequestListView, DataSnapshotInstanceView


class TestDataSnapshotRequestListView(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='owner', password='123', email='owner@example.com')
        self.dataset = DataSet.objects.create(slug='test-dataset', owner=self.owner)
        self.apikey = ApiKey.objects.create(key='abc123', dataset=self.dataset)

        self.factory = RequestFactory()
        self.request_kwargs = {
            'owner_username': self.owner.username,
            'dataset_slug': self.dataset.slug,
            'submission_set_name': 'places'
        }
        self.path = reverse('dataset-snapshot-list', kwargs=self.request_kwargs)
        self.view = DataSnapshotRequestListView.as_view()

        cache_buffer.reset()
        django_cache.clear()

    def tearDown(self):
        User.objects.all().delete()
        DataSet.objects.all().delete()
        DataSnapshotRequest.objects.all().delete()
        ApiKey.objects.all().delete()

        cache_buffer.reset()
        django_cache.clear()

    def test_GET_empty_list(self):
        """GET should return empty list when no snapshots exist."""
        request = self.factory.get(self.path)
        request.user = self.owner
        response = self.view(request, **self.request_kwargs)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    def test_GET_with_existing_snapshots(self):
        """GET should return list of existing snapshots."""
        # Create a snapshot request
        snapshot = DataSnapshotRequest.objects.create(
            dataset=self.dataset,
            submission_set='places',
            status='success',
            guid='test-guid-123'
        )

        request = self.factory.get(self.path)
        request.user = self.owner
        response = self.view(request, **self.request_kwargs)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['status'], 'success')

    @mock.patch('sa_api_v2.views.bulk_data_views.store_bulk_data')
    def test_POST_creates_snapshot_request(self, mock_store):
        """POST should create a new snapshot request."""
        # Mock the celery task
        mock_task = mock.MagicMock()
        mock_task.id = 'mock-task-id'
        mock_store.apply_async.return_value = mock_task

        request = self.factory.post(self.path)
        request.user = self.owner
        response = self.view(request, **self.request_kwargs)

        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.data['status'], 'pending')
        self.assertIn('url', response.data)

        # Verify the celery task was called
        mock_store.apply_async.assert_called_once()

    @mock.patch('sa_api_v2.views.bulk_data_views.store_bulk_data')
    def test_POST_returns_existing_pending_request(self, mock_store):
        """POST should return existing pending request instead of creating duplicate."""
        # Create an existing pending request
        existing = DataSnapshotRequest.objects.create(
            dataset=self.dataset,
            submission_set='places',
            status='pending',
            guid='existing-guid'
        )

        request = self.factory.post(self.path)
        request.user = self.owner
        response = self.view(request, **self.request_kwargs)

        self.assertEqual(response.status_code, 202)
        # Should not have called the task since we're returning existing
        mock_store.apply_async.assert_not_called()

    @mock.patch('sa_api_v2.views.bulk_data_views.store_bulk_data')
    def test_GET_with_new_param_creates_request(self, mock_store):
        """GET with ?new parameter should create a new snapshot request."""
        mock_task = mock.MagicMock()
        mock_task.id = 'mock-task-id'
        mock_store.apply_async.return_value = mock_task

        request = self.factory.get(self.path + '?new=true')
        request.user = self.owner
        response = self.view(request, **self.request_kwargs)

        self.assertEqual(response.status_code, 202)
        mock_store.apply_async.assert_called_once()


class TestDataSnapshotInstanceView(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='owner', password='123', email='owner@example.com')
        self.dataset = DataSet.objects.create(slug='test-dataset', owner=self.owner)
        self.apikey = ApiKey.objects.create(key='abc123', dataset=self.dataset)

        # Create a fulfilled snapshot request
        self.snapshot_request = DataSnapshotRequest.objects.create(
            dataset=self.dataset,
            submission_set='places',
            status='success',
            guid='test-guid-123'
        )
        self.snapshot = DataSnapshot.objects.create(
            request=self.snapshot_request,
            json='{"type": "FeatureCollection", "features": []}',
            csv='id,name\n1,Test'
        )

        self.factory = RequestFactory()
        self.request_kwargs = {
            'owner_username': self.owner.username,
            'dataset_slug': self.dataset.slug,
            'submission_set_name': 'places',
            'data_guid': 'test-guid-123'
        }
        self.path = reverse('dataset-snapshot-instance', kwargs=self.request_kwargs)
        self.view = DataSnapshotInstanceView.as_view()

        cache_buffer.reset()
        django_cache.clear()

    def tearDown(self):
        User.objects.all().delete()
        DataSet.objects.all().delete()
        DataSnapshotRequest.objects.all().delete()
        DataSnapshot.objects.all().delete()
        ApiKey.objects.all().delete()

        cache_buffer.reset()
        django_cache.clear()

    def test_GET_snapshot_json(self):
        """GET should return snapshot data as JSON."""
        request = self.factory.get(self.path)
        request.user = self.owner
        response = self.view(request, **self.request_kwargs)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_GET_snapshot_csv(self):
        """GET with format=csv should return CSV data."""
        request_kwargs = self.request_kwargs.copy()
        request_kwargs['format'] = 'csv'
        # Append format manually since reverse with optional group is tricky
        path = f"{self.path}.csv"

        request = self.factory.get(path)
        request.user = self.owner
        response = self.view(request, **request_kwargs)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')

    def test_GET_snapshot_geojson(self):
        """GET with format=geojson should return GeoJSON data."""
        request_kwargs = self.request_kwargs.copy()
        request_kwargs['format'] = 'geojson'

        # Append format manually since reverse with optional group is tricky
        path = f"{self.path}.geojson"

        request = self.factory.get(path)
        request.user = self.owner
        response = self.view(request, **request_kwargs)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_GET_invalid_format(self):
        """GET with invalid format should return 404."""
        request_kwargs = self.request_kwargs.copy()
        request_kwargs['format'] = 'invalid'

        # Append format manually
        path = f"{self.path}.invalid"

        request = self.factory.get(path)
        request.user = self.owner
        response = self.view(request, **request_kwargs)

        self.assertEqual(response.status_code, 404)

    def test_GET_nonexistent_snapshot(self):
        """GET for non-existent snapshot should return 404."""
        request_kwargs = self.request_kwargs.copy()
        request_kwargs['data_guid'] = 'nonexistent-guid'
        request = self.factory.get(self.path)
        request.user = self.owner
        response = self.view(request, **request_kwargs)

        self.assertEqual(response.status_code, 404)

    def test_GET_pending_snapshot(self):
        """GET for pending snapshot should return 503."""
        # Create a pending request without fulfillment
        pending_request = DataSnapshotRequest.objects.create(
            dataset=self.dataset,
            submission_set='places',
            status='pending',
            guid='pending-guid'
        )

        request_kwargs = self.request_kwargs.copy()
        request_kwargs['data_guid'] = 'pending-guid'
        request = self.factory.get(self.path)
        request.user = self.owner
        response = self.view(request, **request_kwargs)

        self.assertEqual(response.status_code, 503)

    def test_GET_failed_snapshot(self):
        """GET for failed snapshot should return 404."""
        failed_request = DataSnapshotRequest.objects.create(
            dataset=self.dataset,
            submission_set='places',
            status='failure',
            guid='failed-guid'
        )

        request_kwargs = self.request_kwargs.copy()
        request_kwargs['data_guid'] = 'failed-guid'
        request = self.factory.get(self.path)
        request.user = self.owner
        response = self.view(request, **request_kwargs)

        self.assertEqual(response.status_code, 404)

    def test_DELETE_snapshot(self):
        """DELETE should remove the snapshot."""
        from ..apikey.auth import KEY_HEADER
        request = self.factory.delete(self.path)
        request.META[KEY_HEADER] = self.apikey.key
        response = self.view(request, **self.request_kwargs)

        self.assertEqual(response.status_code, 204)
        self.assertFalse(DataSnapshotRequest.objects.filter(guid='test-guid-123').exists())

    def test_DELETE_nonexistent_snapshot(self):
        """DELETE for non-existent snapshot should return 404."""
        from ..apikey.auth import KEY_HEADER
        request_kwargs = self.request_kwargs.copy()
        request_kwargs['data_guid'] = 'nonexistent-guid'
        request = self.factory.delete(self.path)
        request.META[KEY_HEADER] = self.apikey.key
        response = self.view(request, **request_kwargs)

        self.assertEqual(response.status_code, 404)
