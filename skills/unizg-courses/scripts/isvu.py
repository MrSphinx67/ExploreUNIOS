#!/usr/bin/env python3
"""Query the ISVU public course catalog (isvu.hr/visokaucilista). Stdlib only.

Scope: courses, curricula, literature. Teacher names appear as an attribute of a
course because ISVU prints them there, but this tool deliberately offers no way to
index, search or aggregate by person. See SKILL.md.
"""
import argparse, html, json, os, re, sys, threading, time, unicodedata, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor

BASE = "https://www.isvu.hr/visokaucilista/hr"
PROJECT_URL = "https://github.com/pitfa19/explore_unizg"
# Works with no configuration. Set ISVU_CONTACT to add a reachable address, which
# is the courteous thing to do for anything beyond occasional lookups.
CONTACT = os.environ.get("ISVU_CONTACT", "").strip()
UA = (f"unizg-courses/1.0 (+{PROJECT_URL}"
      + (f"; contact: {CONTACT}" if CONTACT else "") + ")")
CACHE = os.environ.get("ISVU_CACHE", os.path.expanduser("~/.cache/isvu"))
MIN_INTERVAL = 1.0 / 3          # 3 req/s ceiling, across all threads
# ISVU answers a course page in ~0.7s, so fetching one at a time spends most of the wall
# clock idle: 69 courses took 104s against a 23s rate-limit floor. A few workers fill that
# idle time. They do NOT raise the request rate: _reserve() hands out send slots
# MIN_INTERVAL apart globally, so the load on ISVU is identical either way.
WORKERS = int(os.environ.get("ISVU_WORKERS", "4"))

_slot_lock = threading.Lock()
_next_slot = [0.0]              # monotonic time of the next permitted request
_halted = [False]               # set once ISVU says 429; no thread starts a new request after


class RateLimited(RuntimeError):
    """ISVU said 429. Raised, not sys.exit: a long-lived server must not kill itself."""


def _reserve():
    """Block until this caller's turn to send, keeping the global rate at MIN_INTERVAL."""
    if _halted[0]:
        raise RateLimited("Stopped after an earlier 429 from ISVU. Retry much later.")
    with _slot_lock:
        slot = max(time.monotonic(), _next_slot[0])
        _next_slot[0] = slot + MIN_INTERVAL
    wait = slot - time.monotonic()
    if wait > 0:
        time.sleep(wait)            # sleeping outside the lock is what allows overlap


def fetch(path, ttl=86400):
    """GET {BASE}{path} with on-disk cache, rate limit and 429 hard stop. Thread-safe."""
    url = path if path.startswith("http") else BASE + path
    key = re.sub(r"[^A-Za-z0-9]+", "_", url)[-180:]
    fp = os.path.join(CACHE, key)
    if os.path.exists(fp) and (ttl is None or time.time() - os.path.getmtime(fp) < ttl):
        try:
            with open(fp, encoding="utf-8") as f:
                return f.read()
        except OSError:
            pass                    # a concurrent write; fall through and refetch
    _reserve()
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        body = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        if e.code == 429:
            _halted[0] = True
            raise RateLimited("ISVU returned 429 (rate limited). Stop and retry much later.")
        raise
    try:                            # write via a unique temp file: concurrent fetches of the
        os.makedirs(CACHE, exist_ok=True)   # same url must not read a half-written cache entry
        tmp = f"{fp}.{os.getpid()}.{threading.get_ident()}.tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(body)
        os.replace(tmp, fp)
    except OSError:
        pass                        # caching is an optimisation, never a requirement
    return body


def fetch_all(paths, ttl=86400, workers=None):
    """Fetch paths concurrently, still at <=3 req/s overall. Returns {path: body}.

    A path that fails is absent from the result rather than sinking the whole batch; a 429
    aborts the batch, because continuing to hammer a service that just said stop is rude.
    """
    paths = list(dict.fromkeys(paths))                  # dedupe, keep order
    out = {}
    if not paths:
        return out
    with ThreadPoolExecutor(max_workers=workers or WORKERS) as pool:
        futures = {pool.submit(fetch, p, ttl): p for p in paths}
        for fut, p in futures.items():
            try:
                out[p] = fut.result()
            except RateLimited:
                raise
            except Exception:
                continue
    return out


# ---------- HTML helpers ----------

def strip(s):
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s))).strip()


