// Bootstrap: jedinstveno stanje, orkestracija prikaza, alatna traka. Učitava se zadnji.
(function () {
  const PMF = (window.PMF = window.PMF || {});

  const state = { courses: [] };

  const $ = (id) => document.getElementById(id);
  let editorEl, graphEl, resultsEl, countEl;

  const emptyCourse = () => ({
    naziv: "",
    semestar: "zimski",
    godina: 1,
    status: "obavezni",
    ects: 0,
    preduvjeti: [],
  });

  function save() {
    PMF.store.save(state.courses);
  }

  function renderDerived() {
    const schedule = PMF.schedule.computeSchedule(state.courses);
    PMF.graph.render(graphEl, schedule, state.courses, { onPin });
    PMF.results.render(resultsEl, schedule);
    if (countEl) countEl.textContent = String(state.courses.length);
  }

  // Fiksiraj kolegij (bez preduvjeta) u zadani semestar; sem == null => automatski (najraniji).
  function onPin(naziv, sem) {
    const i = state.courses.findIndex((c) => c.naziv === naziv);
    if (i < 0) return;
    if (sem == null) {
      const next = { ...state.courses[i] };
      delete next.pin;
      state.courses[i] = next;
    } else {
      state.courses[i] = { ...state.courses[i], pin: sem };
    }
    save();
    renderDerived();
  }

  // Sažmi više izmjena vrijednosti unutar jednog frame-a (npr. tipkanje naziva).
  let rafPending = false;
  function scheduleDerived() {
    if (rafPending) return;
    rafPending = true;
    requestAnimationFrame(() => {
      rafPending = false;
      renderDerived();
    });
  }

  function rebuildEditor(opts) {
    PMF.editor.render(editorEl, state.courses, handlers, opts);
  }

  const handlers = {
    // izmjena vrijednosti polja, ne rušimo uređivač (fokus ostaje)
    onValueEdit(i, patch) {
      state.courses[i] = { ...state.courses[i], ...patch };
      save();
      scheduleDerived();
    },
    onPrereqValueEdit(i, pi, patch) {
      const c = state.courses[i];
      const list = (c.preduvjeti || []).map((pr, idx) => {
        const base = typeof pr === "string" ? { kolegij: pr, uvjet: "" } : pr;
        return idx === pi ? { ...base, ...patch } : base;
      });
      state.courses[i] = { ...c, preduvjeti: list };
      save();
      scheduleDerived();
    },

    // strukturne promjene, grade uređivač nanovo
    addCourse() {
      state.courses = [...state.courses, emptyCourse()];
      save();
      rebuildEditor({ openIndex: state.courses.length - 1 });
      renderDerived();
    },
    removeCourse(i) {
      state.courses = state.courses.filter((_, idx) => idx !== i);
      save();
      rebuildEditor();
      renderDerived();
    },
    addPrereq(i) {
      const c = state.courses[i];
      const options = state.courses.filter((_, idx) => idx !== i).map((x) => x.naziv).filter(Boolean);
      const already = new Set((c.preduvjeti || []).map((p) => (typeof p === "string" ? p : p.kolegij)));
      const first = options.find((o) => !already.has(o)) || "";
      state.courses[i] = { ...c, preduvjeti: [...(c.preduvjeti || []), { kolegij: first, uvjet: "polozen" }] };
      save();
      rebuildEditor();
      renderDerived();
    },
    removePrereq(i, pi) {
      const c = state.courses[i];
      state.courses[i] = { ...c, preduvjeti: (c.preduvjeti || []).filter((_, idx) => idx !== pi) };
      save();
      rebuildEditor();
      renderDerived();
    },
  };

  // ── alatna traka ──
  function doExport() {
    const blob = new Blob([JSON.stringify({ kolegiji: state.courses }, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "kolegiji.json";
    a.click();
    URL.revokeObjectURL(url);
  }

  // Zajednički put za uvoz iz datoteke i iz zalijepljenog teksta.
  function loadFromText(text) {
    const list = PMF.store.normalizeImported(JSON.parse(text));
    state.courses = list;
    save();
    rebuildEditor({ resetOpen: true });
    renderDerived();
    PMF.ui.toast(`Uvezeno ${list.length} kolegija.`, "success");
  }

  async function doImport(file, inputEl) {
    try {
      loadFromText(await file.text());
    } catch (err) {
      PMF.ui.toast(`Greška pri uvozu: ${err.message}`, "error");
    } finally {
      if (inputEl) inputEl.value = "";
    }
  }

  function togglePaste(show) {
    const box = $("paste-box");
    box.hidden = !show;
    if (show) $("paste-json").focus();
    else $("paste-json").value = "";
  }

  function doPaste() {
    const raw = $("paste-json").value.trim();
    if (!raw) return PMF.ui.toast("Prazno polje: zalijepi JSON.", "error");
    try {
      loadFromText(raw);
      togglePaste(false);
    } catch (err) {
      PMF.ui.toast(`Greška pri uvozu: ${err.message}`, "error");
    }
  }

  function doReset() {
    state.courses = PMF.store.reset();
    rebuildEditor({ resetOpen: true });
    renderDerived();
    PMF.ui.toast("Vraćeno na zadani popis.", "info");
  }

  function wireToolbar() {
    $("btn-export").addEventListener("click", doExport);
    const fileInput = $("file-import");
    $("btn-import").addEventListener("click", () => fileInput.click());
    fileInput.addEventListener("change", (e) => {
      const file = e.target.files && e.target.files[0];
      if (file) doImport(file, fileInput);
    });
    $("btn-paste").addEventListener("click", () => togglePaste($("paste-box").hidden));
    $("btn-paste-load").addEventListener("click", doPaste);
    $("btn-paste-cancel").addEventListener("click", () => togglePaste(false));
    $("paste-json").addEventListener("keydown", (e) => {
      if (e.key === "Escape") togglePaste(false);
      if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) doPaste();
    });
    $("btn-reset").addEventListener("click", doReset);
  }

  function boot() {
    editorEl = $("editor");
    graphEl = $("graph");
    resultsEl = $("results");
    countEl = $("course-count");

    state.courses = PMF.store.load();
    rebuildEditor();
    renderDerived();
    wireToolbar();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
