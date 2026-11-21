(function () {
  var box = document.getElementById("post-editor");
  if (!box) return;
  var holder = document.getElementById("post-blocks");
  var status = document.getElementById("post-status");
  var hidden = document.getElementById("description");
  var form = hidden.form;
  var csrf = form.querySelector('input[name="csrf_token"]');
  var MAX = 5 * 1024 * 1024;
  var seq = 0;
  var known = {};
  try { JSON.parse(box.dataset.photos || "[]").forEach(function (p) { known[p.id] = p; }); } catch (e) {}

  function el(tag, props, text) {
    var n = document.createElement(tag);
    Object.keys(props || {}).forEach(function (k) { n[k] = props[k]; });
    if (text) { n.textContent = text; }
    return n;
  }
  function small(label, flag) {
    var b = el("button", { type: "button", className: "btn btn-small" }, label);
    b.setAttribute(flag, "");
    return b;
  }

  /* Подписи и номера блоков пересчитываются после каждого изменения */
  function renumber() {
    var blocks = holder.querySelectorAll(".post-block");
    blocks.forEach(function (b, i) {
      var n = i + 1;
      b.querySelector(".post-block-title").textContent = "Блок " + n + ": " + (b.dataset.kind === "text" ? "текст" : "фото");
      b.querySelector("[data-up]").setAttribute("aria-label", "Блок " + n + ": переместить выше");
      b.querySelector("[data-down]").setAttribute("aria-label", "Блок " + n + ": переместить ниже");
      b.querySelector("[data-del]").setAttribute("aria-label", "Блок " + n + ": убрать");
    });
  }

  function makeBlock(kind) {
    var block = el("div", { className: "post-block" });
    block.dataset.kind = kind;
    block.tabIndex = -1;
    var head = el("div", { className: "post-block-head" });
    var bar = el("div", { className: "post-block-bar" });
    var up = small("Выше", "data-up"), down = small("Ниже", "data-down"), del = small("Убрать", "data-del");
    up.addEventListener("click", function () {
      var prev = block.previousElementSibling;
      if (prev) { holder.insertBefore(block, prev); renumber(); up.focus(); }
    });
    down.addEventListener("click", function () {
      var next = block.nextElementSibling;
      if (next) { holder.insertBefore(next, block); renumber(); down.focus(); }
    });
    del.addEventListener("click", function () {
      block.remove(); renumber();
      status.textContent = "Блок убран.";
      document.getElementById("add-text-block").focus();
    });
    bar.append(up, down, del);
    head.append(el("strong", { className: "post-block-title" }), bar);
    block.appendChild(head);
    holder.appendChild(block);
    return block;
  }

  function addText(value, focus) {
    var block = makeBlock("text");
    var id = "post-text-" + (++seq);
    var ta = el("textarea", { id: id, rows: 6, maxLength: 5000 });
    ta.value = value || "";
    block.append(el("label", { htmlFor: id }, "Текст"), ta);
    renumber();
    if (focus) { ta.focus(); }
  }

  function showUploaded(body, p) {
    body.innerHTML = "";
    body.append(el("img", { src: p.url, alt: p.caption, className: "post-thumb" }),
                el("p", { className: "post-caption" }, "Подпись: " + p.caption));
  }

  function showUploader(block, body) {
    var n = ++seq;
    var file = el("input", { id: "post-file-" + n, type: "file",
                             accept: ".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp" });
    var cap = el("input", { id: "post-cap-" + n, type: "text", maxLength: 200 });
    var go = el("button", { type: "button", className: "btn btn-small" }, "Загрузить фото");
    var msg = el("p", { className: "hint" });
    msg.setAttribute("role", "status");
        var prev = el("img", { className: "post-thumb", alt: "Предпросмотр выбранного фото" });
    prev.hidden = true;
    var url = null;
    file.addEventListener("change", function () {
      if (url) { URL.revokeObjectURL(url); url = null; }
      var f = file.files && file.files[0];
      if (f && /\.(jpe?g|png|webp)$/i.test(f.name) && f.size <= MAX) {
        url = URL.createObjectURL(f); prev.src = url; prev.hidden = false;
      } else { prev.removeAttribute("src"); prev.hidden = true; }
    });
    body.append(el("label", { htmlFor: file.id }, "1. Выберите фото (JPG, PNG, WEBP, до 5 МБ)"), file, prev,
                el("label", { htmlFor: cap.id }, "2. Опишите, что на фото (это подпись и текст для незрячих)"), cap,
                go, msg);

    cap.addEventListener("keydown", function (e) { if (e.key === "Enter") { e.preventDefault(); go.click(); } });
        /* Загрузка; возвращает Promise: true, если фото загружено */
    function doUpload() {
      var f = file.files && file.files[0], c = cap.value.trim();
      if (!f) { msg.textContent = "Сначала выберите фото."; file.focus(); return Promise.resolve(false); }
      if (!/\.(jpe?g|png|webp)$/i.test(f.name)) { msg.textContent = "Подойдут только JPG, PNG или WEBP."; return Promise.resolve(false); }
      if (f.size > MAX) {
        msg.textContent = "Файл весит " + (f.size / 1048576).toFixed(1).replace(".", ",") + " МБ, а можно до 5 МБ.";
        file.value = ""; return Promise.resolve(false);
      }
      if (!c) { msg.textContent = "Опишите, что на фото."; cap.focus(); return Promise.resolve(false); }

      var fd = new FormData();
      fd.append("photo", f); fd.append("caption", c);
      go.disabled = true; msg.textContent = "Загружаю…";
      return fetch(box.dataset.uploadUrl, {
        method: "POST", body: fd, credentials: "same-origin",
        headers: { "X-CSRFToken": csrf ? csrf.value : "" }
      })
        .then(function (r) { return r.json(); })
        .then(function (d) {
          if (d.error) { msg.textContent = d.error; return false; }
          block.dataset.photoId = d.id;
          block.classList.remove("post-block--error");
          showUploaded(body, d);
          status.textContent = "Фото загружено.";
          return true;
        })
        .catch(function () { msg.textContent = "Не удалось загрузить. Проверьте размер (до 5 МБ) и соединение."; return false; })
        .then(function (ok) { go.disabled = false; return ok; });
    }
    block._upload = doUpload;
    go.addEventListener("click", function () {
      doUpload().then(function (ok) { if (ok) { block.focus(); } });
    });
  }

  function addPhoto(photo, focus) {
    var block = makeBlock("photo");
    var body = el("div", { className: "post-photo-body" });
    block.appendChild(body);
    if (photo) { block.dataset.photoId = photo.id; showUploaded(body, photo); }
    else { showUploader(block, body); if (focus) { body.querySelector("input").focus(); } }
    renumber();
  }

  document.getElementById("add-text-block").addEventListener("click", function () { addText("", true); });
  document.getElementById("add-photo-block").addEventListener("click", function () { addPhoto(null, true); });

  /* Собираем текст и метки [фото:N] из блоков при отправке формы */
  var submitError = document.getElementById("submit-error");
  var sending = false;

  /* Показываем ошибку рядом с кнопкой «Сохранить» и подсвечиваем блок */
  function fail(text, block) {
    status.textContent = text;
    if (submitError) { submitError.textContent = text; submitError.hidden = false; }
    if (block) {
      block.classList.add("post-block--error");
      var f = block.querySelector("input, textarea");
      (f || block).focus();
    }
  }

  form.addEventListener("submit", function (e) {
    if (submitError) { submitError.hidden = true; }
    holder.querySelectorAll(".post-block--error").forEach(function (b) { b.classList.remove("post-block--error"); });

    /* Фото выбраны, но не загружены: загружаем сами, потом отправляем форму */
    var waiting = Array.prototype.slice.call(
      holder.querySelectorAll('.post-block[data-kind="photo"]:not([data-photo-id])'));
    if (waiting.length) {
      e.preventDefault();
      if (sending) { return; }
      sending = true;
      status.textContent = "Загружаю фото…";
      waiting.reduce(function (chain, block) {
        return chain.then(function (okSoFar) {
          if (!okSoFar) { return false; }
          return block._upload().then(function (ok) {
            if (!ok) { fail("Фото не загружено: выберите файл и опишите фото либо уберите этот блок.", block); }
            return ok;
          });
        });
      }, Promise.resolve(true)).then(function (ok) {
        sending = false;
        if (ok) { form.requestSubmit(); }
      });
      return;
    }

    var parts = [];
    holder.querySelectorAll(".post-block").forEach(function (b) {
      if (b.dataset.kind === "text") {
        var t = b.querySelector("textarea").value.trim();
        if (t) { parts.push(t); }
      } else {
        parts.push("[фото:" + b.dataset.photoId + "]");
      }
    });
    if (!parts.length) {
      e.preventDefault();
      fail("Напишите хотя бы немного текста в описании.", holder.querySelector(".post-block"));
      return;
    }
    hidden.value = parts.join("\n\n");
  });

  /* Разбираем уже имеющееся описание (при правке или после ошибки) на блоки */
  (hidden.value || "").split(/\[фото:(\d{1,9})\]/).forEach(function (chunk, i) {
    if (i % 2 === 0) { if (chunk.trim()) { addText(chunk.trim()); } }
    else if (known[chunk]) { addPhoto(known[chunk]); }
  });
  if (!holder.children.length) { addText(""); }
})();