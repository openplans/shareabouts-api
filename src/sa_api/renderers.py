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
        geometry = data.pop(self.geometry_field)
        
        if isinstance(geometry, basestring):
            geometry = GEOSGeometry(geometry)
            
        new_data = {
          'type': 'Feature',
          'geometry': geometry.json,
          'properties': data,
        }
        
        return super(GeoJSONRenderer, self).render(new_data, media_type, renderer_context)

