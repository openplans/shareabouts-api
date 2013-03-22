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
      }),

      vizLayers = [],

      $visualization = $('select[name="visualization_type"]'),
      $variable = $('select[name="variable"]');

  function getValueFunction(varType, varParam) {
    switch (varType) {
      case 'identity':
        return function() { return 1; };

      case 'submission_count':
        var name = varParam;
        return function(place) {
          var submissionSet = _.findWhere(place.submissions, {'type': name});
          if (submissionSet) {
            return submissionSet.length;
          } else {
            return 0;
          }
        };

      default:
        return null;
    }
  }

  function getScaleLayer(data, options) {
    var maxRadius = 25,
        minRadius = 3,
        defaultRadius = 5,
        circleLayers, max, min, diff, layerData;

    layerData = _.map(data, function(place) {
      return { place: place, latLng: [place.location.lat, place.location.lng], val: options.valueFn(place)};
    });

    max = _.max(layerData, function(d) { return d.val; }).val;
    min = _.min(layerData, function(d) { return d.val; }).val;
    diff = max - min;

    circleLayers = _.map(layerData, function(d) {
      var marker, radius;
      if (diff > 0) {
        radius = ((d.val - min) / diff) * (maxRadius - minRadius) + minRadius;
      } else {
        radius = defaultRadius;
      }

      marker = L.circleMarker(d.latLng, {
        radius: radius,
        fillOpacity: 0.4,
        stroke: false,
        color: '#ff5c00'
      });

      marker.bindPopup('<a href="../places/'+d.place.id+'" target="_blank">' + d.place.id + '</a>');

      return marker;
    });

    return L.layerGroup(circleLayers);
  }

  function getLayer(vizType, data, options) {
    switch (vizType) {
      case 'heatmap':
        return S.heatmap(data, options).layer;
      case 'scale':
        return getScaleLayer(data, options);
      default:
        return null;
    }
  }

  function getPlaceBounds(data) {
    var points = _.map(data, function(place) { return [place.location.lat, place.location.lng]; }),
        bounds = new L.LatLngBounds(points);
    return bounds;
  }

  function updateMap(data) {
    var options,
        layer;

    // First, clear the map
    _.each(vizLayers, function(layer) {
      map.removeLayer(layer);
    });
    vizLayers = [];

    // Get your variable function (assuming single-variate viz)
    options = {
      valueFn: getValueFunction($variable.find(':selected').attr('data-variable-type'),
                                $variable.find(':selected').attr('data-variable-param'))
    };

    // Draw your visualization
    layer = getLayer($visualization.find(':selected').val(), data, options);
    vizLayers.push(layer);
    map.addLayer(layer);
  }

  function initVariableOptions(data) {
    // Get all the unique submission set names
    var submissionSetNames = [];
    _.each(data, function(place, i) {
      _.each(place.submissions, function(submission_set, i) {
        submissionSetNames.push(submission_set.type);
      });
    });
    submissionSetNames = _.uniq(submissionSetNames);

    // Populate submission count variables
    _.each(submissionSetNames, function(name) {
      $variable.append('<option '+
                           'data-variable-type="submission_count" '+
                           'data-variable-param="' + name + '" '+
                           'value="' + name + '_count">Number of ' + name + '</option>');
    });
  }

  $(function() {
    initVariableOptions(S.placesData);
    map.fitBounds(getPlaceBounds(S.placesData));

    $variable.change(function() {
      updateMap(S.placesData);
    });

    $visualization.change(function() {
      updateMap(S.placesData);
    });

    updateMap(S.placesData);
  });

}(Shareabouts, jQuery));
