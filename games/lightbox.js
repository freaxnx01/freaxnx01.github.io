(function () {
  "use strict";

  var overlay = document.getElementById("lightbox");
  if (!overlay) return;

  var img = overlay.querySelector(".lightbox__img");
  var caption = overlay.querySelector(".lightbox__caption");
  var closeBtn = overlay.querySelector(".lightbox__close");

  // Retro-clone cards: show what the game is inspired by, if known.
  document.querySelectorAll(".card[data-original-title]").forEach(function (card) {
    var title = card.getAttribute("data-original-title");
    var url = card.getAttribute("data-original-url");
    var body = card.querySelector(".card__body");
    if (!title || !body) return;

    var p = document.createElement("p");
    p.className = "card__inspired";

    if (url) {
      p.appendChild(document.createTextNode("Inspired by "));
      var a = document.createElement("a");
      a.href = url;
      a.target = "_blank";
      a.rel = "noopener";
      a.textContent = title;
      p.appendChild(a);
    } else {
      p.textContent = "Inspired by " + title;
    }

    var badges = body.querySelector(".card__badges");
    if (badges) {
      body.insertBefore(p, badges);
    } else {
      body.appendChild(p);
    }
  });

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