def _rows(inner):
    out = []
    for r in re.findall(r"(?s)<tr[^>]*>(.*?)</tr>", inner):
        cells = [strip(c) for c in re.findall(r"(?s)<t[hd][^>]*>(.*?)</t[hd]>", r)]
        if cells:
            out.append(cells)
    return out


_OPEN = re.compile(r"<table[^>]*>", re.S)
_TOK = re.compile(r"(?s)<table[^>]*>|</table>")


def balanced_tables(doc):
    """[(opening_tag, inner_html, start, end)] for top-level <table>s at this level.

    Curriculum pages nest elective tables inside the semester table, so a
    non-greedy <table>...</table> regex closes the outer table on the inner
    table's tag and mangles both. Count depth instead.
    """
    out, i = [], 0
    while True:
        m = _OPEN.search(doc, i)
        if not m:
            return out
        depth, inner_end, end = 1, len(doc), len(doc)
        for t in _TOK.finditer(doc, m.end()):
            depth += -1 if t.group(0).startswith("</") else 1
            if depth == 0:
                inner_end, end = t.start(), t.end()
                break
        out.append((m.group(0), doc[m.end():inner_end], m.start(), end))
        i = end


def _own_rows(inner):
    """Rows belonging to this table only, with nested tables cut out by position."""
    keep, last = [], 0
    for _, _, s, e in balanced_tables(inner):
        keep.append(inner[last:s])
        last = e
    keep.append(inner[last:])
    return _rows("".join(keep))


def tables(doc, with_tag=False):
    """Every table at any nesting depth, as rows of cell strings."""
    out = []

    def walk(fragment):
        for tag, inner, _, _ in balanced_tables(fragment):
            r = _own_rows(inner)
            if r:
                out.append((tag, r) if with_tag else r)
            walk(inner)

    walk(doc)
    return out


def fold(s):
    """Diacritic-insensitive, casefolded. c/c, s/s, z/z, dj for d."""
    s = s.replace("đ", "dj").replace("Đ", "Dj")
    s = unicodedata.normalize("NFD", s)
    return "".join(c for c in s if unicodedata.category(c) != "Mn").casefold()


def fields(doc):
    """Course detail fields, read off the <dl> structure.

    Markup is <dt><span class="karticaDetaljno">Label:</span></dt><dd>value</dd>.
    Every field is optional and only rendered when populated, so never assume a
    fixed label list: read whatever labels are present. That is how the two
    Preduvjeti fields are easy to miss.
    """
    out = {}
    for k, v in re.findall(
            r"(?s)<dt[^>]*>.*?karticaDetaljno[^>]*>(.*?)</span>.*?</dt>\s*<dd[^>]*>(.*?)</dd>", doc):
        key = html.unescape(re.sub(r"<[^>]+>", "", k)).strip().rstrip(":").strip()
        txt = html.unescape(re.sub(r"<(br|/p|/div|/li)[^>]*>", "\n", v))
        txt = re.sub(r"<[^>]+>", " ", txt)
        txt = re.sub(r"\n\s*\n+", "\n", re.sub(r"[ \t]+", " ", txt)).strip()
        if key and txt:
            out[key] = txt
    return out


def parse_prereqs(txt):
    """'Ime predmeta (položen)  Drugo ime (odslušan)' -> structured edges."""
    if not txt:
        return []
    out = []
    for name, cond in re.findall(r"([^()\n]+?)\s*\((polo[žz]en|odslu[šs]an)\)", txt):
        n = name.strip(" ,;\n\t")
        if n:
            out.append({"kolegij": n, "uvjet": fold(cond).replace("z", "z")})
    return out


# ---------- commands ----------

def cmd_institutions(a):
    doc = fetch("/pretrazivanje")
    out = []
    for t in tables(doc):
        for row in t:
            m = None
            if len(row) >= 3:
                out.append(row)
    # re-scan with ids, since ids live in hrefs not cells
    rows = re.findall(r"(?s)<tr[^>]*>(.*?)</tr>", doc)
    res = []
    for r in rows:
        idm = re.search(r"podaci/(\d+)", r)
        cells = [strip(c) for c in re.findall(r"(?s)<td[^>]*>(.*?)</td>", r)]
        if idm and len(cells) >= 3:
            res.append({"id": int(idm.group(1)), "naziv": cells[0],
                        "nadredjena": cells[1], "grad": cells[2]})
    if a.unizg:
        res = [x for x in res if "Sveučilište u Zagrebu" in x["nadredjena"]]
    if a.search:
        q = fold(a.search)
        res = [x for x in res if q in fold(x["naziv"])]
    print(json.dumps(res, ensure_ascii=False, indent=2))


