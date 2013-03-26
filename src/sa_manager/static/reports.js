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
      $variable = $('select[name="variable"]'),
      $minValue = $('input[name="min_value"]'),

      allValues = [];

  function getValueFunction(varType, varParam) {
    switch (varType) {

      // Simple presence of a place
      case 'identity':
        return function() { return 1; };

      // Number of submissions in a given submission set
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

      // Number of attachments on a place
      case 'attachment_count':
        return function(place) {
          return place.attachments.length;
        }

      // Value of a place's attribute
      case 'attribute_value':
        var attr = varParam;
        return function(place) {
          return place[attr] || 0;
        }

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

  function resetMinValueSlider(data) {
    var valueFn = getValueFunction($variable.find(':selected').attr('data-variable-type'),
                                   $variable.find(':selected').attr('data-variable-param'));

    allValues = _.map(data, valueFn);
    allValues = _.filter(allValues, _.isNumber)
    allValues = _.uniq(allValues.sort(function(a,b){return a-b}), true);

    $minValue.attr('max', allValues.length - 1);
    $minValue.attr('value', 0);

    updateMinValueLabel();
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

    data = _.filter(data, function(d) { return options.valueFn(d) >= allValues[$minValue.val()]; });

    // Draw your visualization
    layer = getLayer($visualization.find(':selected').val(), data, options);
    vizLayers.push(layer);
    map.addLayer(layer);
  }

  function updateMinValueLabel() {
    $('.min-value label').text('Min value: ' + allValues[$minValue.val()]);
  }

  function _allKeys(data) {
    var tempObject = {};

    _.each(data, function(obj) {
      tempObject = _.extend(tempObject, obj);
    });

    return _.keys(tempObject);
  }

  function initVariableOptions(data) {
    var submissionSetNames = [],
        placeAttributes = [];

    // Get all the unique submission set names
    _.each(data, function(place, i) {
      submissionSetNames = submissionSetNames.concat(_.pluck(place.submissions, 'type'));
    });
    submissionSetNames = _.uniq(submissionSetNames);

    // Populate submission count variables
    _.each(submissionSetNames, function(name) {
      $variable.append('<option '+
                           'data-variable-type="submission_count" '+
                           'data-variable-param="' + name + '" '+
                           'value="' + name + '_count">Number of ' + name + '</option>');
    });

    // Add number of attachments variable
    $variable.append('<option '+
                         'data-variable-type="attachment_count" '+
                         'data-variable-param="" '+
                         'value="attachment_count">Number of attachments</option>');

    // Get all the unique attributes
    placeAttributes = _allKeys(data)
    placeAttributes = _.without(placeAttributes, 'attachments', 'updated_datetime', 'created_datetime', 'id', 'dataset', 'visible', 'location', 'url', 'submissions')

    // Populate the values
    _.each(placeAttributes, function(attr) {
      $variable.append('<option '+
                           'data-variable-type="attribute_value" '+
                           'data-variable-param="' + attr + '" '+
                           'value="' + attr + '_value">Value of ' + attr + '</option>');
    });
  }

  $(function() {
    initVariableOptions(S.placesData);
    map.fitBounds(getPlaceBounds(S.placesData));

    $variable.change(function() {
      resetMinValueSlider(S.placesData);
      updateMap(S.placesData);
    });

    $visualization.change(function() {
      updateMap(S.placesData);
    });

    $minValue.change(function() {
      updateMinValueLabel();
      updateMap(S.placesData);
    });

    resetMinValueSlider(S.placesData);
    updateMap(S.placesData);
  });

}(Shareabouts, jQuery));
