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

      $variable = $('select[name="variable"]');
      S.$variable = $('select[name="variable"]');

  function getValueFunction(varType, varParam) {
    switch (varType) {
      case 'identity':
        return null;

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

  function getPlaceBounds(data) {
    var points = _.map(data, function(place) { return [place.location.lat, place.location.lng]; }),
        bounds = new L.LatLngBounds(points);
    return bounds;
  }

  function updateMap(data) {
    var options,
        _heatmap;

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
    _heatmap = S.heatmap(data, options);
    vizLayers.push(_heatmap.layer)

    map.addLayer(_heatmap.layer);
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

//    updateMap(S.placesData);

    $variable.change(function() {
      updateMap(S.placesData);
    });
  });

}(Shareabouts, jQuery));
