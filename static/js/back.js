(function () {
  var link = document.getElementById("back-link");
  if (!link) return;
  link.addEventListener("click", function (e) {
    var ref = document.referrer;
    var fromSite = ref && ref.indexOf(location.origin) === 0;
    var fromForm = /\/routes\/(new|\d+\/edit)/.test(ref);
    if (fromSite && !fromForm && history.length > 1) {
      e.preventDefault();
      history.back();
    }
  });
})();