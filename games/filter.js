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
  var searchInput = document.getElementById("game-search");

  // Current selection. primary: all | solo | mp. sub applies only when primary === "mp".
  var primary = "all";
  var sub = "all";
  var category = "all";
  var search = "";

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

  // Does a card's title satisfy the active search text (case-insensitive substring)?
  function matchesSearch(title) {
    return search === "" || title.toLowerCase().indexOf(search) !== -1;
  }

  function matches(modes, cardCategory, title) {
    return matchesMode(modes) && matchesCategory(cardCategory) && matchesSearch(title);
  }

  function apply() {
    var visible = 0;
    cards.forEach(function (card) {
      var modes = (card.getAttribute("data-modes") || "").split(/\s+/);
      var cardCategory = card.getAttribute("data-category") || "";
      var titleEl = card.querySelector(".card__title");
      var title = titleEl ? titleEl.textContent : "";
      var show = matches(modes, cardCategory, title);
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

  if (searchInput) {
    searchInput.addEventListener("input", function () {
      search = searchInput.value.trim().toLowerCase();
      apply();
    });
  }

  // Sort control: A-Z (document order, cached once) vs newest-added-first.
  var sortSelect = document.getElementById("sort-select");
  var originalOrder = cards.slice();

  function sortCards(mode) {
    var ordered;
    if (mode === "newest") {
      ordered = cards.slice().sort(function (a, b) {
        var da = a.getAttribute("data-added") || "";
        var db = b.getAttribute("data-added") || "";
        if (da === db) return 0;
        return da < db ? 1 : -1; // descending: newest first
      });
    } else {
      ordered = originalOrder;
    }
    ordered.forEach(function (card) {
      grid.appendChild(card);
    });
  }

  if (sortSelect) {
    sortSelect.addEventListener("change", function () {
      sortCards(sortSelect.value);
      apply(); // reapply hidden state + re-trigger enter animation in new order
    });
    // Browsers restore a <select>'s value from history on back/forward
    // navigation without firing "change" — and they do it after
    // DOMContentLoaded, via "pageshow", so the dropdown can end up showing
    // "Newest first" while the grid is still in its default order. Re-sync
    // whenever the page becomes visible (covers both bfcache restores and
    // plain reloads where the browser reapplies the remembered value).
    window.addEventListener("pageshow", function () {
      sortCards(sortSelect.value);
      apply();
    });
  }

  // Mark cards added within the last 14 days as NEW. Computed once at load;
  // does not change as filters/sort are toggled.
  var NEW_WINDOW_DAYS = 14;
  function markNewBadges() {
    var now = Date.now();
    cards.forEach(function (card) {
      var added = card.getAttribute("data-added");
      if (!added) return;
      var addedTime = new Date(added + "T00:00:00Z").getTime();
      if (isNaN(addedTime)) return;
      var ageDays = (now - addedTime) / (1000 * 60 * 60 * 24);
      if (ageDays > NEW_WINDOW_DAYS) return;
      if (card.querySelector(".badge--new")) return;
      var badge = document.createElement("span");
      badge.className = "badge badge--new";
      badge.textContent = "NEW";
      card.insertBefore(badge, card.firstChild);
    });
  }
  markNewBadges();

  apply();
})();
