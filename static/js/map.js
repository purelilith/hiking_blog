(function () {
  const input = document.getElementById("points");
  const list = document.getElementById("points-list");
  const status = document.getElementById("point-status");
  const distBadge = document.getElementById("live-distance");
  if (!input) return;

  let points = [];
  try { points = JSON.parse(input.value || "[]"); } catch (e) { points = []; }

  const map = L.map("map").setView([55.75, 37.62], 5);
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; участники OpenStreetMap"
  }).addTo(map);

  const line = L.polyline([], { color: "#bf6a02", weight: 4 }).addTo(map);
  const markers = L.layerGroup().addTo(map);

  function calcKm(pts) {
    let total = 0;
    for (let i = 1; i < pts.length; i++) {
      const p1 = pts[i - 1][0] * Math.PI / 180;
      const p2 = pts[i][0] * Math.PI / 180;
      const dlon = (pts[i][1] - pts[i - 1][1]) * Math.PI / 180;
      const a = Math.sin((p2 - p1) / 2) ** 2 + Math.cos(p1) * Math.cos(p2) * Math.sin(dlon / 2) ** 2;
      total += 6371 * 2 * Math.asin(Math.sqrt(a));
    }
    return total.toFixed(2);
  }

  function render() {
    line.setLatLngs(points);
    markers.clearLayers();
    list.innerHTML = "";
    points.forEach(function (p, i) {
      L.marker(p).addTo(markers).bindPopup("Точка " + (i + 1));
      const li = document.createElement("li");
      li.textContent = p[0].toFixed(5) + ", " + p[1].toFixed(5);
      list.appendChild(li);
    });
    input.value = JSON.stringify(points);
    if (distBadge) {
      distBadge.textContent = "Точек: " + points.length + " · Расчётная длина: " + calcKm(points) + " км";
    }
  }

  function addPoint(lat, lon) {
    points.push([lat, lon]);
    render();
    status.textContent = "Добавлена точка " + points.length + ".";
  }

  map.on("click", function (e) { addPoint(e.latlng.lat, e.latlng.lng); });

  document.getElementById("add-point").addEventListener("click", function () {
    const lat = parseFloat(document.getElementById("lat-input").value.replace(",", "."));
    const lon = parseFloat(document.getElementById("lon-input").value.replace(",", "."));
    if (isNaN(lat) || isNaN(lon) || Math.abs(lat) > 90 || Math.abs(lon) > 180) {
      status.textContent = "Введите правильные координаты, например 55.75 и 37.62.";
      return;
    }
    addPoint(lat, lon);
  });

  document.getElementById("undo-point").addEventListener("click", function () {
    points.pop();
    render();
    status.textContent = "Последняя точка удалена.";
  });

  document.getElementById("clear-points").addEventListener("click", function () {
    points = [];
    render();
    status.textContent = "Все точки удалены.";
  });

  render();
  if (points.length > 1) { map.fitBounds(line.getBounds().pad(0.2)); }
})();
