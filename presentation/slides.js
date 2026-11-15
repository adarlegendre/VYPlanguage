(() => {
  const slides = Array.from(document.querySelectorAll(".slide"));
  const prevBtn = document.getElementById("prev");
  const nextBtn = document.getElementById("next");
  const progress = document.getElementById("progress");
  const total = slides.length;
  let index = Math.max(
    0,
    slides.findIndex((s) => s.classList.contains("is-active")),
  );
  if (index < 0) index = 0;

  slides.forEach((slide, n) => {
    const el = slide.querySelector(".pageno");
    if (el) el.textContent = `${n + 1}/${total}`;
  });

  function show(i) {
    index = Math.max(0, Math.min(total - 1, i));
    slides.forEach((slide, n) => {
      slide.classList.toggle("is-active", n === index);
    });
    if (progress) progress.textContent = `${index + 1} / ${total}`;
    if (prevBtn) prevBtn.disabled = index === 0;
    if (nextBtn) nextBtn.disabled = index === total - 1;
    const title = slides[index]?.dataset.title || "Slide";
    document.title = `VYPa — Parser · ${title}`;
    history.replaceState(null, "", `#${index + 1}`);
  }

  function fromHash() {
    const n = Number.parseInt(location.hash.replace("#", ""), 10);
    if (Number.isFinite(n) && n >= 1 && n <= total) show(n - 1);
    else show(index);
  }

  prevBtn?.addEventListener("click", () => show(index - 1));
  nextBtn?.addEventListener("click", () => show(index + 1));

  window.addEventListener("keydown", (e) => {
    const tag = (e.target && e.target.tagName) || "";
    if (tag === "INPUT" || tag === "TEXTAREA") return;
    if (e.key === "ArrowRight" || e.key === " " || e.key === "PageDown") {
      e.preventDefault();
      show(index + 1);
    } else if (e.key === "ArrowLeft" || e.key === "PageUp") {
      e.preventDefault();
      show(index - 1);
    } else if (e.key === "Home") {
      e.preventDefault();
      show(0);
    } else if (e.key === "End") {
      e.preventDefault();
      show(total - 1);
    } else if (e.key === "p" || e.key === "P") {
      window.print();
    }
  });

  window.addEventListener("hashchange", fromHash);
  fromHash();
})();
