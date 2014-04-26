from rest_framework.parsers import JSONParser, ParseError
from .renderers import GeoJSONRenderer


class GeoJSONParser (JSONParser):
    renderer_class = GeoJSONRenderer

    def parse(self, stream, media_type, parser_context):
        data = super(GeoJSONParser, self).parse(stream, media_type, parser_context)

        if isinstance(data, dict):
            data = self.process_object(data)
        elif isinstance(data, list):
            data = self.process_array(data)

        return data

    def process_array(self, data):
        return [self.process_object(obj) for obj in data]

    def process_object(self, data):
        try:
            obj_type = data['type']
        except KeyError:
            raise ParseError('GeoJSON parse error - No "type" found in %s' % (data,))

        valid_types = ('Point', 'LineString', 'Polygon', 'MultiPoint', 'MultiLineString', 'MultiPolygon', 'GeometryCollection', 'Feature', 'FeatureCollection')
        if obj_type not in valid_types:
            raise ParseError('GeoJSON parse error - %r is not a valid object type: only %s' % (obj_type, ', '.join(valid_types)))

        if obj_type == 'Feature':
            data = self.process_feature(data)
        elif obj_type == 'FeatureCollection':
            data = self.process_array(data.get('features', []))

        return data

    def process_feature(self, data):
        del data['type']
        properties = data.pop('properties', None)

        if not isinstance(properties, dict):
            raise ParseError('GeoJSON parse error - Feature "properties" must be an object (dict) not %s - %s' % (type(data), data))

        data.update(properties)
        return data
