/* Ссылка «← Назад»: если пользователь пришёл с другой страницы сайта (не из формы маршрута),
   возвращаем его в то место, где он был; иначе работает обычная ссылка на каталог. */
(function () {
  var link = document.getElementById("back-link");
  if (!link) return;
  link.addEventListener("click", function (e) {
    var ref = document.referrer;
    var fromSite = ref && ref.indexOf(location.origin) === 0;
    /* Из формы не возвращаем: иначе можно попасть на недосохранённую страницу правки */
    var fromForm = /\/routes\/(new|\d+\/edit)/.test(ref);
    if (fromSite && !fromForm && history.length > 1) {
      e.preventDefault();
      history.back();
    }
  });
})();
