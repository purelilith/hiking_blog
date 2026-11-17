(function () {
  const el = document.getElementById("map");
  const points = JSON.parse(el.dataset.points);
  const map = L.map("map");
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; участники OpenStreetMap"
  }).addTo(map);

  const line = L.polyline(points, { color: "#0b3d91" }).addTo(map);
  points.forEach(function (p, i) {
    L.marker(p).addTo(map).bindPopup("Точка " + (i + 1));
  });
  map.fitBounds(line.getBounds().pad(0.2));
})();