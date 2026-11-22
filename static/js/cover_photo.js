/* Обложка маршрута в форме: предпросмотр выбранного файла и проверка типа и размера
   до отправки (сервер всё равно проверяет файл ещё раз). */
(function () {
  var input = document.getElementById("photo");
  var preview = document.getElementById("photo-preview");
  var status = document.getElementById("photo-status");
  var removeCheck = document.getElementById("remove-photo");
  if (!input || !preview) return;

  var MAX = 5 * 1024 * 1024;  // 5 МБ, как на сервере
  var initialSrc = preview.getAttribute("src") || "";
  var objectUrl = null;

  /* Показывает картинку в предпросмотре или прячет его, если src пустой */
  function show(src) {
    if (src) { preview.src = src; preview.hidden = false; }
    else { preview.removeAttribute("src"); preview.hidden = true; }
  }

  input.addEventListener("change", function () {
    if (objectUrl) { URL.revokeObjectURL(objectUrl); objectUrl = null; }
    status.textContent = "";
    var file = input.files && input.files[0];
    if (!file) { show(initialSrc); return; }

    var okType = /^image\/(jpeg|png|webp)$/.test(file.type) || /\.(jpe?g|png|webp)$/i.test(file.name);
    if (!okType) {
      status.textContent = "Подойдут только файлы JPG, PNG или WEBP.";
      input.value = ""; show(initialSrc); return;
    }
    if (file.size > MAX) {
      status.textContent = "Файл весит " + (file.size / 1048576).toFixed(1).replace(".", ",") +
                           " МБ, а можно до 5 МБ. Выберите файл поменьше.";
      input.value = ""; show(initialSrc); return;
    }
    objectUrl = URL.createObjectURL(file);
    show(objectUrl);
    if (removeCheck) removeCheck.checked = false;
  });
})();
