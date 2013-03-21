/*
 * L.ImageOverlay.Canvas is used to overlay HTML5 canvases over the map (to specific geographical bounds).
 */

L.ImageOverlay.Canvas = L.ImageOverlay.extend({
  options: {
    opacity: 1,
    // Should the pixel of the canvas resize on reset? If false, the CSS width
    // and height change but not the canvas pixel content. If true, then the
    // canvas is also resized and new data will need to be provided.
    resizeCanvas: false
  },

  initialize: function (bounds, options) { // (LatLngBounds, Object)
    this._bounds = L.latLngBounds(bounds);

    L.setOptions(this, options);
  },

  _initImage: function () {
    var topLeft = this._map.latLngToLayerPoint(this._bounds.getNorthWest()),
        size = this._map.latLngToLayerPoint(this._bounds.getSouthEast())._subtract(topLeft);

    // Publicly accessible canvas to draw on.
    this.canvas = this._image = L.DomUtil.create('canvas', 'leaflet-image-layer');
    this.canvas.width  = size.x;
    this.canvas.height = size.y;

    if (this._map.options.zoomAnimation && L.Browser.any3d) {
      L.DomUtil.addClass(this.canvas, 'leaflet-zoom-animated');
    } else {
      L.DomUtil.addClass(this.canvas, 'leaflet-zoom-hide');
    }

    this._updateOpacity();

    L.extend(this.canvas, {
      galleryimg: 'no',
      onselectstart: L.Util.falseFn,
      onmousemove: L.Util.falseFn,
      onload: L.bind(this._onImageLoad, this)
    });
  },

  _reset: function () {
    var topLeft = this._map.latLngToLayerPoint(this._bounds.getNorthWest()),
        size = this._map.latLngToLayerPoint(this._bounds.getSouthEast())._subtract(topLeft);

    L.DomUtil.setPosition(this.canvas, topLeft);

    if (this.options.resizeCanvas) {
      this.canvas.width  = size.x;
      this.canvas.height = size.y;
    }

    this.canvas.style.width  = size.x + 'px';
    this.canvas.style.height = size.y + 'px';

    // This layer has updated itself per the map's viewreset event. Update
    // the canvas if you need to.
    this.fire('viewreset');
  }
});

L.imageOverlay.canvas = function (bounds, options) {
  return new L.ImageOverlay.Canvas(bounds, options);
};
/*global L HeatCanvas */

/*
 * L.ImageOverlay.Canvas is used to overlay HTML5 canvases over the map (to specific geographical bounds).
 */

L.ImageOverlay.HeatCanvas = L.ImageOverlay.Canvas.extend({
  options: {
    step: 1,
    degree: HeatCanvas.LINEAR,
    opacity: 1,
    colorscheme: null,
    resizeCanvas: true,
    bufferPixels: 0
  },

  initialize: function (data, options) { // ([[latLng, value], ...], Object)
    L.setOptions(this, options);

    this.setData(data);
  },

  setData: function(data) {
    var i, len, nePoint, swPoint;

    this._data = data;

    if (this.canvas) {
      this._updateBounds();
      this._reset();
    }
  },

  _updateBounds: function() {
    var i, len, nePoint, swPoint;

    this._bounds = L.latLngBounds([this._data[0][0], this._data[0][0]]);

    for (i=1, len=this._data.length; i<len; i++) {
      this._bounds.extend(this._data[i][0]);
    }

    if (this.options.bufferPixels) {
      nePoint = this._map.project(this._bounds.getNorthEast());
      swPoint = this._map.project(this._bounds.getSouthWest());

      this._bounds.extend(this._map.unproject([nePoint.x + this.options.bufferPixels,
                                               nePoint.y - this.options.bufferPixels]));
      this._bounds.extend(this._map.unproject([swPoint.x - this.options.bufferPixels,
                                               swPoint.y + this.options.bufferPixels]));
    }
  },

  _initImage: function () {
    this._updateBounds();

    L.ImageOverlay.Canvas.prototype._initImage.call(this);

    //this.canvas is a thing
    this.heatCanvas = new HeatCanvas(this.canvas);
    this.heatCanvas.bgcolor = this.options.bgcolor;
  },

  _reset: function () {
    L.ImageOverlay.Canvas.prototype._reset.call(this);

    var topLeft = this._map.latLngToLayerPoint(this._bounds.getNorthWest()),
        size = this._map.latLngToLayerPoint(this._bounds.getSouthEast())._subtract(topLeft),
        i, len, pixel;

    // Update the bounds on view reset since pixel buffers are very different
    // at different zoom levels
    this._updateBounds();
    // Be sure to update the size properties for heatcanvas.js
    this.heatCanvas.resize(size.x, size.y);

    this.heatCanvas.clear();
    for (i=0, len=this._data.length; i<len; i++) {
      pixel = this._map.latLngToLayerPoint(this._data[i][0]);
      this.heatCanvas.push(
              Math.floor(pixel.x - topLeft.x),
              Math.floor(pixel.y - topLeft.y),
              this._data[i][1]);
    }
    this.heatCanvas.render(this.options.step, this.options.degree, this.options.colorscheme);
  }
});

L.imageOverlay.heatCanvas = function (data, options) {
  return new L.ImageOverlay.HeatCanvas(data, options);
};
/*global L */

var Shareabouts = Shareabouts || {};

(function(S, L) {
  'use strict';

  S.Heatmap = function(data, options) {
    var shareaboutsFormatToHeatCanvasFormat = function(sd, valueFn) {
      var hcd = [],
          i, len, val;

      for(i=0, len=sd.length; i<len; i++) {
        if (Object.prototype.toString.call(valueFn) === '[object Function]') {
          val = valueFn(sd[i]);
        } else {
          val = 1;
        }

        hcd[i] = [[sd[i].location.lat, sd[i].location.lng], val];
      }

      return hcd;
    };

    this.options = L.extend({
      valueFn: null,
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
    }, options);

    this.layer = new L.ImageOverlay.HeatCanvas(
      (shareaboutsFormatToHeatCanvasFormat(data, this.options.valueFn)),
      this.options
    );

    this.setData = function(data) {
      this.layer.setData(shareaboutsFormatToHeatCanvasFormat(data, this.options.valueFn));
    };
  };

  S.heatmap = function(data, options) {
    return new S.Heatmap(data, options);
  };
}(Shareabouts, L));