import json
from rest_framework.renderers import JSONRenderer
from django.contrib.gis.geos import GEOSGeometry

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
        else:
            new_data = self.get_feature(data) or data

        return super(GeoJSONRenderer, self).render(new_data, media_type, renderer_context)

    def get_feature(self, data):
        if 'geometry' not in data:
            return None

        geometry = data.pop(self.geometry_field)

        if isinstance(geometry, basestring):
            geometry = GEOSGeometry(geometry)

        feature = {
          'type': 'Feature',
          'geometry': geometry.json,
          'properties': data,
        }

        return feature
