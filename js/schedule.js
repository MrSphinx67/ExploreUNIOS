// Logika rasporeda kolegija, čisti JS, radi u pregledniku (bez backenda).
// Port skripte kolegiji_dag/raspored.py (model "compress": lanac preduvjeta + sezona).
(function () {
  const PMF = (window.PMF = window.PMF || {});

  function prereqList(course) {
    return (course.preduvjeti || []).map((p) =>
      typeof p === "string" ? { kolegij: p, uvjet: "" } : { kolegij: p.kolegij, uvjet: p.uvjet || "" }
    );
  }

  function prereqNames(course) {
    return prereqList(course).map((p) => p.kolegij);
  }

  // Semestar prema službenom planu (iz godine + pariteta).
  function nominalSemester(course) {
    const g = Number(course.godina) || 1;
    return course.semestar === "zimski" ? 2 * g - 1 : 2 * g;
  }

  function semParity(sem) {
    return sem % 2 === 1 ? "zimski" : "ljetni";
  }

  // Prvi semestar >= sem koji je u sezoni kolegija. Kolegij se izvodi samo u svojoj
  // sezoni, pa ga nema smisla smjestiti u semestar suprotnog pariteta.
  function matchSeason(sem, course) {
    return semParity(sem) === (course.semestar === "zimski" ? "zimski" : "ljetni")
      ? sem
      : sem + 1;
  }

  function fail(error) {
    return { ok: false, error };
  }

  // Prazan, ali valjan rezultat (npr. kad nema kolegija), da UI ne dobije -Infinity.
  function emptyOk() {
    return {
      ok: true,
      earliest: new Map(),
      nodes: [],
      edges: [],
      perCourse: [],
      totalSemesters: 0,
      totalYears: 0,
      ectsPerSem: {},
      totalEcts: 0,
    };
  }

  // Izračunaj DAG + najraniji raspored (dubina lanca preduvjeta + sezona kolegija).
  function computeSchedule(courses) {
    if (!Array.isArray(courses) || courses.length === 0) return emptyOk();

    const byName = new Map();
    for (const k of courses) {
      const naziv = (k.naziv || "").trim();
      if (!naziv) return fail("Postoji kolegij bez naziva.");
      if (byName.has(naziv)) return fail(`Dvostruki kolegij: "${naziv}".`);
      if (k.semestar !== "zimski" && k.semestar !== "ljetni")
        return fail(`"${naziv}": semestar mora biti "zimski" ili "ljetni".`);
      byName.set(naziv, k);
    }

    // provjeri preduvjete
    for (const k of courses) {
      for (const pn of prereqNames(k)) {
        if (pn === k.naziv) return fail(`"${k.naziv}": kolegij ne može biti sam sebi preduvjet.`);
        if (!byName.has(pn)) return fail(`"${k.naziv}": nepoznat preduvjet "${pn}".`);
      }
    }

    // detekcija ciklusa + najraniji semestar (DFS s bojama)
    const WHITE = 0, GRAY = 1, BLACK = 2;
    const color = new Map();
    courses.forEach((k) => color.set(k.naziv, WHITE));
    const earliest = new Map();
    const stack = [];
    let cycleError = null;

    function dfs(name) {
      color.set(name, GRAY);
      stack.push(name);
      let m = 0;
      for (const pn of prereqNames(byName.get(name))) {
        if (color.get(pn) === GRAY) {
          const idx = stack.indexOf(pn);
          cycleError = "Ciklus u preduvjetima: " + stack.slice(idx).concat(pn).join(" → ");
          throw new Error("cycle");
        }
        if (color.get(pn) === WHITE) dfs(pn);
        m = Math.max(m, earliest.get(pn));
      }
      const cur = byName.get(name);
      // Prvi semestar nakon svih (i posrednih) preduvjeta, ali samo u svojoj sezoni:
      // zimski kolegij se drži u neparnom, ljetni u parnom semestru. Ako prvi slobodni
      // semestar ima pogrešan paritet, kolegij čeka jedan semestar više.
      let sem = matchSeason(m + 1, cur);
      // Fiksirani semestar (povuci-i-ispusti): poštuj ga ako nije prije najranijeg.
      const pin = Number(cur.pin);
      if (Number.isFinite(pin) && pin >= sem) sem = matchSeason(pin, cur);
      earliest.set(name, sem);
      stack.pop();
      color.set(name, BLACK);
    }

    try {
      for (const k of courses) if (color.get(k.naziv) === WHITE) dfs(k.naziv);
    } catch (e) {
      return fail(cycleError || String(e.message || e));
    }

    // bridovi: preduvjet -> kolegij
    const edges = [];
    for (const k of courses) {
      for (const p of prereqList(k)) {
        edges.push({
          id: `${p.kolegij}__${k.naziv}`,
          source: p.kolegij,
          target: k.naziv,
          uvjet: p.uvjet,
        });
      }
    }

    const perCourse = courses
      .map((k) => {
        const s = earliest.get(k.naziv);
        return {
          naziv: k.naziv,
          earliest: s,
          godina: Math.ceil(s / 2),
          parity: semParity(s),
          plan: nominalSemester(k),
          status: k.status || "",
          ects: Number(k.ects) || 0,
          preduvjeti: prereqList(k),
        };
      })
      .sort((a, b) => a.earliest - b.earliest || a.naziv.localeCompare(b.naziv, "hr"));

    const totalSemesters = Math.max(...earliest.values());
    const totalYears = Math.ceil(totalSemesters / 2);

    const ectsPerSem = {};
    for (const pc of perCourse) ectsPerSem[pc.earliest] = (ectsPerSem[pc.earliest] || 0) + pc.ects;

    const nodes = courses.map((k) => ({ naziv: k.naziv, semestar: earliest.get(k.naziv) }));
    const totalEcts = courses.reduce((sum, k) => sum + (Number(k.ects) || 0), 0);

    return { ok: true, earliest, nodes, edges, perCourse, totalSemesters, totalYears, ectsPerSem, totalEcts };
  }

  // Skup svih (tranzitivnih) preduvjeta nekog kolegija (uzvodno).
  function ancestorsOf(naziv, courses) {
    const byName = new Map(courses.map((k) => [k.naziv, k]));
    const seen = new Set();
    const st = [naziv];
    while (st.length) {
      const cur = st.pop();
      for (const pn of prereqNames(byName.get(cur) || {})) {
        if (!seen.has(pn)) {
          seen.add(pn);
          st.push(pn);
        }
      }
    }
    return seen;
  }

  // Skup svih kolegija koji (tranzitivno) ovise o ovom (nizvodno).
  function descendantsOf(naziv, courses) {
    const children = new Map();
    for (const k of courses) {
      for (const pn of prereqNames(k)) {
        if (!children.has(pn)) children.set(pn, []);
        children.get(pn).push(k.naziv);
      }
    }
    const seen = new Set();
    const st = [naziv];
    while (st.length) {
      const cur = st.pop();
      for (const ch of children.get(cur) || []) {
        if (!seen.has(ch)) {
          seen.add(ch);
          st.push(ch);
        }
      }
    }
    return seen;
  }

  PMF.schedule = {
    prereqList,
    prereqNames,
    nominalSemester,
    semParity,
    computeSchedule,
    ancestorsOf,
    descendantsOf,
  };
})();
