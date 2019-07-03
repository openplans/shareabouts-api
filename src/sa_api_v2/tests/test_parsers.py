import json
from io import BytesIO
from django.test import TestCase
from sa_api_v2.parsers import GeoJSONParser


class TestGeoJSONParser (TestCase):
    def test_should_extract_properties(self):
        geojson = json.dumps({
            'type': 'Feature',
            'geometry': { "type": "Point", "coordinates": [100.0, 0.0] },
            'properties': {
                'name': 'Mjumbe',
                'age': 29
            }
        })

        parser = GeoJSONParser()
        data = parser.parse(BytesIO(geojson.encode()), 'application/json', {})

        self.assertNotIn('type', data)
        self.assertNotIn('properties', data)
        self.assertIn('name', data)
        self.assertIn('age', data)
        self.assertIn('geometry', data)
