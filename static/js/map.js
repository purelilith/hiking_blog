(function () {
  const input = document.getElementById("points");
  const list = document.getElementById("points-list");
  const status = document.getElementById("point-status");
  let points = [];
  try { points = JSON.parse(input.value || "[]"); } catch (e) { points = []; }

  const map = L.map("map").setView([55.75, 37.62], 5);
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; участники OpenStreetMap"
  }).addTo(map);

  const line = L.polyline([], { color: "#0b3d91" }).addTo(map);
  const markers = L.layerGroup().addTo(map);

  function render() {
    line.setLatLngs(points);
    markers.clearLayers();
    list.innerHTML = "";
    points.forEach(function (p, i) {
      L.marker(p).addTo(markers);
      const li = document.createElement("li");
      li.textContent = p[0].toFixed(5) + ", " + p[1].toFixed(5);
      list.appendChild(li);
    });
    input.value = JSON.stringify(points);
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