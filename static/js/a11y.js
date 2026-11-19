(function () {
  var root = document.documentElement;
  var DEFAULTS = { size: 100, contrast: "normal", theme: "light" };
  var state = Object.assign({}, DEFAULTS);

  try {
    var saved = JSON.parse(localStorage.getItem("tropa_prefs_v2") || "{}");
    if (saved.size >= 85 && saved.size <= 150) state.size = Number(saved.size);
    if (saved.contrast === "high" || saved.contrast === "normal") state.contrast = saved.contrast;
    if (saved.theme === "dark" || saved.theme === "light") state.theme = saved.theme;
  } catch (e) {}

  function apply() {
    root.style.fontSize = state.size + "%";
    root.dataset.contrast = state.contrast;
    root.dataset.theme = state.theme;
    try { localStorage.setItem("tropa_prefs_v2", JSON.stringify(state)); } catch (e) {}
  }
  apply();

  document.addEventListener("DOMContentLoaded", function () {
    var btn = document.getElementById("settings-btn");
    var panel = document.getElementById("settings-panel");
    var range = document.getElementById("font-range");
    var output = document.getElementById("font-value");
    var toggle = document.getElementById("contrast-toggle");
    var themeBtns = panel ? panel.querySelectorAll("[data-theme-val]") : [];

    if (!btn || !panel) return;

    function refresh() {
      if (range) range.value = state.size;
      if (output) output.textContent = state.size + "%";
      if (toggle) toggle.checked = state.contrast === "high";
      themeBtns.forEach(function (b) {
        b.setAttribute("aria-pressed", String(b.dataset.themeVal === state.theme));
      });
      apply();
    }

    function setOpen(open) {
      panel.hidden = !open;
      btn.setAttribute("aria-expanded", String(open));
    }

    btn.addEventListener("click", function (e) {
      e.stopPropagation();
      setOpen(panel.hidden);
    });

    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && !panel.hidden) {
        setOpen(false);
        btn.focus();
      }
    });

    document.addEventListener("click", function (e) {
      if (!panel.hidden && !panel.contains(e.target) && !btn.contains(e.target)) {
        setOpen(false);
      }
    });

    if (range) {
      range.addEventListener("input", function () {
        state.size = Number(range.value);
        refresh();
      });
    }

    if (toggle) {
      toggle.addEventListener("change", function () {
        state.contrast = toggle.checked ? "high" : "normal";
        refresh();
      });
    }

    themeBtns.forEach(function (b) {
      b.addEventListener("click", function () {
        state.theme = b.dataset.themeVal;
        refresh();
      });
    });

    var resetBtn = document.getElementById("settings-reset");
    if (resetBtn) {
      resetBtn.addEventListener("click", function () {
        state = Object.assign({}, DEFAULTS);
        refresh();
      });
    }

    refresh();
  });
})();
