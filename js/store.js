// Pohrana popisa kolegija u localStorage (bez backenda).
(function () {
  const PMF = (window.PMF = window.PMF || {});
  const KEY = "kolegiji_v1";

  function clone(list) {
    return JSON.parse(JSON.stringify(list));
  }

  function load() {
    try {
      const raw = window.localStorage.getItem(KEY);
      if (!raw) return clone(PMF.data.DEFAULT_KOLEGIJI);
      const parsed = JSON.parse(raw);
      if (!Array.isArray(parsed)) return clone(PMF.data.DEFAULT_KOLEGIJI);
      return parsed;
    } catch {
      return clone(PMF.data.DEFAULT_KOLEGIJI);
    }
  }

  function save(list) {
    try {
      window.localStorage.setItem(KEY, JSON.stringify(list));
    } catch {
      // localStorage nedostupan (npr. file://), tiho preskoči.
    }
  }

  function reset() {
    try {
      window.localStorage.removeItem(KEY);
    } catch {
      // ignore
    }
    return clone(PMF.data.DEFAULT_KOLEGIJI);
  }

  // Osnovna validacija oblika uvezenih podataka.
  function normalizeImported(data) {
    // Prihvaćamo i omote: MCP alat vraća kolegije uz popratna polja, a modeli ih rado
    // zapakiraju u još jednu razinu. Bolje raspakirati nego odbiti ispravan popis.
    let node = data;
    for (let i = 0; i < 3 && node && !Array.isArray(node); i++) {
      if (Array.isArray(node.kolegiji)) break;
      const wrapper = ["paste_this", "data", "result", "courses"].find((k) => node[k]);
      if (!wrapper) break;
      node = node[wrapper];
    }
    const list = Array.isArray(node) ? node : Array.isArray(node && node.kolegiji) ? node.kolegiji : null;
    if (!list) {
      const found = data && typeof data === "object" ? Object.keys(data).join(", ") : typeof data;
      throw new Error(
        `Neispravan JSON: očekivan niz kolegija ili { kolegiji: [...] }. Pronađeno: ${found}.`
      );
    }
    return list.map((k) => {
      const item = {
        naziv: String(k.naziv || "").trim(),
        semestar: k.semestar === "ljetni" ? "ljetni" : "zimski",
        godina: Number(k.godina) || 1,
        status: k.status === "izborni" ? "izborni" : "obavezni",
        ects: Number(k.ects) || 0,
        preduvjeti: Array.isArray(k.preduvjeti)
          ? k.preduvjeti.map((p) =>
              typeof p === "string"
                ? { kolegij: p, uvjet: "" }
                : { kolegij: String(p.kolegij || "").trim(), uvjet: p.uvjet || "" }
            )
          : [],
      };
      const pin = Number(k.pin);
      if (Number.isFinite(pin) && pin >= 1) item.pin = pin;
      return item;
    });
  }

  PMF.store = { KEY, load, save, reset, normalizeImported };
})();
