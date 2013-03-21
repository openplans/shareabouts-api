/*global Shareabouts _ L jQuery*/

(function(S, $) {
  'use strict';

  var // Map objects
      url = 'http://{s}.tiles.mapbox.com/v3/openplans.map-dmar86ym/{z}/{x}/{y}.png',
      attribution = '&copy; OpenStreetMap contributors, CC-BY-SA. <a href="http://mapbox.com/about/maps" target="_blank">Terms &amp; Feedback</a>',
      base =  L.tileLayer(url, {attribution: attribution}),

      // Map setup
      map = L.map('report-map', {
        center: [0, 0],
        zoom: 2,
        layers: [base],
        maxZoom: 17
      });

  function initMap(data) {
    var _heatmap = S.heatmap(data, {
      resizeCanvas: false,
      bgcolor: [0, 0, 0, 0],
      bufferPixels: 100,
      step: 0.05,
      colorscheme: function(value){
        var h = (1 - value);
        var l = 0.5;
        var s = 1;
        var a = value + 0.03;
        return [h, s, l, a];
      }
    });

    map.addLayer(_heatmap.layer);
    map.fitBounds(_heatmap.layer._bounds);
  }

  $(function() {
    initMap(S.placesData);
  });

}(Shareabouts, jQuery));
