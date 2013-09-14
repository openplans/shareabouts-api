import json
from rest_framework.renderers import JSONRenderer
from rest_framework_csv.renderers import CSVRenderer
from django.contrib.gis.geos import GEOSGeometry


class PaginatedCSVRenderer (CSVRenderer):
    def render(self, data, media_type=None, renderer_context=None):
        if not isinstance(data, list):
            data = data.get('results') or data.get('features')
        return super(PaginatedCSVRenderer, self).render(data, media_type, renderer_context)


class GeoJSONRenderer(JSONRenderer):
    """
    Renderer which serializes to GeoJSON
    """

    media_type = 'application/json'
    format = 'json'
    geometry_field = 'geometry'

    def render(self, data, media_type=None, renderer_context=None):
        """
        Renders *data* into a GeoJSON feature.
        """
        if isinstance(data, list):
            new_data = {
              'type': 'FeatureCollection',
              'features': [(self.get_feature(elem) or elem) for elem in data]
            }
        elif isinstance(data, dict) and data.get('type') == 'FeatureCollection':
            new_data = data
            new_data['features'] = [(self.get_feature(elem) or elem) for elem in data['features']]
        elif data is None:
            new_data = None
        else:
            new_data = self.get_feature(data) or data

        return super(GeoJSONRenderer, self).render(new_data, media_type, renderer_context)

    def get_feature(self, data):
        if 'geometry' not in data:
            return None

        geometry = data.pop(self.geometry_field)

        if isinstance(geometry, basestring):
            geometry = json.loads(GEOSGeometry(geometry).json)

        feature = {
          'type': 'Feature',
          'geometry': geometry,
          'properties': data,
        }

        return feature
