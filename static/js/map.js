(function () {
  var pointsInput = document.getElementById("points");
  var placesInput = document.getElementById("places");
  if (!pointsInput || !placesInput) return;
  var list = document.getElementById("places-list");
  var status = document.getElementById("point-status");
  var badge = document.getElementById("live-distance");

  var points = [], places = [];
  try { points = JSON.parse(pointsInput.value || "[]"); } catch (e) {}
  try { places = JSON.parse(placesInput.value || "[]"); } catch (e) {}

  var map = TropaMap.create("map");
  var line = L.polyline([], { color: "#bf6a02", weight: 4 }).addTo(map);
  var dots = L.layerGroup().addTo(map);
  var pins = L.layerGroup().addTo(map);

  function mode() { return document.querySelector('input[name="map-mode"]:checked').value; }
  function noEnter(e) { if (e.key === "Enter") { e.preventDefault(); } }

  function calcKm(pts) {
    var total = 0;
    for (var i = 1; i < pts.length; i++) {
      var p1 = pts[i - 1][0] * Math.PI / 180, p2 = pts[i][0] * Math.PI / 180;
      var dlon = (pts[i][1] - pts[i - 1][1]) * Math.PI / 180;
      var a = Math.pow(Math.sin((p2 - p1) / 2), 2) +
              Math.cos(p1) * Math.cos(p2) * Math.pow(Math.sin(dlon / 2), 2);
      total += 6371 * 2 * Math.asin(Math.sqrt(a));
    }
    return total.toFixed(2);
  }

  /* Записывает данные в скрытые поля формы и обновляет подпись над картой */
  function syncInputs() {
    pointsInput.value = JSON.stringify(points);
    placesInput.value = JSON.stringify(places);
    badge.textContent = "Точек линии: " + points.length + " · Мест: " + places.length +
                        " · Расчётная длина: " + calcKm(points) + " км";
  }

  function renderMap() {
    line.setLatLngs(points);
    dots.clearLayers();
    pins.clearLayers();
    points.forEach(function (p) {
      L.circleMarker(p, { radius: 4, color: "#bf6a02", fillColor: "#bf6a02",
                          fillOpacity: 1, interactive: false }).addTo(dots);
    });
    places.forEach(function (p) {
      var m = L.marker([p.lat, p.lon], { draggable: true, title: p.name, alt: p.name }).addTo(pins);
      m.bindPopup(TropaMap.placePopup(p));
      m.on("dragend", function () {
        var ll = m.getLatLng();
        p.lat = ll.lat; p.lon = ll.lng;
        syncInputs();
      });
    });
    syncInputs();
  }

  /* Список мест под картой: у каждого можно изменить название и заметку */
  function buildList() {
    list.innerHTML = "";
    places.forEach(function (p, i) {
      var li = document.createElement("li");
      li.className = "place-item";

      var l1 = document.createElement("label");
      l1.htmlFor = "place-name-" + i;
      l1.textContent = "Название места " + (i + 1);
      var name = document.createElement("input");
      name.id = "place-name-" + i; name.type = "text"; name.required = true;
      name.maxLength = 80; name.value = p.name;
      name.addEventListener("input", function () { p.name = name.value; renderMap(); });
      name.addEventListener("keydown", noEnter);

      var l2 = document.createElement("label");
      l2.htmlFor = "place-note-" + i;
      l2.textContent = "Заметка (необязательно)";
      var note = document.createElement("input");
      note.id = "place-note-" + i; note.type = "text"; note.maxLength = 300; note.value = p.note || "";
      note.addEventListener("input", function () { p.note = note.value; renderMap(); });
      note.addEventListener("keydown", noEnter);

      var del = document.createElement("button");
      del.type = "button"; del.className = "btn btn-small"; del.textContent = "Удалить место";
      del.addEventListener("click", function () {
        places.splice(i, 1);
        buildList(); renderMap();
        status.textContent = "Место удалено.";
      });

      li.append(l1, name, l2, note, del);
      list.appendChild(li);
    });
  }

  function addPoint(lat, lon) {
    points.push([lat, lon]);
    renderMap();
    status.textContent = "Добавлена точка линии " + points.length + ".";
  }

  function addPlace(lat, lon) {
    var def = "Место " + (places.length + 1);
    var name = window.prompt("Название места:", def);
    if (name === null) { return; }
    name = name.trim().slice(0, 80) || def;
    places.push({ lat: lat, lon: lon, name: name, note: "" });
    buildList(); renderMap();
    status.textContent = "Добавлено место «" + name + "». Название и заметку можно изменить в списке ниже.";
  }

  function addAt(lat, lon) { if (mode() === "place") { addPlace(lat, lon); } else { addPoint(lat, lon); } }

  map.on("click", function (e) { addAt(e.latlng.lat, e.latlng.lng); });

  function addByCoords() {
    var lat = parseFloat(document.getElementById("lat-input").value.replace(",", "."));
    var lon = parseFloat(document.getElementById("lon-input").value.replace(",", "."));
    if (isNaN(lat) || isNaN(lon) || Math.abs(lat) > 90 || Math.abs(lon) > 180) {
      status.textContent = "Введите правильные координаты, например 55.75 и 37.62.";
      return;
    }
    addAt(lat, lon);
  }
  document.getElementById("add-point").addEventListener("click", addByCoords);
  ["lat-input", "lon-input"].forEach(function (id) {
    document.getElementById(id).addEventListener("keydown", function (e) {
      if (e.key === "Enter") { e.preventDefault(); addByCoords(); }
    });
  });

  document.getElementById("undo-point").addEventListener("click", function () {
    points.pop(); renderMap();
    status.textContent = "Последняя точка линии удалена.";
  });
  document.getElementById("clear-points").addEventListener("click", function () {
    if (points.length && !window.confirm("Очистить всю линию маршрута? Места останутся.")) { return; }
    points = []; renderMap();
    status.textContent = "Линия очищена.";
  });

  buildList();
  renderMap();
  var all = points.concat(places.map(function (p) { return [p.lat, p.lon]; }));
  if (all.length > 1) { map.fitBounds(all, { padding: [30, 30] }); }
  else if (all.length === 1) { map.setView(all[0], 13); }
})();