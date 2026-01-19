from django.test import TestCase
from django.test.client import RequestFactory
from django.urls import reverse
from django.conf import settings
from sa_api_v2.models import User, DataSet, Place
from sa_api_v2.views import PlaceListView
import json

class APITestMixin(object):
    def assertStatusCode(self, response, *expected):
        self.assertIn(response.status_code, expected,
            'Status code not in %s response: (%s) %s' %
            (expected, response.status_code, response.rendered_content))

class TestSpatialViews(APITestMixin, TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='aaron', password='123', email='abc@example.com')
        self.dataset = DataSet.objects.create(slug='ds', owner=self.owner)
        self.factory = RequestFactory()

        # Create base path for place list
        self.request_kwargs = {
            'owner_username': self.owner.username,
            'dataset_slug': self.dataset.slug
        }
        self.path = reverse('place-list', kwargs=self.request_kwargs)
        self.view = PlaceListView.as_view()

        # Create some places at specific coordinates
        # (0,0), (10,0), (20,0), (30,0)
        self.p1 = Place.objects.create(dataset=self.dataset, geometry='POINT(0 0)', data=json.dumps({'name': 1}))
        self.p2 = Place.objects.create(dataset=self.dataset, geometry='POINT(10 0)', data=json.dumps({'name': 2}))
        self.p3 = Place.objects.create(dataset=self.dataset, geometry='POINT(20 0)', data=json.dumps({'name': 3}))
        self.p4 = Place.objects.create(dataset=self.dataset, geometry='POINT(30 0)', data=json.dumps({'name': 4}))

    def test_GET_near_valid(self):
        """GET with valid 'near' param should sort by distance."""
        # Request near (0, 0)
        request = self.factory.get(self.path + '?near=0,0')
        response = self.view(request, **self.request_kwargs)

        self.assertStatusCode(response, 200)
        data = json.loads(response.rendered_content)

        # Should be ordered 1, 2, 3, 4
        self.assertEqual(len(data['features']), 4)
        names = [f['properties']['name'] for f in data['features']]
        self.assertEqual(names, [1, 2, 3, 4])

        # Request near (30, 0). to_geom expects "lat, lng".
        # So we pass "0, 30" (Lat 0, Lon 30).
        request = self.factory.get(self.path + '?near=0,30')
        response = self.view(request, **self.request_kwargs)

        self.assertStatusCode(response, 200)
        data = json.loads(response.rendered_content)

        # Should be ordered 4, 3, 2, 1
        names = [f['properties']['name'] for f in data['features']]
        self.assertEqual(names, [4, 3, 2, 1])

    def test_GET_near_invalid(self):
        """GET with invalid 'near' param should return 400."""
        # Invalid format (not enough coords)
        request = self.factory.get(self.path + '?near=0')
        response = self.view(request, **self.request_kwargs)
        self.assertStatusCode(response, 400)

        # Invalid format (non-numeric)
        request = self.factory.get(self.path + '?near=foo,bar')
        response = self.view(request, **self.request_kwargs)
        self.assertStatusCode(response, 400)

    def test_GET_bbox_valid(self):
        """GET with valid 'bbox' param should filter places."""
        # Approx bounding box around (9, -1) to (21, 1) -> Should catch 2 (10,0) and 3 (20,0)
        # Bbox format: min_lon,min_lat,max_lon,max_lat
        request = self.factory.get(self.path + '?bounds=9,-1,21,1')
        response = self.view(request, **self.request_kwargs)

        self.assertStatusCode(response, 200)
        data = json.loads(response.rendered_content)

        self.assertEqual(len(data['features']), 2)
        names = sorted([f['properties']['name'] for f in data['features']])
        self.assertEqual(names, [2, 3])

    def test_GET_bbox_invalid(self):
        """GET with invalid 'bounds' param should return 400."""
        # Not enough coords
        request = self.factory.get(self.path + '?bounds=0,0,10')
        response = self.view(request, **self.request_kwargs)
        self.assertStatusCode(response, 400)

        # Non-numeric
        request = self.factory.get(self.path + '?bounds=a,b,c,d')
        response = self.view(request, **self.request_kwargs)
        self.assertStatusCode(response, 400)

    def test_GET_distance_valid(self):
        """GET with 'distance' param should filter results by distance from 'near'."""
        # Near (0,0), distance 1500km.
        # Places at 0 degrees (0km) and 10 degrees (~1111km).
        # Place at 20 degrees (~2222km) should be excluded.
        request = self.factory.get(self.path + '?near=0,0&distance_lt=1500km')
        response = self.view(request, **self.request_kwargs)

        self.assertStatusCode(response, 200)
        data = json.loads(response.rendered_content)

        names = sorted([f['properties']['name'] for f in data['features']])
        # Should include 1 (0,0) and 2 (10,0)
        self.assertEqual(names, [1, 2])

    def test_GET_distance_missing_near(self):
        """GET with 'distance' but missing 'near' should return 400."""
        request = self.factory.get(self.path + '?distance_lt=10')
        response = self.view(request, **self.request_kwargs)
        # The view raises QueryError, which usually maps to 400.
        self.assertStatusCode(response, 400)

    def test_GET_distance_invalid(self):
        """GET with invalid 'distance' param should return 400."""
        request = self.factory.get(self.path + '?near=0,0&distance_lt=invalid')
        response = self.view(request, **self.request_kwargs)
        self.assertStatusCode(response, 400)
