/**
 * Leaflet map initialization for Saulzet & Vous.
 * Handles both editable (report creation) and read-only (report detail) maps.
 */

// Custom green marker icon
var _greenIcon = L.divIcon({
  className: "custom-marker",
  html: '<svg width="25" height="41" viewBox="0 0 25 41" xmlns="http://www.w3.org/2000/svg">' +
    '<path d="M12.5 0C5.6 0 0 5.6 0 12.5C0 21.9 12.5 41 12.5 41S25 21.9 25 12.5C25 5.6 19.4 0 12.5 0Z" fill="#2D5016"/>' +
    '<circle cx="12.5" cy="12.5" r="5" fill="white"/>' +
    "</svg>",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [0, -41],
});

function _initMapElement(el) {
  "use strict";
  var lat = parseFloat(el.dataset.lat) || 45.6565;
  var lng = parseFloat(el.dataset.lng) || 2.9162;
  var zoom = parseInt(el.dataset.zoom, 10) || 14;
  var editable = el.dataset.editable === "True" || el.dataset.editable === "true";

  var map = L.map(el.id).setView([lat, lng], zoom);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    maxZoom: 19,
  }).addTo(map);

  var marker = null;

  // Show existing marker (read-only or pre-set)
  var markerLat = parseFloat(el.dataset.markerLat);
  var markerLng = parseFloat(el.dataset.markerLng);
  if (!isNaN(markerLat) && !isNaN(markerLng)) {
    marker = L.marker([markerLat, markerLng], { icon: _greenIcon }).addTo(map);
    map.setView([markerLat, markerLng], zoom);
  }

  if (editable) {
    // Click to place/move marker
    map.on("click", function (e) {
      var latlng = e.latlng;
      if (marker) {
        marker.setLatLng(latlng);
      } else {
        marker = L.marker(latlng, { icon: _greenIcon }).addTo(map);
      }
      _updateHiddenFields(latlng.lat, latlng.lng);
    });

    // Geolocation button handler
    var geoBtn = document.getElementById("geo-locate-btn");
    if (geoBtn) {
      geoBtn.addEventListener("click", function () {
        if (!navigator.geolocation) {
          return;
        }
        geoBtn.classList.add("loading");
        navigator.geolocation.getCurrentPosition(
          function (pos) {
            geoBtn.classList.remove("loading");
            var latlng = [pos.coords.latitude, pos.coords.longitude];
            map.setView(latlng, 16);
            if (marker) {
              marker.setLatLng(latlng);
            } else {
              marker = L.marker(latlng, { icon: _greenIcon }).addTo(map);
            }
            _updateHiddenFields(latlng[0], latlng[1]);
          },
          function () {
            geoBtn.classList.remove("loading");
          },
          { enableHighAccuracy: true, timeout: 10000 }
        );
      });
    }
  }

  // Fix map size after container becomes visible
  setTimeout(function () {
    map.invalidateSize();
  }, 200);

  return map;
}

function _updateHiddenFields(lat, lng) {
  "use strict";
  var latInput = document.getElementById("id_latitude");
  var lngInput = document.getElementById("id_longitude");
  if (latInput) latInput.value = lat.toFixed(6);
  if (lngInput) lngInput.value = lng.toFixed(6);
}

/**
 * Initialize the map on the create form.
 * Called from Alpine.js when the location section opens.
 */
function initCreateMap() {
  "use strict";
  var el = document.getElementById("map");
  if (el) {
    _initMapElement(el);
  }
}

/**
 * Auto-initialize read-only maps on page load (detail pages).
 */
document.addEventListener("DOMContentLoaded", function () {
  "use strict";
  document.querySelectorAll("[data-lat][data-lng]").forEach(function (el) {
    // Skip the create form map — it will be initialized by initCreateMap()
    if (el.id === "map") return;
    if (el.id) {
      _initMapElement(el);
    }
  });
});
