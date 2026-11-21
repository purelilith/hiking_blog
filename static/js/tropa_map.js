/* Общая карта: обычная и топографическая (переключатель справа вверху) */
window.TropaMap = {
  create: function (id) {
    var osm = L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19, attribution: "&copy; участники OpenStreetMap"
    });
    var topo = L.tileLayer("https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png", {
      maxZoom: 17,
      attribution: "Данные: &copy; OpenStreetMap, SRTM · Стиль: &copy; OpenTopoMap (CC-BY-SA)"
    });
    var map = L.map(id, { layers: [osm] }).setView([55.75, 37.62], 5);
    L.control.layers({ "Обычная карта": osm, "Топографическая": topo }).addTo(map);
    return map;
  },
  /* Всплывающее окно места; текст вставляется как текст, не как код */
  placePopup: function (p) {
    var box = document.createElement("div");
    var b = document.createElement("strong");
    b.textContent = p.name;
    box.appendChild(b);
    if (p.note) {
      var n = document.createElement("div");
      n.textContent = p.note;
      box.appendChild(n);
    }
    return box;
  }
};