(function($) {
  $(function(){
    // Get lat from the form input as a float
    var getLat = function() {
      return parseFloat($lat.val());
    };

    // Get lng from the form input as a float
    var getLng = function() {
      return parseFloat($lng.val());
    };

    var $lat = $('[name="lat"]'),
        $lng = $('[name="lng"]'),

        // Map objects
        url = 'http://{s}.tiles.mapbox.com/v3/openplans.map-dmar86ym/{z}/{x}/{y}.png',
        attribution = '&copy; OpenStreetMap contributors, CC-BY-SA. <a href="http://mapbox.com/about/maps" target="_blank">Terms &amp; Feedback</a>',
        base =  L.tileLayer(url, {attribution: attribution}),
        marker = L.marker([getLat(), getLng()], {draggable: true}),

        // Map setup
        map = L.map('place-map', {
          center: [getLat(), getLng()],
          zoom: 16,
          layers: [base, marker],
          maxZoom: 17
        });

    // Update the form inputs on marker drag
    marker.on('drag', function(evt) {
      var latLng = evt.target.getLatLng();
      $lat.val(latLng.lat);
      $lng.val(latLng.lng);
    });

    // Update the map on form input change (where input event is supported)
    $('[name="lat"], [name="lng"]').on('input', function(){
      var lat = getLat(),
          lng = getLng();

      if (lat && lng) {
        marker.setLatLng([lat, lng]);
      }
    });
  });
})(jQuery);
