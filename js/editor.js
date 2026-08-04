// Uređivač kolegija, čisti DOM + delegacija događaja. Bez okvira.
// Uređivanje vrijednosti NE ruši DOM (fokus/kursor ostaju); strukturne promjene ga grade nanovo.
(function () {
  const PMF = (window.PMF = window.PMF || {});

  let openSet = new Set(); // indeksi otvorenih kartica (preživi strukturne rebuild-ove)

  function el(tag, cls, text) {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }

  function select(field, options, value, extra) {
    const s = el("select");
    s.dataset.field = field;
    if (extra && extra.placeholder != null) {
      const o = el("option", null, extra.placeholder);
      o.value = "";
      s.appendChild(o);
    }
    for (const opt of options) {
      const o = el("option", null, opt);
      o.value = opt;
      s.appendChild(o);
    }
    // sačuvaj postojeću (nepostojeću) referencu kao vlastitu opciju
    if (value && !options.includes(value)) {
      const o = el("option", null, `${value} (nepostojeći)`);
      o.value = value;
      s.appendChild(o);
    }
    s.value = value || "";
    return s;
  }

  function labeled(labelText, control) {
    const l = el("label", "field");
    l.append(el("span", "field__label", labelText), control);
    return l;
  }

  function summaryMeta(c) {
    const n = (c.preduvjeti || []).length;
    const par = c.semestar === "zimski" ? "Z" : "Lj";
    return `${par} · ${c.godina}. god · ${c.ects} ECTS` + (n ? ` · ${n} pred.` : "");
  }

  function refreshSummary(courseEl) {
    const q = (sel) => courseEl.querySelector(sel);
    const naziv = q('input[data-field="naziv"]').value.trim();
    const sem = q('select[data-field="semestar"]').value;
    const god = q('input[data-field="godina"]').value;
    const ects = q('input[data-field="ects"]').value;
    const npred = courseEl.querySelectorAll(".prereq").length;
    const nameEl = q(".course__name");
    nameEl.textContent = naziv || "Bez naziva";
    nameEl.classList.toggle("is-empty", !naziv);
    q(".course__meta").textContent =
      `${sem === "zimski" ? "Z" : "Lj"} · ${god}. god · ${ects} ECTS` + (npred ? ` · ${npred} pred.` : "");
  }

  function courseNode(c, i, courses) {
    const otherNames = courses.filter((_, idx) => idx !== i).map((x) => x.naziv).filter(Boolean);

    const details = el("details", "course");
    details.dataset.idx = String(i);
    if (openSet.has(i)) details.open = true;

    // ── summary ──
    const summary = el("summary", "course__summary");
    const name = el("span", "course__name", c.naziv || "Bez naziva");
    if (!c.naziv) name.classList.add("is-empty");
    const meta = el("span", "course__meta mono", summaryMeta(c));
    const del = el("button", "icon-btn course__del", "✕");
    del.type = "button";
    del.dataset.action = "remove-course";
    del.setAttribute("aria-label", `Obriši kolegij ${c.naziv || ""}`.trim());
    summary.append(el("span", "course__chevron", "›"), name, meta, del);
    details.appendChild(summary);

    // ── body ──
    const body = el("div", "course__body");

    const naziv = el("input");
    naziv.type = "text";
    naziv.dataset.field = "naziv";
    naziv.value = c.naziv;
    naziv.placeholder = "Naziv kolegija";
    body.appendChild(labeled("Naziv", naziv));

    const grid = el("div", "field-grid");
    grid.appendChild(labeled("Semestar", select("semestar", PMF.data.SEMESTRI, c.semestar)));
    const god = el("input");
    god.type = "number";
    god.min = "1";
    god.dataset.field = "godina";
    god.value = c.godina;
    grid.appendChild(labeled("Godina", god));
    grid.appendChild(labeled("Status", select("status", PMF.data.STATUSI, c.status)));
    const ects = el("input");
    ects.type = "number";
    ects.min = "0";
    ects.dataset.field = "ects";
    ects.value = c.ects;
    grid.appendChild(labeled("ECTS", ects));
    body.appendChild(grid);

    // ── preduvjeti ──
    const pre = el("div", "prereqs");
    const head = el("div", "prereqs__head");
    head.append(el("span", "field__label", "Preduvjeti"));
    const addBtn = el("button", "link-btn", "+ dodaj preduvjet");
    addBtn.type = "button";
    addBtn.dataset.action = "add-prereq";
    head.appendChild(addBtn);
    pre.appendChild(head);

    const list = c.preduvjeti || [];
    if (list.length === 0) {
      pre.appendChild(el("p", "prereqs__empty", "Nema preduvjeta."));
    }
    list.forEach((pr, pi) => {
      const val = typeof pr === "string" ? { kolegij: pr, uvjet: "" } : pr;
      const row = el("div", "prereq");
      row.dataset.pi = String(pi);
      const ks = select("prereq-kolegij", otherNames, val.kolegij, { placeholder: ", odaberi, " });
      ks.classList.add("prereq__kolegij");
      const us = select("prereq-uvjet", PMF.data.UVJETI, val.uvjet || "polozen");
      us.classList.add("prereq__uvjet");
      const rm = el("button", "icon-btn", "✕");
      rm.type = "button";
      rm.dataset.action = "remove-prereq";
      rm.setAttribute("aria-label", "Ukloni preduvjet");
      row.append(ks, us, rm);
      pre.appendChild(row);
    });

    body.appendChild(pre);
    details.appendChild(body);

    details.addEventListener("toggle", () => {
      if (details.open) openSet.add(i);
      else openSet.delete(i);
    });

    return details;
  }

  function render(mount, courses, handlers, opts) {
    if (opts && opts.resetOpen) openSet = new Set();
    if (opts && opts.openIndex != null) openSet.add(opts.openIndex);

    // odbaci indekse izvan dosega (nakon brisanja)
    openSet = new Set([...openSet].filter((i) => i < courses.length));

    while (mount.firstChild) mount.removeChild(mount.firstChild);

    const listEl = el("div", "courses");
    courses.forEach((c, i) => listEl.appendChild(courseNode(c, i, courses)));
    mount.appendChild(listEl);

    const add = el("button", "add-course", "+ Dodaj kolegij");
    add.type = "button";
    add.dataset.action = "add-course";
    mount.appendChild(add);

    if (mount.__wired) return; // delegacija se veže samo jednom
    mount.__wired = true;

    const idxOf = (target) => Number(target.closest(".course").dataset.idx);
    const piOf = (target) => Number(target.closest(".prereq").dataset.pi);

    mount.addEventListener("click", (e) => {
      const btn = e.target.closest("[data-action]");
      if (!btn || !mount.contains(btn)) return;
      const action = btn.dataset.action;
      if (action === "add-course") return handlers.addCourse();
      // spriječi da klik unutar <summary> preklopi <details>
      e.preventDefault();
      if (action === "remove-course") handlers.removeCourse(idxOf(btn));
      else if (action === "add-prereq") handlers.addPrereq(idxOf(btn));
      else if (action === "remove-prereq") handlers.removePrereq(idxOf(btn), piOf(btn));
    });

    mount.addEventListener("input", (e) => {
      const inp = e.target.closest("input[data-field]");
      if (!inp) return;
      const courseEl = inp.closest(".course");
      const i = Number(courseEl.dataset.idx);
      const f = inp.dataset.field;
      let patch;
      if (f === "naziv") patch = { naziv: inp.value };
      else if (f === "godina") patch = { godina: Number(inp.value) || 1 };
      else if (f === "ects") patch = { ects: Number(inp.value) || 0 };
      else return;
      refreshSummary(courseEl);
      handlers.onValueEdit(i, patch);
    });

    mount.addEventListener("change", (e) => {
      const sel = e.target.closest("select[data-field]");
      if (!sel) return;
      const courseEl = sel.closest(".course");
      const i = Number(courseEl.dataset.idx);
      const f = sel.dataset.field;
      if (f === "semestar") {
        handlers.onValueEdit(i, { semestar: sel.value });
        refreshSummary(courseEl);
      } else if (f === "status") {
        handlers.onValueEdit(i, { status: sel.value });
      } else if (f === "prereq-kolegij") {
        handlers.onPrereqValueEdit(i, piOf(sel), { kolegij: sel.value });
      } else if (f === "prereq-uvjet") {
        handlers.onPrereqValueEdit(i, piOf(sel), { uvjet: sel.value });
      }
    });
  }

  PMF.editor = { render };
})();