def course_list_path(inst, year=None):
    """Path of an institution's course list. Exposed so callers can warm several at once."""
    return f"/podaci/{inst}/predmeti" + (f"/akademskagodina/{year}" if year else "")


def course_list(inst, year=None):
    """Course list, parsed off the header row.

    Two gotchas: the column order is Naziv then Šifra (name first), and the
    per-course hrefs live outside the <tr> elements, so do not try to read the
    code out of a link. Some institutions link course names, others do not.
    """
    doc = fetch(course_list_path(inst, year))
    out, seen = [], set()
    for rows in tables(doc):
        keys = [k.strip() for k in rows[0]]
        if "Naziv" not in keys or "Šifra" not in keys:
            continue
        ni, si = keys.index("Naziv"), keys.index("Šifra")
        for r in rows[1:]:
            if len(r) != len(keys):
                continue
            code = r[si].strip()
            if code and code not in seen:
                seen.add(code)
                out.append({"sifra": code, "naziv": r[ni].strip()})
    return out


def cmd_courses(a):
    res = course_list(a.inst, a.year)
    if a.search:
        q = fold(a.search)
        res = [c for c in res if q in fold(c["naziv"])]
    if a.limit:
        res = res[: a.limit]
    print(json.dumps({"institution": a.inst, "count": len(res), "courses": res},
                     ensure_ascii=False, indent=2))


def cmd_course(a):
    year = a.year or 2025
    doc = fetch(f"/podaci/{a.inst}/akademskagodina/{year}/predmeti/predmet/{a.code}")
    f = fields(doc)
    rec = {"institution": a.inst, "sifra": a.code, "akademskaGodina": year,
           "source": f"{BASE}/podaci/{a.inst}/akademskagodina/{year}/predmeti/predmet/{a.code}"}
    h2 = re.findall(r"(?s)<h2[^>]*>(.*?)</h2>", doc)
    rec["naziv"] = strip(h2[-1]) if h2 else None
    for lab, key in [("Kratica", "kratica"), ("Opterećenje", "opterecenje"),
                     ("Opis predmeta", "opis"), ("Obavezna literatura", "literatura_obavezna"),
                     ("Preporučena literatura", "literatura_preporucena"),
                     ("Jezici izvođenja nastave", "jezici"), ("Nositelji", "nositelji"),
                     ("Izvođači", "izvodaci")]:
        rec[key] = f.get(lab)
    try:
        rec["ects"] = float(f["ECTS bodovi"])
    except (KeyError, ValueError):
        rec["ects"] = None
    rec["preduvjeti_upis"] = parse_prereqs(f.get("Preduvjeti za upis predmeta"))
    rec["preduvjeti_polaganje"] = parse_prereqs(f.get("Preduvjeti za polaganje predmeta"))
    rec["fields_present"] = sorted(f)
    # programmes: semester + obavezni/izborni per study programme
    progs = []
    i = doc.find("Predmet u nastavnom programu")
    if i > 0:
        for row in re.findall(r"(?s)<tr[^>]*>(.*?)</tr>", doc[i:]):
            c = [strip(x) for x in re.findall(r"(?s)<td[^>]*>(.*?)</td>", row)]
            if len(c) >= 5 and c[3].strip().isdigit():
                progs.append({"sifraStudija": c[0], "naziv": c[1], "razina": c[2],
                              "semestar": int(c[3]), "status": c[4]})
    rec["programmes"] = progs
    print(json.dumps(rec, ensure_ascii=False, indent=2))


def cmd_programmes(a):
    year = a.year or 2025
    levels = json.loads(fetch(f"/podaci/{a.inst}/dohvatirazine/{year}"))
    tree = []
    for lv in levels:
        r = lv["sifraRazine"]
        modes = json.loads(fetch(f"/podaci/{a.inst}/razina/{r}/dohvatiizvedbe/{year}"))
        for md in modes:
            i = md["oznaka"]
            try:
                studies = json.loads(fetch(f"/podaci/{a.inst}/razina/{r}/izvedba/{i}/akgodina/{year}"))
            except Exception:
                continue
            tree.append({"razina": r, "nazivRazine": lv["nazivRazineIVrste"],
                         "izvedba": i, "nazivIzvedbe": md["naziv"], "studiji": studies})
    print(json.dumps({"institution": a.inst, "akademskaGodina": year, "razine": tree},
                     ensure_ascii=False, indent=2))


