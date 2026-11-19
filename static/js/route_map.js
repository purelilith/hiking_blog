(function () {
  const el = document.getElementById("map");
  if (!el) return;
  let points = [];
  try { points = JSON.parse(el.dataset.points || "[]"); } catch (e) {}

  const map = L.map("map").setView([55.75, 37.62], 5);
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; участники OpenStreetMap"
  }).addTo(map);

  if (points.length > 0) {
    const line = L.polyline(points, { color: "#bf6a02", weight: 4 }).addTo(map);
    points.forEach(function (p, i) {
      L.marker(p).addTo(map).bindPopup("Точка " + (i + 1));
    });
    if (points.length > 1) {
      map.fitBounds(line.getBounds().pad(0.2));
    } else {
      map.setView(points[0], 13);
    }
  }
})();
