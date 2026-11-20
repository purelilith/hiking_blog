/* Добавляет CSRF-токен во все POST-формы (токен лежит в <meta name="csrf-token">) */
(function () {
  var meta = document.querySelector('meta[name="csrf-token"]');
  if (!meta) return;
  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll('form[method="post" i]').forEach(function (f) {
      if (f.querySelector('input[name="csrf_token"]')) return;
      var i = document.createElement("input");
      i.type = "hidden"; i.name = "csrf_token"; i.value = meta.content;
      f.appendChild(i);
    });
  });
})();