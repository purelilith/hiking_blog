/* Карта на странице маршрута: линия и места только для просмотра.
   Данные берутся из атрибутов data-points и data-places элемента #map. */
(function () {
  var el = document.getElementById("map");
  if (!el) return;
  var points = [], places = [];
  try { points = JSON.parse(el.dataset.points || "[]"); } catch (e) {}
  try { places = JSON.parse(el.dataset.places || "[]"); } catch (e) {}

  var map = TropaMap.create("map");
  var group = L.featureGroup().addTo(map);
  if (points.length > 1) {
    L.polyline(points, { color: "#bf6a02", weight: 4 }).addTo(group);
  }
  places.forEach(function (p) {
    L.marker([p.lat, p.lon], { title: p.name, alt: p.name })
      .addTo(group).bindPopup(TropaMap.placePopup(p));
  });
  if (group.getLayers().length) {
    map.fitBounds(group.getBounds().pad(0.2), { maxZoom: 15 });
  }
})();