def cmd_curriculum(a):
    year = a.year or 2025
    p = (f"/podaci/{a.inst}/nastavniprogram/{year}/razina/{a.razina}"
         f"/izvedba/{a.izvedba}/smjer/{a.smjer}")
    doc = fetch(p)
    sems = []
    for sem, chunk in split_semesters(doc):
        entry = {"semestar": sem, "grupe": []}
        for grp_name, tbl in _grouped_tables(chunk):
            entry["grupe"].append({"grupa": grp_name, "predmeti": tbl})
        sems.append(entry)
    print(json.dumps({"institution": a.inst, "akademskaGodina": year, "smjer": a.smjer,
                      "source": BASE + p, "semestri": sems}, ensure_ascii=False, indent=2))


def split_semesters(doc):
    """[(semester_number, html_chunk)] from the tab panes.

    Do NOT split on the visible "Semestar N" text: those are nav-tab labels and
    they all appear together before any content, so text splitting assigns every
    course to the last semester. The content lives in sibling
    <div id="semestarN" class="tab-pane"> panes.
    """
    marks = [(int(m.group(1)), m.start())
             for m in re.finditer(r'<div[^>]*id="semestar(\d+)"', doc)]
    out = []
    for i, (sem, pos) in enumerate(marks):
        end = marks[i + 1][1] if i + 1 < len(marks) else len(doc)
        out.append((sem, doc[pos:end]))
    return out


def _grouped_tables(chunk):
    """[(group, [course dicts])] for one semester. group is None for mandatory courses.

    Elective tables carry id="izb_predmetiNNN_semN"; mandatory ones do not. The group
    label and its ECTS minimum sit in the header cell just before the table, as
    <b>Izborna grupa: </b>LABEL<br><p><b>Opis: </b>...najmanje N</p>.
    """
    groups = {}   # izb id -> {"naziv":…, "min_ects":…}
    for m in re.finditer(r"(?s)<b>\s*Izborna grupa:\s*</b>(.*?)(?:<br|</td)", chunk):
        head = chunk[max(0, m.start() - 260): m.start()]
        gid = re.findall(r"izb_predmeti(\d+)", head)
        tail = chunk[m.end(): m.end() + 300]
        mn = re.search(r"najmanje\s+([\d.]+)", tail)
        if gid:
            groups[gid[-1]] = {"naziv": strip(m.group(1)),
                               "min_ects": float(mn.group(1)) if mn else None}
    out = []
    for tag, rows in tables(chunk, with_tag=True):
        keys = [h.strip() for h in rows[0]]
        if "Naziv" not in keys:
            continue
        gid = re.search(r'id="izb_predmeti(\d+)', tag)
        grp = groups.get(gid.group(1), {"naziv": None, "min_ects": None}) if gid else None
        items = []
        for r in rows[1:]:
            if len(r) != len(keys):
                continue
            d = dict(zip(keys, r))
            items.append({"sifra": d.get("Šifra"), "naziv": d.get("Naziv"),
                          "ects": d.get("ECTS"), "polaze_se": d.get("Polaže se"),
                          "sati": {k: v for k, v in d.items()
                                   if k not in ("Šifra", "Naziv", "ECTS", "Polaže se")}})
        if items:
            out.append((grp, items))
    return out


