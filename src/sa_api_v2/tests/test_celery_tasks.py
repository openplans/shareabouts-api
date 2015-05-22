from django.test import TestCase
from ..models import DataSet, User
from ..tasks import load_dataset_archive
from mock import patch

from .. import tasks


class BulkDataLoadTests (TestCase):
    def setUp(self):
        self.ds = DataSet.objects.create(
            owner=User.objects.create(username='newuser'),
            slug='newdataset',
        )

    def tearDown(self):
        User.objects.all().delete()

    def test_loads_with_no_submission_sets(self):
        class StubResponse:
            status_code = 200

            @staticmethod
            def json():
                return {
                    'type': 'FeatureCollection',
                    'features': [
                        {
                            'type': 'Feature',
                            'geometry': {'type': 'Point', 'coordinates': [1, 2]},
                            'properties': {
                                'p1': 'red',
                                'p2': 'blue',
                            }
                        },
                        {
                            'type': 'Feature',
                            'geometry': {'type': 'Point', 'coordinates': [1, 2]},
                            'properties': {
                                'p1': 'green',
                                'p2': 'orange',
                            }
                        }
                    ]
                }

        with patch.object(tasks.requests, 'get', lambda *a, **k: StubResponse()):
            load_dataset_archive(self.ds.id, 'http://www.example.com/')

        ds = DataSet.objects.get(id=self.ds.id)
        self.assertEqual(ds.places.count(), 2)
