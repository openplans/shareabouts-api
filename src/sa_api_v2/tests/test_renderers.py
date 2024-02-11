from django.test import TestCase
from sa_api_v2.renderers import GeoJSONRenderer


class TestGeoJSONRenderer (TestCase):
    def test_no_data(self):
        renderer = GeoJSONRenderer()
        data = None

        result = renderer.render(data)
        self.assertEqual(result, b'')
