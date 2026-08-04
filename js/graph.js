// Prikaz DAG-a preduvjeta u D3/SVG. Statičan raspored po stupcima (semestrima),
// s godišnjim pojasom na vrhu. Kolegiji bez preduvjeta mogu se povući u kasniji semestar.
(function () {
  const PMF = (window.PMF = window.PMF || {});
  const SVGNS = "http://www.w3.org/2000/svg";
  const XHTML = "http://www.w3.org/1999/xhtml";

  // Geometrija (SVG korisničke jedinice; cijeli se SVG skalira preko CSS-a).
  const CARD_W = 188;
  const CARD_H = 60;
  const COL_GAP = 92;
  const ROW_GAP = 30;
  const PAD_L = 28;
  const PAD_R = 28;
  const PAD_B = 22;
  const YEAR_TOP = 8;
  const YEAR_H = 18;
  const HEAD_TOP = YEAR_TOP + YEAR_H + 10; // = 36
  const HEAD_H = 24;
  const HEAD_GAP = 14;
  const NODES_TOP = HEAD_TOP + HEAD_H + HEAD_GAP; // = 74
  const PORT_GAP = 12;

  function svgEl(tag, attrs) {
    const e = document.createElementNS(SVGNS, tag);
    if (attrs) for (const k in attrs) e.setAttribute(k, attrs[k]);
    return e;
  }
  function htmlEl(tag, cls) {
    const e = document.createElementNS(XHTML, tag);
    if (cls) e.setAttribute("class", cls);
    return e;
  }
  function clear(el) {
    while (el.firstChild) el.removeChild(el.firstChild);
  }
  const parityTag = (s) => (s % 2 === 1 ? "Z" : "Lj");
  const colXof = (s) => PAD_L + (s - 1) * (CARD_W + COL_GAP);

  // Vodoravni kubični brid (isto što i d3.linkHorizontal): kontrolne točke na pola puta.
  function linkPath(x0, y0, x1, y1) {
    const mx = (x0 + x1) / 2;
    return `M${x0},${y0}C${mx},${y0},${mx},${y1},${x1},${y1}`;
  }

  // Suptilna tinta zaglavlja stupca ovisno o dubini semestra.
  function semTint(t) {
    const ink = [0x22, 0x1e, 0x18];
    const sur = [0xf9, 0xf6, 0xf0];
    const f = 0.06 + t * 0.3;
    const c = ink.map((v, i) => Math.round(sur[i] * (1 - f) + v * f));
    return `rgb(${c[0]},${c[1]},${c[2]})`;
  }

  function renderEmpty(mount) {
    const box = document.createElement("div");
    box.className = "graph__note";
    box.textContent = "Nema kolegija za prikaz. Dodaj kolegij u uređivaču.";
    mount.appendChild(box);
  }

  function renderError(mount, message) {
    const box = document.createElement("div");
    box.className = "callout callout--error";
    const h = document.createElement("h3");
    h.className = "callout__title";
    h.textContent = "Ne mogu izračunati raspored";
    const p = document.createElement("p");
    p.className = "callout__body";
    p.textContent = message || "Provjeri preduvjete i semestre kolegija.";
    box.append(h, p);
    mount.appendChild(box);
  }

  function layout(schedule, courses) {
    const bySem = new Map();
    for (const k of courses) {
      const s = schedule.earliest.get(k.naziv);
      if (!bySem.has(s)) bySem.set(s, []);
      bySem.get(s).push(k.naziv);
    }
    const statusOf = new Map(courses.map((k) => [k.naziv, k.status || ""]));
    const ectsOf = new Map(courses.map((k) => [k.naziv, Number(k.ects) || 0]));

    const pos = {};
    let maxRows = 0;
    const total = schedule.totalSemesters;
    for (let s = 1; s <= total; s++) {
      const names = (bySem.get(s) || []).slice().sort((a, b) => a.localeCompare(b, "hr"));
      maxRows = Math.max(maxRows, names.length);
      const colX = colXof(s);
      names.forEach((n, i) => {
        const y = NODES_TOP + i * (CARD_H + ROW_GAP);
        pos[n] = { x: colX, y, cy: y + CARD_H / 2, sem: s, status: statusOf.get(n) || "", ects: ectsOf.get(n) || 0 };
      });
    }
    const width = PAD_L + total * (CARD_W + COL_GAP) - COL_GAP + PAD_R;
    const height = NODES_TOP + maxRows * (CARD_H + ROW_GAP) - ROW_GAP + PAD_B;
    return { pos, width, height, total };
  }

  function render(mount, schedule, courses, opts) {
    clear(mount);
    if (!schedule || !schedule.ok) return renderError(mount, schedule && schedule.error);
    if (!schedule.totalSemesters) return renderEmpty(mount);

    const onPin = opts && opts.onPin;
    const { pos, width, height, total } = layout(schedule, courses);

    const svg = svgEl("svg", {
      class: "graph__svg",
      width: String(width),
      height: String(height),
      viewBox: `0 0 ${width} ${height}`,
      preserveAspectRatio: "xMidYMid meet",
      role: "img",
      "aria-label": "Graf preduvjeta kolegija po semestrima i godinama",
    });

    const defs = svgEl("defs");
    const marker = svgEl("marker", {
      id: "pmf-arrow", viewBox: "0 0 8 8", refX: "7.5", refY: "4",
      markerWidth: "8", markerHeight: "8", markerUnits: "userSpaceOnUse", orient: "auto",
    });
    marker.appendChild(svgEl("path", { d: "M0,0 L8,4 L0,8 Z", class: "graph__arrow" }));
    defs.appendChild(marker);
    svg.appendChild(defs);

    // ── godišnji pojas (grupira semestre u godine) ──
    const gYears = svgEl("g", { class: "graph__years" });
    const groups = [];
    for (let s = 1; s <= total; s++) {
      const y = Math.ceil(s / 2);
      const last = groups[groups.length - 1];
      if (!last || last.year !== y) groups.push({ year: y, first: s, last: s });
      else last.last = s;
    }
    const ruleY = YEAR_TOP + YEAR_H;
    for (const g of groups) {
      const x0 = colXof(g.first);
      const x1 = colXof(g.last) + CARD_W;
      gYears.appendChild(svgEl("line", { x1: x0, y1: ruleY, x2: x1, y2: ruleY, class: "graph__year-rule" }));
      gYears.appendChild(svgEl("line", { x1: x0, y1: ruleY, x2: x0, y2: ruleY + 4, class: "graph__year-rule" }));
      gYears.appendChild(svgEl("line", { x1: x1, y1: ruleY, x2: x1, y2: ruleY + 4, class: "graph__year-rule" }));
      const label = svgEl("text", { x: (x0 + x1) / 2, y: YEAR_TOP + 6, "text-anchor": "middle", "dominant-baseline": "hanging", class: "graph__year-label" });
      label.textContent = `${g.year}. godina`;
      gYears.appendChild(label);
    }
    svg.appendChild(gYears);

    // ── zaglavlja stupaca (semestri) ──
    const gHeads = svgEl("g", { class: "graph__heads" });
    for (let s = 1; s <= total; s++) {
      const colX = colXof(s);
      const t = total > 1 ? (s - 1) / (total - 1) : 0;
      gHeads.appendChild(svgEl("rect", { x: colX, y: HEAD_TOP, width: CARD_W, height: HEAD_H, rx: 3, fill: semTint(t) }));
      const cy = HEAD_TOP + HEAD_H / 2;
      const numT = svgEl("text", { x: colX + 10, y: cy, "dominant-baseline": "central", class: "graph__head-sem" });
      numT.textContent = s + ".";
      const parT = svgEl("text", { x: colX + CARD_W - 10, y: cy, "text-anchor": "end", "dominant-baseline": "central", class: "graph__head-par" });
      parT.textContent = parityTag(s);
      gHeads.append(numT, parT);
    }
    svg.appendChild(gHeads);

    const gTargets = svgEl("g", { class: "graph__targets" });
    const gEdges = svgEl("g", { class: "graph__edges" });
    const gNodes = svgEl("g", { class: "graph__nodes" });
    svg.append(gTargets, gEdges, gNodes);

    // ── port fan-out ──
    const outIdx = new Map();
    const inIdx = new Map();
    for (const e of schedule.edges) {
      if (!pos[e.source] || !pos[e.target]) continue;
      if (!outIdx.has(e.source)) outIdx.set(e.source, []);
      if (!inIdx.has(e.target)) inIdx.set(e.target, []);
      outIdx.get(e.source).push(e);
      inIdx.get(e.target).push(e);
    }
    outIdx.forEach((arr) => arr.sort((a, b) => pos[a.target].cy - pos[b.target].cy));
    inIdx.forEach((arr) => arr.sort((a, b) => pos[a.source].cy - pos[b.source].cy));

    const nodeEls = new Map();
    const edgeInfos = []; // { el, s, t }
    const maxPort = CARD_H / 2 - 8;
    const clampPort = (v) => Math.max(-maxPort, Math.min(maxPort, v));

    for (const e of schedule.edges) {
      const S = pos[e.source];
      const T = pos[e.target];
      if (!S || !T) continue;
      const outs = outIdx.get(e.source);
      const ins = inIdx.get(e.target);
      const sPort = clampPort((outs.indexOf(e) - (outs.length - 1) / 2) * PORT_GAP);
      const tPort = clampPort((ins.indexOf(e) - (ins.length - 1) / 2) * PORT_GAP);
      const d = linkPath(S.x + CARD_W, S.cy + sPort, T.x - 2.5, T.cy + tPort);
      const path = svgEl("path", { class: "edge", d, "marker-end": "url(#pmf-arrow)" });
      gEdges.appendChild(path);
      edgeInfos.push({ el: path, s: e.source, t: e.target });
    }

    // koji kolegiji nemaju preduvjete (samo se oni mogu povlačiti)
    const noPrereq = new Set(courses.filter((k) => PMF.schedule.prereqNames(k).length === 0).map((k) => k.naziv));

    // ── čvorovi (kartice) ──
    for (const k of courses) {
      const p = pos[k.naziv];
      if (!p) continue;
      const fo = svgEl("foreignObject", { x: String(p.x), y: String(p.y), width: String(CARD_W), height: String(CARD_H) });
      const draggable = onPin && noPrereq.has(k.naziv);
      const card = htmlEl("div", "node" + (p.status === "izborni" ? " node--izborni" : "") + (draggable ? " node--draggable" : ""));
      card.setAttribute("data-naziv", k.naziv);
      if (draggable) card.setAttribute("title", "Povuci u kasniji semestar (ili natrag za automatski)");
      const name = htmlEl("span", "node__name");
      name.textContent = k.naziv;
      const meta = htmlEl("span", "node__meta");
      meta.textContent = `${p.sem}. · ${p.ects} ECTS · ${parityTag(p.sem)}`;
      card.append(name, meta);
      fo.appendChild(card);
      gNodes.appendChild(fo);
      nodeEls.set(k.naziv, card);

      card.addEventListener("mouseenter", () => setHot(k.naziv, true));
      card.addEventListener("mouseleave", () => setHot(k.naziv, false));
      if (draggable) enableDrag(fo, card, k, p);
    }

    // Hover: istakni put (kolegij + svi njegovi preduvjeti i ovisnici), zatamni ostalo.
    function setHot(naziv, on) {
      if (!on) {
        svg.classList.remove("has-hover");
        for (const el of nodeEls.values()) el.classList.remove("node--hot", "node--adj", "node--dim");
        for (const ei of edgeInfos) ei.el.classList.remove("edge--hot", "edge--dim");
        return;
      }
      // Ističemo samo preduvjete (uzvodni lanac), ne i kolegije koji ovise o ovome (nizvodno).
      const chain = new Set([naziv]);
      PMF.schedule.ancestorsOf(naziv, courses).forEach((n) => chain.add(n));
      svg.classList.add("has-hover");
      for (const [n, el] of nodeEls) {
        const inChain = chain.has(n);
        el.classList.toggle("node--dim", !inChain);
        el.classList.toggle("node--hot", n === naziv);
        el.classList.toggle("node--adj", inChain && n !== naziv);
      }
      for (const ei of edgeInfos) {
        // Cijeli lanac preduvjeta/ovisnika (i posredni) se ističe, ne samo izravni bridovi, // tako se vidi da su npr. Opća i Organska kemija (preko Biokemije) preduvjeti Mol. genetike.
        const inChain = chain.has(ei.s) && chain.has(ei.t);
        ei.el.classList.toggle("edge--hot", inChain);
        ei.el.classList.toggle("edge--dim", !inChain);
      }
    }

    // ── povlačenje (drag) kolegija bez preduvjeta u drugi semestar ──
    const svgScale = () => {
      const r = svg.getBoundingClientRect();
      return r.width ? width / r.width : 1;
    };
    // Samo semestri u sezoni kolegija: ljetni kolegij ne može u neparni semestar.
    function validColumns(base, course) {
      const wantOdd = course.semestar !== "ljetni";
      const cols = [];
      for (let s = base; s <= total; s++) {
        if ((s % 2 === 1) === wantOdd) cols.push({ sem: s, cx: colXof(s) + CARD_W / 2 });
      }
      return cols;
    }
    function nearestColumn(centerX, cols) {
      let best = cols[0];
      for (const c of cols) if (Math.abs(c.cx - centerX) < Math.abs(best.cx - centerX)) best = c;
      return best;
    }

    function enableDrag(fo, card, course, p) {
      // Kolegij bez preduvjeta: najraniji mu je prvi semestar njegove sezone.
      const base = course.semestar === "ljetni" ? 2 : 1;
      let dragging = false, startX = 0, startY = 0, cols = [];

      const showTargets = () => {
        clear(gTargets);
        const top = NODES_TOP - 8;
        const h = height - top - PAD_B + 8;
        for (const c of cols) {
          const r = svgEl("rect", { x: colXof(c.sem) - 8, y: top, width: CARD_W + 16, height: h, rx: 6, class: "target" });
          r.setAttribute("data-sem", String(c.sem));
          gTargets.appendChild(r);
        }
      };
      const markNearest = (centerX) => {
        const t = nearestColumn(centerX, cols);
        for (const r of gTargets.children) r.classList.toggle("target--on", Number(r.getAttribute("data-sem")) === t.sem);
      };

      card.addEventListener("pointerdown", (ev) => {
        if (ev.button != null && ev.button !== 0) return;
        ev.preventDefault();
        dragging = true;
        startX = ev.clientX;
        startY = ev.clientY;
        cols = validColumns(base, course);
        try { card.setPointerCapture(ev.pointerId); } catch (e) {}
        card.classList.add("node--dragging");
        svg.classList.add("is-dragging");
        gNodes.appendChild(fo); // podigni iznad ostalih
        showTargets();
        markNearest(p.x + CARD_W / 2);
      });
      card.addEventListener("pointermove", (ev) => {
        if (!dragging) return;
        const sc = svgScale();
        const nx = p.x + (ev.clientX - startX) * sc;
        const ny = p.y + (ev.clientY - startY) * sc;
        fo.setAttribute("x", String(nx));
        fo.setAttribute("y", String(ny));
        markNearest(nx + CARD_W / 2);
      });
      const end = (ev) => {
        if (!dragging) return;
        dragging = false;
        card.classList.remove("node--dragging");
        svg.classList.remove("is-dragging");
        clear(gTargets);
        const sc = svgScale();
        const nx = p.x + (ev.clientX - startX) * sc;
        const target = nearestColumn(nx + CARD_W / 2, cols);
        onPin(course.naziv, target.sem <= base ? null : target.sem);
      };
      card.addEventListener("pointerup", end);
      card.addEventListener("pointercancel", end);
    }

    mount.appendChild(svg);
  }

  PMF.graph = { render };
})();
