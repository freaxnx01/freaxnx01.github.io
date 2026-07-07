(function () {
  "use strict";

  var overlay = document.getElementById("lightbox");
  if (!overlay) return;

  var img = overlay.querySelector(".lightbox__img");
  var caption = overlay.querySelector(".lightbox__caption");
  var closeBtn = overlay.querySelector(".lightbox__close");

  function open(full, title) {
    img.src = full;
    img.alt = title;
    caption.textContent = title;
    overlay.classList.add("is-open");
  }

  function close() {
    overlay.classList.remove("is-open");
    img.removeAttribute("src");
  }

  // Any element carrying data-full opens the lightbox.
  document.querySelectorAll("[data-full]").forEach(function (el) {
    function activate() {
      open(el.getAttribute("data-full"), el.getAttribute("data-title") || "");
    }
    el.addEventListener("click", activate);
    el.addEventListener("keydown", function (e) {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        activate();
      }
    });
  });

  overlay.addEventListener("click", function (e) {
    if (e.target === overlay) close();
  });
  closeBtn.addEventListener("click", close);
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && overlay.classList.contains("is-open")) close();
  });
})();
