(() => {
  "use strict";

  // عداد الإحصائيات (إن وجدت data-count-to)
  function animateCount(el, to) {
    const prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (prefersReduced) {
      el.textContent = String(to);
      return;
    }

    const from = 0;
    const duration = 900;
    const start = performance.now();

    function tick(now) {
      const t = Math.min(1, (now - start) / duration);
      const val = Math.floor(from + (to - from) * t);
      el.textContent = String(val);
      if (t < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  }

  const counters = document.querySelectorAll(".count[data-count-to]");
  if (counters.length) {
    const io = new IntersectionObserver(
      (entries, obs) => {
        entries.forEach((e) => {
          if (!e.isIntersecting) return;
          const el = e.target;
          const to = Number(el.getAttribute("data-count-to") || "0");
          animateCount(el, Number.isFinite(to) ? to : 0);
          obs.unobserve(el);
        });
      },
      { threshold: 0.4 }
    );

    counters.forEach((c) => io.observe(c));
  }

  // FAQ: افتح واحد فقط (اختياري، يعطي شكل مرتب)
  const faqs = document.querySelectorAll(".faq details");
  faqs.forEach((d) => {
    d.addEventListener("toggle", () => {
      if (!d.open) return;
      faqs.forEach((other) => {
        if (other !== d) other.removeAttribute("open");
      });
    });
  });
})();


