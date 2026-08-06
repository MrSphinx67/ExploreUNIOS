// Minimalni toast (zamjena za React Toast). Bez ovisnosti.
(function () {
  const APP = (window.APP = window.APP || {});

  function container() {
    let el = document.getElementById("toasts");
    if (!el) {
      el = document.createElement("div");
      el.id = "toasts";
      el.setAttribute("aria-live", "polite");
      el.setAttribute("aria-atomic", "false");
      document.body.appendChild(el);
    }
    return el;
  }

  function toast(message, kind = "info") {
    const el = document.createElement("div");
    el.className = `toast toast--${kind}`;
    el.setAttribute("role", kind === "error" ? "alert" : "status");
    el.textContent = message;
    container().appendChild(el);

    // izlazna animacija pa uklanjanje
    const remove = () => {
      el.classList.add("toast--out");
      el.addEventListener("transitionend", () => el.remove(), { once: true });
      // sigurnosni fallback ako transitionend ne okine (reduced-motion)
      setTimeout(() => el.remove(), 400);
    };
    setTimeout(remove, kind === "error" ? 4200 : 2800);

    // ulazna animacija (sljedeći frame)
    requestAnimationFrame(() => el.classList.add("toast--in"));
  }

  APP.ui = { toast };
})();
