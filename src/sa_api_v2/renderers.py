import ujson as json
from django.conf import settings
from rest_framework.renderers import JSONRenderer
from rest_framework_csv.renderers import CSVRenderer
if settings.USE_GEODB:
    from django.contrib.gis.geos import GEOSGeometry


class JSONPRenderer (JSONRenderer):
    """
    (Copied from https://github.com/encode/django-rest-framework/blob/2.4.8/rest_framework/renderers.py)
    Renderer which serializes to json, wrapping the json output in a callback function.
    """

    media_type = 'application/javascript'
    format = 'jsonp'
    callback_parameter = 'callback'
    default_callback = 'callback'
    charset = 'utf-8'

    def get_callback(self, renderer_context):
        """
        Determine the name of the callback to wrap around the json output.
        """
        request = renderer_context.get('request', None)
        params = request and request.query_params or {}
        return params.get(self.callback_parameter, self.default_callback)

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        Renders into jsonp, wrapping the json output in a callback function.
        Clients may set the callback function name using a query parameter
        on the URL, for example: ?callback=exampleCallbackName
        """
        renderer_context = renderer_context or {}
        callback = self.get_callback(renderer_context)
        json = super(JSONPRenderer, self).render(data, accepted_media_type, renderer_context)
        return callback.encode(self.charset) + b'(' + json + b');'


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
    id_field = 'id'

    def render(self, data, media_type=None, renderer_context=None):
        """
        Renders *data* into a GeoJSON feature.
        """
        # Let error codes slip through to the super class method.
        response = (renderer_context or {}).get('response')
        if response and response.status_code >= 400:
            return super(GeoJSONRenderer, self).render(data, media_type, renderer_context)

        # Assume everything else is a successful geometry.
        if isinstance(data, list):
            new_data = {
              'type': 'FeatureCollection',
              'features': [(self.get_feature(elem) or elem) for elem in data]
            }
        elif isinstance(data, dict) and data.get('type') == 'FeatureCollection':
            new_data = data.copy()
            new_data['features'] = [(self.get_feature(elem) or elem) for elem in data['features']]
        elif data is None:
            new_data = None
        else:
            new_data = self.get_feature(data) or data

        return super(GeoJSONRenderer, self).render(new_data, media_type, renderer_context)

    def get_feature(self, data):
        if 'geometry' not in data:
            return None

        feature_props = data.copy()
        geometry = feature_props.pop(self.geometry_field)
        feature_id = feature_props.get(self.id_field)  # Should this be popped?

        if isinstance(geometry, str):
            geometry = json.loads(GEOSGeometry(geometry).json)
        elif isinstance(geometry, GEOSGeometry):
            geometry = json.loads(geometry.json)

        feature = {
          'type': 'Feature',
          'geometry': geometry,
          'properties': feature_props,
        }

        if feature_id is not None:
            feature['id'] = feature_id

        return feature


class GeoJSONPRenderer(JSONPRenderer, GeoJSONRenderer):
    """
    Renderer which serializes to geojson,
    wrapping the json output in a callback function.

    (JSONPRenderer will call GeoJSONRenderer before JSONRenderer)
    """
    pass


class NullJSONRenderer(JSONRenderer):
    """
    Renderer JSON with a simple None value as null
    """
    def render(self, data, media_type=None, renderer_context=None):
        if data is None:
            return bytes('null'.encode('utf-8'))
        return super(NullJSONRenderer, self).render(data, media_type, renderer_context)


class NullJSONPRenderer(JSONPRenderer, NullJSONRenderer):
    """
    (JSONPRenderer will call NullJSONRenderer before JSONRenderer)
    """
    pass