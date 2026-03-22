/**
 * Leaflet map initialization for Saulzet & Vous.
 * Handles both editable (report creation) and read-only (report detail) maps.
 */
(function () {
  "use strict";

  // Custom green marker icon
  const greenIcon = L.divIcon({
    className: "custom-marker",
    html: '<svg width="25" height="41" viewBox="0 0 25 41" xmlns="http://www.w3.org/2000/svg">' +
      '<path d="M12.5 0C5.6 0 0 5.6 0 12.5C0 21.9 12.5 41 12.5 41S25 21.9 25 12.5C25 5.6 19.4 0 12.5 0Z" fill="#2D5016"/>' +
      '<circle cx="12.5" cy="12.5" r="5" fill="white"/>' +
      "</svg>",
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [0, -41],
  });

  function initMap(el) {
    const lat = parseFloat(el.dataset.lat) || 45.6565;
    const lng = parseFloat(el.dataset.lng) || 2.9162;
    const zoom = parseInt(el.dataset.zoom, 10) || 14;
    const editable = el.dataset.editable === "True" || el.dataset.editable === "true";

    const map = L.map(el.id).setView([lat, lng], zoom);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
      maxZoom: 19,
    }).addTo(map);

    let marker = null;

    // Show existing marker (read-only or pre-set)
    const markerLat = parseFloat(el.dataset.markerLat);
    const markerLng = parseFloat(el.dataset.markerLng);
    if (!isNaN(markerLat) && !isNaN(markerLng)) {
      marker = L.marker([markerLat, markerLng], { icon: greenIcon }).addTo(map);
      map.setView([markerLat, markerLng], zoom);
    }

    if (editable) {
      // Click to place/move marker
      map.on("click", function (e) {
        const latlng = e.latlng;
        if (marker) {
          marker.setLatLng(latlng);
        } else {
          marker = L.marker(latlng, { icon: greenIcon }).addTo(map);
        }
        updateHiddenFields(latlng.lat, latlng.lng);
      });

      // Geolocation button handler
      const geoBtn = document.getElementById("geo-locate-btn");
      if (geoBtn) {
        geoBtn.addEventListener("click", function () {
          if (!navigator.geolocation) {
            return;
          }
          geoBtn.classList.add("loading");
          navigator.geolocation.getCurrentPosition(
            function (pos) {
              geoBtn.classList.remove("loading");
              const latlng = [pos.coords.latitude, pos.coords.longitude];
              map.setView(latlng, 16);
              if (marker) {
                marker.setLatLng(latlng);
              } else {
                marker = L.marker(latlng, { icon: greenIcon }).addTo(map);
              }
              updateHiddenFields(latlng[0], latlng[1]);
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

  function updateHiddenFields(lat, lng) {
    const latInput = document.getElementById("id_latitude");
    const lngInput = document.getElementById("id_longitude");
    if (latInput) latInput.value = lat.toFixed(6);
    if (lngInput) lngInput.value = lng.toFixed(6);
  }

  // Initialize all maps on page
  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("[data-lat][data-lng]").forEach(function (el) {
      if (el.id) {
        initMap(el);
      }
    });
  });
})();
