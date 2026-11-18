(function () {
  var btn = document.getElementById("load-more");
  var list = document.getElementById("popular-list");
  var status = document.getElementById("load-status");
  if (!btn || !list) { return; }

  btn.addEventListener("click", function (e) {
    e.preventDefault();
    var offset = list.children.length;
    fetch(btn.dataset.url + "?offset=" + offset)
      .then(function (r) { if (!r.ok) { throw new Error(); } return r.json(); })
      .then(function (data) {
        var before = list.children.length;
        list.insertAdjacentHTML("beforeend", data.html);
        var firstNew = list.children[before];
        if (firstNew) { firstNew.querySelector("a").focus(); }
        status.textContent = "Показано маршрутов: " + list.children.length;
        if (!data.has_more) { btn.hidden = true; }
      })
      .catch(function () { window.location = btn.href; });
  });
})();