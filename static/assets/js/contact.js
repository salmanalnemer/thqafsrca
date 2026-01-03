(() => {
  const msg = document.querySelector("textarea");
  const count = document.getElementById("msgCount");
  const btn = document.getElementById("sendBtn");

  const update = () => {
    if (!msg || !count) return;
    count.textContent = String(msg.value.length);
  };

  if (msg) {
    msg.addEventListener("input", update);
    update();
  }

  // UX: منع الضغط المتكرر
  const form = document.querySelector("form.contact-form");
  if (form && btn) {
    form.addEventListener("submit", () => {
      btn.disabled = true;
      btn.textContent = "جاري الإرسال...";
    });
  }
})();
