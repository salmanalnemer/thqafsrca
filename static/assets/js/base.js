(() => {
  "use strict";

  const $id = (id) => document.getElementById(id);
  const $all = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  // =========================
  // Live Time
  // =========================
  function formatLiveArabic(d) {
    const time = new Intl.DateTimeFormat("ar-SA", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: true,
      timeZone: "Asia/Riyadh",
    }).format(d);

    const greg = new Intl.DateTimeFormat("ar-SA-u-ca-gregory", {
      weekday: "long",
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      timeZone: "Asia/Riyadh",
    }).format(d);

    return `الوقت الآن: ${time} | ${greg} م`;
  }

  function initLiveTime() {
    const liveEl = document.querySelector("#liveTime");
    if (!liveEl) return;

    if (document.documentElement.dataset.thqafClockBound === "1") return;
    document.documentElement.dataset.thqafClockBound = "1";

    const update = () => (liveEl.textContent = formatLiveArabic(new Date()));
    update();
    const timer = setInterval(update, 1000);
    window.addEventListener("beforeunload", () => clearInterval(timer));
  }

  // =========================
  // Helpers
  // =========================
  const isInside = (parent, target) => !!(parent && target && parent.contains(target));

  function setAriaExpanded(btn, open) {
    if (!btn) return;
    btn.setAttribute("aria-expanded", open ? "true" : "false");
  }

  // =========================
  // Dropdowns
  // =========================
  let dropdownRegistry = [];

  function closeAllDropdowns() {
    dropdownRegistry.forEach(({ wrap, btn }) => {
      wrap.classList.remove("open");
      setAriaExpanded(btn, false);
    });
  }

  function closeOtherDropdowns(keepWrap) {
    dropdownRegistry.forEach(({ wrap, btn }) => {
      if (wrap !== keepWrap) {
        wrap.classList.remove("open");
        setAriaExpanded(btn, false);
      }
    });
  }

  function setupDropdowns() {
    dropdownRegistry = [];

    const dropdowns = $all(".dropdown");
    dropdowns.forEach((wrap) => {
      const btn = wrap.querySelector(".dropbtn");
      const panel = wrap.querySelector(".dropdown-menu");
      if (!btn || !panel) return;

      dropdownRegistry.push({ wrap, btn, panel });

      btn.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();

        const willOpen = !wrap.classList.contains("open");
        closeOtherDropdowns(wrap);

        wrap.classList.toggle("open", willOpen);
        setAriaExpanded(btn, willOpen);
      });

      // داخل الدروب داون لا يغلق
      panel.addEventListener("click", (e) => e.stopPropagation());
      wrap.addEventListener("click", (e) => e.stopPropagation());
    });

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") closeAllDropdowns();
    });
  }

  // =========================
  // Mobile Menu (FIXED Overlay)
  // =========================
  function ensureOverlay() {
    let overlay = document.querySelector(".menu-overlay");
    if (overlay) return overlay;

    overlay = document.createElement("div");
    overlay.className = "menu-overlay";
    overlay.setAttribute("aria-hidden", "true");
    document.body.appendChild(overlay);
    return overlay;
  }

  function setupMobileMenu() {
    const burger = $id("hamburger");
    const menu = $id("menu");
    if (!burger || !menu) return null;

    const overlay = ensureOverlay();

    const setOpen = (open) => {
      menu.classList.toggle("open", open);
      setAriaExpanded(burger, open);

      overlay.classList.toggle("active", open);
      overlay.setAttribute("aria-hidden", open ? "false" : "true");

      document.body.classList.toggle("menu-lock", open);

      if (!open) closeAllDropdowns();
    };

    const toggle = () => setOpen(!menu.classList.contains("open"));

    burger.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      toggle();
    });

    // ✅ هذا هو المهم: يمنع خروج الضغط للخارج
    menu.addEventListener("click", (e) => e.stopPropagation());

    // الضغط على الـ overlay يقفل
    overlay.addEventListener("click", () => setOpen(false));

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") setOpen(false);
    });

    return { burger, menu, overlay, setOpen };
  }

  // =========================
  // Admin Modal
  // =========================
  function setupAdminModal() {
    const modal = $id("adminModal");
    const openBtn = $id("loginBtn");
    const closeBtn = $id("closeAdminModal");
    const cancelBtn = $id("cancelAdminModal");
    if (!modal || !openBtn) return;

    const open = () => {
      modal.classList.add("active");
      modal.setAttribute("aria-hidden", "false");
      const phone = $id("adminPhone");
      if (phone) phone.focus();
    };

    const close = () => {
      modal.classList.remove("active");
      modal.setAttribute("aria-hidden", "true");
      openBtn.focus();
    };

    openBtn.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      open();
    });

    if (closeBtn) closeBtn.addEventListener("click", close);
    if (cancelBtn) cancelBtn.addEventListener("click", close);

    modal.addEventListener("click", (e) => {
      if (e.target === modal) close();
    });

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && modal.classList.contains("active")) close();
    });

    const submit = $id("adminLoginSubmit");
    if (submit) submit.addEventListener("click", close);
  }

  // =========================
  // Outside Click (desktop dropdown only)
  // =========================
  function setupOutsideClick(mobile) {
    document.addEventListener("click", (e) => {
      const target = e.target;

      const modal = $id("adminModal");
      if (modal && modal.classList.contains("active")) return;

      // إذا السايدبار مفتوح: overlay هو اللي يقفل — لا تدخل هنا
      if (mobile && mobile.menu.classList.contains("open")) return;

      const insideAnyDropdown = dropdownRegistry.some(({ wrap }) => isInside(wrap, target));
      if (!insideAnyDropdown) closeAllDropdowns();
    });
  }

  // =========================
  // DOM Ready
  // =========================
  document.addEventListener("DOMContentLoaded", () => {
    initLiveTime();
    setupDropdowns();
    const mobile = setupMobileMenu();
    setupOutsideClick(mobile);
    setupAdminModal();
  });
})();
