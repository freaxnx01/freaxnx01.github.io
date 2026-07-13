(function () {
  "use strict";

  var panel = document.querySelector("[data-filters]");
  var grid = document.querySelector(".hub__grid");
  if (!panel || !grid) return;

  var cards = Array.prototype.slice.call(grid.querySelectorAll(".card"));
  var primaryBtns = Array.prototype.slice.call(panel.querySelectorAll("[data-filter]"));
  var subRow = panel.querySelector(".filter-row--sub");
  var subBtns = Array.prototype.slice.call(panel.querySelectorAll("[data-sub]"));
  var categoryBtns = Array.prototype.slice.call(panel.querySelectorAll("[data-category]"));
  var count = panel.querySelector(".hub__count");

  // Current selection. primary: all | solo | mp. sub applies only when primary === "mp".
  var primary = "all";
  var sub = "all";
  var category = "all";

  // Does a card's mode list satisfy the active mode filter?
  function matchesMode(modes) {
    if (primary === "all") return true;
    if (primary === "solo") return modes.indexOf("solo") !== -1;
    // primary === "mp"
    if (sub === "local") return modes.indexOf("local") !== -1;
    if (sub === "p2p") return modes.indexOf("p2p") !== -1;
    // sub === "all": any multiplayer mode
    return modes.indexOf("local") !== -1 || modes.indexOf("p2p") !== -1;
  }

  // Does a card's category satisfy the active category filter?
  function matchesCategory(cardCategory) {
    return category === "all" || cardCategory === category;
  }

  function matches(modes, cardCategory) {
    return matchesMode(modes) && matchesCategory(cardCategory);
  }

  function apply() {
    var visible = 0;
    cards.forEach(function (card) {
      var modes = (card.getAttribute("data-modes") || "").split(/\s+/);
      var cardCategory = card.getAttribute("data-category") || "";
      var show = matches(modes, cardCategory);
      if (show) {
        visible++;
        card.classList.remove("card--hidden");
        // Re-trigger the enter animation.
        card.classList.remove("card--enter");
        void card.offsetWidth; // force reflow so the animation restarts
        card.classList.add("card--enter");
      } else {
        card.classList.add("card--hidden");
        card.classList.remove("card--enter");
      }
    });
    if (count) {
      count.textContent =
        visible === cards.length
          ? "Showing all " + cards.length + " games"
          : "Showing " + visible + " of " + cards.length + " games";
    }
  }

  function setPressed(buttons, activeBtn) {
    buttons.forEach(function (b) {
      var on = b === activeBtn;
      b.classList.toggle("is-active", on);
      b.setAttribute("aria-pressed", on ? "true" : "false");
    });
  }

  primaryBtns.forEach(function (btn) {
    btn.addEventListener("click", function () {
      primary = btn.getAttribute("data-filter");
      setPressed(primaryBtns, btn);

      var isMp = primary === "mp";
      if (subRow) {
        subRow.hidden = !isMp;
        var mpBtn = panel.querySelector('[data-filter="mp"]');
        if (mpBtn) mpBtn.setAttribute("aria-expanded", isMp ? "true" : "false");
      }
      // Reset the sub-filter whenever leaving/entering Multiplayer.
      if (!isMp) {
        sub = "all";
        var allSub = panel.querySelector('[data-sub="all"]');
        if (allSub) setPressed(subBtns, allSub);
      }
      apply();
    });
  });

  subBtns.forEach(function (btn) {
    btn.addEventListener("click", function () {
      sub = btn.getAttribute("data-sub");
      setPressed(subBtns, btn);
      // Choosing a connection sub-mode implies Multiplayer: keep the first
      // row in sync so the parent button reflects the active filter.
      if (primary !== "mp") {
        primary = "mp";
        var mpBtn = panel.querySelector('[data-filter="mp"]');
        setPressed(primaryBtns, mpBtn);
        if (subRow) {
          subRow.hidden = false;
          if (mpBtn) mpBtn.setAttribute("aria-expanded", "true");
        }
      }
      apply();
    });
  });

  categoryBtns.forEach(function (btn) {
    btn.addEventListener("click", function () {
      category = btn.getAttribute("data-category");
      setPressed(categoryBtns, btn);
      apply();
    });
  });

  apply();
})();