def merge_duplicates(courses):
    """Collapse courses sharing a name into one. Returns (courses, merged).

    A curriculum routinely lists the same course name more than once, and the scheduler
    keys its graph by name, so it rejects the import outright ("Dvostruki kolegij").
    Deduping by sifra is not enough because the rows often carry different sifre. Across
    PMF-119's curricula, 91 duplicate-name groups survive a sifra-level dedupe. Two causes:

    - Year-long courses split into a placeholder row and a credit-bearing row. Real case:
      "Klasicna elektrodinamika" on Fizika/istrazivacki is sifra 51520 in semester 5 at
      0.0 ECTS and sifra 51521 in semester 6 at 12.0 ECTS. It is one course taught over
      two semesters and graded at the end.
    - The same course offered in either of two semesters, or relisted under a second
      sifra after a revision.

    The row carrying the credits is the real one, so the survivor is the highest-ECTS row,
    earliest semester breaking ties. Prerequisites are unioned rather than taken from the
    survivor, because the placeholder row sometimes carries them instead.
    """
    groups, order = {}, []
    for c in courses:
        k = fold(c["naziv"])
        if k not in groups:
            groups[k] = []
            order.append(k)
        groups[k].append(c)

    out, merged = [], []
    for k in order:
        rows = groups[k]
        if len(rows) == 1:
            out.append(rows[0])
            continue
        # highest ECTS wins; then earliest semester (godina, then zimski before ljetni)
        best = max(rows, key=lambda c: (c["ects"], -c["godina"],
                                        0 if c["semestar"] == "ljetni" else 1))
        seen_p, union = set(), []
        for c in rows:
            for p in c["preduvjeti"]:
                sig = (fold(p["kolegij"]), p["uvjet"])
                if sig not in seen_p:
                    seen_p.add(sig)
                    union.append(p)
        best["preduvjeti"] = union
        # Callers may hang a "_paths" list of source pages on each row; union those too, so a
        # merge before fetching still reads the prerequisites off every row it collapsed.
        paths = []
        for c in rows:
            for p in c.get("_paths") or []:
                if p not in paths:
                    paths.append(p)
        if paths:
            best["_paths"] = paths
        merged.append({
            "naziv": best["naziv"],
            "kept": {"godina": best["godina"], "semestar": best["semestar"],
                     "ects": best["ects"]},
            "dropped": [{"godina": c["godina"], "semestar": c["semestar"], "ects": c["ects"]}
                        for c in rows if c is not best],
        })
        out.append(best)
    return out, merged


def prune_dangling(courses):
    """Drop prerequisite edges naming a course outside this list. Returns (courses, dropped).

    ISVU prerequisites are free text and routinely name courses that are not in the
    programme being exported, usually renamed or retired ones. Real example at
    Arhitektonski: "Nosive konstrukcije II" requires "Arhitektonske konstrukcije I"
    while the curriculum only contains "Arhitektonske konstrukcije i materijali I".
    The scheduler app rejects the whole import if any prerequisite names a course it
    cannot find, so these have to go. Report them, never drop silently.
    """
    known = {fold(c["naziv"]): c["naziv"] for c in courses}
    dropped = []
    for c in courses:
        keep = []
        for p in c["preduvjeti"]:
            k = fold(p["kolegij"])
            if k in known:
                keep.append({"kolegij": known[k], "uvjet": p["uvjet"]})
            else:
                dropped.append({"course": c["naziv"], "missing_prerequisite": p["kolegij"],
                                "uvjet": p["uvjet"]})
        c["preduvjeti"] = keep
    return courses, dropped


def cmd_dag(a):
    """Emit one programme in the kolegiji.json schema the scheduler app consumes.

    Prerequisites come from the two optional ISVU fields, so expect many empty
    lists: only ~10% of courses declare an upis prerequisite. Absent is not the
    same as none, and this is exactly where faculty sites (PMF, PBF) add data.
    """
    year = a.year or 2025
    doc = fetch(f"/podaci/{a.inst}/nastavniprogram/{year}/razina/{a.razina}"
                f"/izvedba/{a.izvedba}/smjer/{a.smjer}")
    seen, out = set(), []
    for sem, chunk in split_semesters(doc):
        for grp, items in _grouped_tables(chunk):
            for it in items:
                if not it["sifra"] or it["sifra"] in seen:
                    continue
                seen.add(it["sifra"])
                try:
                    ects = float(it["ects"])
                except (TypeError, ValueError):
                    ects = 0.0
                out.append({
                    "naziv": it["naziv"],
                    "sifra": it["sifra"],
                    "semestar": "zimski" if sem % 2 else "ljetni",
                    "godina": (sem + 1) // 2,
                    "status": "izborni" if grp else "obavezni",
                    "ects": ects,
                    "preduvjeti": [],
                    "_paths": [f"/podaci/{a.inst}/akademskagodina/{year}"
                               f"/predmeti/predmet/{it['sifra']}"],
                })
    # Merge before fetching: a year-long course is two rows, and the credit-bearing one is
    # the keeper. See merge_duplicates for why sifra-level dedupe does not catch these.
    out, merged = merge_duplicates(out)
    docs = fetch_all([p for c in out for p in c.get("_paths") or []])
    for c in out:
        seen_p = set()
        for p in c.pop("_paths", []):
            doc = docs.get(p)
            if not doc:
                continue
            for pr in parse_prereqs(fields(doc).get("Preduvjeti za upis predmeta")):
                sig = (fold(pr["kolegij"]), pr["uvjet"])
                if sig not in seen_p:
                    seen_p.add(sig)
                    c["preduvjeti"].append(pr)
    if merged:
        print(f"# merged {len(merged)} duplicated course name(s); kept the credit-bearing row:",
              file=sys.stderr)
        for m in merged:
            drops = ", ".join(f"g{d['godina']} {d['semestar']} {d['ects']} ECTS"
                              for d in m["dropped"])
            print(f"#   {m['naziv']}: kept g{m['kept']['godina']} {m['kept']['semestar']} "
                  f"{m['kept']['ects']} ECTS, dropped {drops}", file=sys.stderr)
    out, dropped = prune_dangling(out)
    if dropped:
        print(f"# dropped {len(dropped)} prerequisite edge(s) naming courses outside this "
              f"programme:", file=sys.stderr)
        for d in dropped:
            print(f"#   {d['course']} <- {d['missing_prerequisite']} ({d['uvjet']})",
                  file=sys.stderr)
    print(json.dumps({"kolegiji": out}, ensure_ascii=False, indent=2))


