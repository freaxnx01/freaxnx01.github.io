(function () {
  "use strict";

  // Featured games: copies of the grid cards marked data-featured="1|2|3",
  // in that order, shown large above the filters. The originals stay in the
  // grid, so filters and the game count are unchanged. Runs before
  // lightbox.js (so the copies open the lightbox and get the "Inspired by"
  // line) and before filter.js (which adds NEW/MOBILE tags and hides the
  // section while a search or filter is active).
  var section = document.getElementById("featured");
  var grid = section && section.querySelector(".featured__grid");
  if (!grid) return;

  var picks = Array.prototype.slice.call(document.querySelectorAll(".hub__grid .card[data-featured]"));
  picks.sort(function (a, b) {
    return Number(a.getAttribute("data-featured")) - Number(b.getAttribute("data-featured"));
  });
  if (picks.length === 0) return;

  picks.forEach(function (card) {
    var copy = card.cloneNode(true);
    copy.classList.add("card--featured");
    copy.removeAttribute("data-featured");
    // The full screenshot where the card is wide or the screen is dense.
    var thumb = copy.querySelector(".card__thumb");
    var full = thumb && thumb.getAttribute("data-full");
    if (full) {
      thumb.setAttribute("srcset", thumb.getAttribute("src") + " 400w, " + full + " 1280w");
      thumb.setAttribute("sizes", "(max-width: 700px) 100vw, 360px");
    }
    grid.appendChild(copy);
  });
  section.hidden = false;
})();
