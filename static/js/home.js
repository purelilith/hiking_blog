(function () {
  /* 1. Растягиваем «РОССИИ» на всю ширину текстового блока */
  function fitHero() {
    var outer = document.querySelector(".hero-big");
    if (!outer) return;
    var inner = outer.firstElementChild;
    if (!inner) return;
    outer.style.fontSize = "100px";
    var innerW = inner.getBoundingClientRect().width;
    if (innerW > 0) {
      var ratio = outer.clientWidth / innerW;
      outer.style.fontSize = (100 * ratio) + "px";
    }
  }
  if (document.fonts && document.fonts.load) {
    document.fonts.load("100px Manomakh").then(fitHero, fitHero);
  }
  window.addEventListener("load", fitHero);
  window.addEventListener("resize", fitHero);
  fitHero();

  /* 2. Кнопка «Смотреть ещё» */
  var btn = document.getElementById("load-more");
  var list = document.getElementById("popular-list");
  var status = document.getElementById("load-status");
  if (!btn || !list) return;

  btn.addEventListener("click", function (e) {
    e.preventDefault();
    var offset = list.children.length;
    fetch(btn.dataset.url + "?offset=" + offset)
      .then(function (r) { if (!r.ok) throw new Error(); return r.json(); })
      .then(function (data) {
        var before = list.children.length;
        list.insertAdjacentHTML("beforeend", data.html);
        var firstNew = list.children[before];
        if (firstNew && firstNew.querySelector("a")) {
          firstNew.querySelector("a").focus();
        }
        if (status) {
          status.textContent = "Показано маршрутов: " + list.children.length;
        }
        if (!data.has_more) {
          btn.hidden = true;
        }
      })
      .catch(function () { window.location = btn.href; });
  });
})();