def cmd_selfcheck(a):
    """The three JSON endpoints are undocumented internals. Fail loudly if they move."""
    ok = True
    try:
        lv = json.loads(fetch("/podaci/36/dohvatirazine/2025", ttl=0))
        assert isinstance(lv, list) and "sifraRazine" in lv[0], "dohvatirazine shape"
        md = json.loads(fetch("/podaci/36/razina/3/dohvatiizvedbe/2025", ttl=0))
        assert isinstance(md, list) and "oznaka" in md[0], "dohvatiizvedbe shape"
        st = json.loads(fetch("/podaci/36/razina/3/izvedba/R/akgodina/2025", ttl=0))
        assert isinstance(st, list) and "sifraSmjera" in st[0], "programme tree shape"
        print("JSON endpoints OK:", len(lv), "levels,", len(md), "modes,", len(st), "studies")
    except Exception as e:
        ok = False
        print("JSON endpoint CHANGED:", e)
    n = len(course_list(36))
    print(f"course list OK: FER has {n} courses" if n > 500 else f"course list SUSPECT: {n}")
    doc = fetch("/podaci/36/akademskagodina/2025/predmeti/predmet/183357", ttl=0)
    for lab in ("Predmet u nastavnom programu", "ECTS bodovi"):
        print(("field present: " if lab in doc else "field MISSING: ") + lab)
        ok &= lab in doc
    sys.exit(0 if ok else 1)


def main():
    ap = argparse.ArgumentParser(description="ISVU public course catalog client")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("institutions", help="list institutions and their ISVU ids")
    p.add_argument("--unizg", action="store_true", help="only UNIZG constituents")
    p.add_argument("--search")
    p.set_defaults(fn=cmd_institutions)

    p = sub.add_parser("courses", help="list an institution's courses")
    p.add_argument("inst", type=int)
    p.add_argument("--year", type=int)
    p.add_argument("--search", help="diacritic-insensitive substring")
    p.add_argument("--limit", type=int)
    p.set_defaults(fn=cmd_courses)

    p = sub.add_parser("course", help="course detail: description, literature, programmes")
    p.add_argument("inst", type=int)
    p.add_argument("code")
    p.add_argument("--year", type=int)
    p.set_defaults(fn=cmd_course)

    p = sub.add_parser("programmes", help="programme/module tree for an institution")
    p.add_argument("inst", type=int)
    p.add_argument("--year", type=int)
    p.set_defaults(fn=cmd_programmes)

    p = sub.add_parser("curriculum", help="one programme's courses, by semester")
    p.add_argument("inst", type=int)
    p.add_argument("razina", type=int)
    p.add_argument("izvedba")
    p.add_argument("smjer", type=int)
    p.add_argument("--year", type=int)
    p.set_defaults(fn=cmd_curriculum)

    p = sub.add_parser("dag", help="export a programme in the scheduler's kolegiji.json schema")
    p.add_argument("inst", type=int)
    p.add_argument("razina", type=int)
    p.add_argument("izvedba")
    p.add_argument("smjer", type=int)
    p.add_argument("--year", type=int)
    p.set_defaults(fn=cmd_dag)

    p = sub.add_parser("selfcheck", help="verify undocumented endpoints still work")
    p.set_defaults(fn=cmd_selfcheck)

    a = ap.parse_args()
    try:
        a.fn(a)
    except RateLimited as e:                 # the CLI still stops hard; the server does not
        sys.exit(str(e))


if __name__ == "__main__":
    main()
