{% extends "gis/admin/openlayers.js" %}
{% block base_layer %}new OpenLayers.Layer.OSM("OpenStreetMap (Mapnik)",
      // Official OSM tileset over https
      [
        'https://a.tile.openstreetmap.org/${z}/${x}/${y}.png',
        'https://b.tile.openstreetmap.org/${z}/${x}/${y}.png',
        'https://c.tile.openstreetmap.org/${z}/${x}/${y}.png'
      ]);{% endblock %}
