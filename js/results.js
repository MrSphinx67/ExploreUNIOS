// Rezultati: ukupne brojke + tablica (najranije vs. plan) + ECTS po semestru.
(function () {
  const APP = (window.APP = window.APP || {});

  function el(tag, cls, text) {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }
  const par = (p) => (p === "zimski" ? "Z" : "Lj");

  function totals(schedule) {
    const wrap = el("div", "totals");
    const items = [
      [schedule.totalSemesters, "Semestara"],
      [schedule.totalYears, "Godina"],
      [schedule.totalEcts, "Ukupno ECTS"],
    ];
    for (const [num, label] of items) {
      const s = el("div", "stat");
      s.append(el("span", "stat__num", String(num)), el("span", "stat__label", label));
      wrap.appendChild(s);
    }
    return wrap;
  }

  function table(perCourse) {
    const t = el("table", "ledger");
    const thead = el("thead");
    const hr = el("tr");
    ["Kolegij", "Najranije", "Plan", "ECTS"].forEach((h, i) => {
      const th = el("th", i === 0 ? "" : i === 3 ? "num" : "center", h);
      hr.appendChild(th);
    });
    thead.appendChild(hr);
    t.appendChild(thead);

    const tb = el("tbody");
    for (const c of perCourse) {
      const tr = el("tr");
      const name = el("td", "ledger__name");
      name.append(document.createTextNode(c.naziv));
      if (c.status === "izborni") name.appendChild(el("span", "tag", "izb"));
      tr.appendChild(name);

      const early = el("td", "center mono");
      early.append(el("span", "ledger__sem", `${c.earliest}.`), el("span", "ledger__par", ` ${par(c.parity)}`));
      tr.appendChild(early);

      const plan = el("td", "center mono");
      if (c.earliest < c.plan) {
        plan.append(`${c.plan}.`, el("span", "delta", ` ↓${c.plan - c.earliest}`));
      } else {
        const span = el("span", "muted", `${c.plan}.`);
        plan.appendChild(span);
      }
      tr.appendChild(plan);

      tr.appendChild(el("td", "num mono", String(c.ects)));
      tb.appendChild(tr);
    }
    t.appendChild(tb);
    return t;
  }

  function loadbars(schedule) {
    const wrap = el("div", "loadbars");
    wrap.appendChild(el("h3", "section__title", "ECTS opterećenje po semestru"));
    for (let s = 1; s <= schedule.totalSemesters; s++) {
      const ects = schedule.ectsPerSem[s] || 0;
      const pct = Math.min(100, (ects / 35) * 100);
      const heavy = ects > 30;
      const row = el("div", "loadbar");
      row.appendChild(el("span", "loadbar__label mono", `${s}. sem (${s % 2 === 1 ? "Z" : "Lj"})`));
      const track = el("div", "loadbar__track");
      const fill = el("div", "loadbar__fill" + (heavy ? " is-heavy" : ""));
      fill.style.width = pct + "%";
      if (heavy) fill.title = "Preopterećen semestar (> 30 ECTS)";
      track.appendChild(fill);
      row.appendChild(track);
      row.appendChild(el("span", "loadbar__val mono", `${ects} ECTS`));
      wrap.appendChild(row);
    }
    return wrap;
  }

  function render(mount, schedule) {
    while (mount.firstChild) mount.removeChild(mount.firstChild);
    if (!schedule || !schedule.ok || !schedule.totalSemesters) return; // graf prikazuje grešku/prazno

    mount.appendChild(el("h2", "section__heading", "Najraniji raspored"));
    mount.appendChild(totals(schedule));

    const scroll = el("div", "ledger__scroll");
    scroll.appendChild(table(schedule.perCourse));
    mount.appendChild(scroll);

    mount.appendChild(loadbars(schedule));
  }

  APP.results = { render };
})();
