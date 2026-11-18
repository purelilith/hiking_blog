(function () {
  var root = document.documentElement;
  var SIZE_NAMES = ["", "обычный", "крупный", "очень крупный"];
  var state = { size: 1, contrast: "normal" };
  try { Object.assign(state, JSON.parse(localStorage.getItem("a11y") || "{}")); } catch (e) {}

  function apply() {
    root.dataset.size = String(state.size);
    root.dataset.contrast = state.contrast;
    try { localStorage.setItem("a11y", JSON.stringify(state)); } catch (e) {}
  }
  apply();

  document.addEventListener("DOMContentLoaded", function () {
    var btn = document.getElementById("settings-btn");
    var panel = document.getElementById("settings-panel");
    var label = document.getElementById("size-label");
    var toggle = document.getElementById("contrast-toggle");

    function refresh() {
      label.textContent = SIZE_NAMES[state.size];
      toggle.checked = state.contrast === "high";
      apply();
    }
    function setOpen(open) {
      panel.hidden = !open;
      btn.setAttribute("aria-expanded", String(open));
    }

    btn.addEventListener("click", function () { setOpen(panel.hidden); });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && !panel.hidden) { setOpen(false); btn.focus(); }
    });
    document.addEventListener("click", function (e) {
      if (!panel.hidden && !panel.contains(e.target) && !btn.contains(e.target)) { setOpen(false); }
    });

    panel.querySelectorAll("[data-size-step]").forEach(function (b) {
      b.addEventListener("click", function () {
        state.size = Math.min(3, Math.max(1, state.size + Number(b.dataset.sizeStep)));
        refresh();
      });
    });
    toggle.addEventListener("change", function () {
      state.contrast = toggle.checked ? "high" : "normal";
      refresh();
    });
    document.getElementById("settings-reset").addEventListener("click", function () {
      state.size = 1; state.contrast = "normal"; refresh();
    });
    refresh();
  });
})();