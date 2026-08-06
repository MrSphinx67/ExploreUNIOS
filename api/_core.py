"""Shared MCP core: tool definitions, dispatch, and the server instructions.

Imported by api/mcp.py (remote HTTP, for the Claude web and mobile apps) and by
mcp/stdio_server.py (local stdio, for Claude Desktop and Claude Code). Depends only
on the stdlib plus the ISVU client in skills/unios-courses/scripts/isvu.py.
"""
import importlib.util
import json
import os
import sys

os.environ.setdefault("ISVU_CACHE", "/tmp/isvu-cache")   # serverless: only /tmp is writable

_HERE = os.path.dirname(os.path.abspath(__file__))
_CANDIDATES = [
    os.path.join(_HERE, "..", "skills", "unios-courses", "scripts", "isvu.py"),
    os.path.join(_HERE, "skills", "unios-courses", "scripts", "isvu.py"),
    os.path.join(_HERE, "_isvu.py"),
]


def _load_isvu():
    for p in _CANDIDATES:
        p = os.path.normpath(p)
        if os.path.exists(p):
            spec = importlib.util.spec_from_file_location("isvu", p)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod
    raise RuntimeError("isvu.py not found; looked in: " + ", ".join(_CANDIDATES))


isvu = _load_isvu()

# ---------------------------------------------------------------- instructions
# "18 constituent faculties" is the count from _institutions() (nadredjena filter). "roughly 9,500
# courses" is a live sum of len(isvu.course_list(i["id"])) over those 18 ids, no year param (current
# ISVU listing), measured 2026-08-05 -> 9,501. Re-run that if this drifts noticeably; it is a snapshot,
# not a tracked figure.

INSTRUCTIONS = """\
Read-only access to the official Sveučilište Josipa Jurja Strossmayera u Osijeku (SUJJS) course catalog, the ISVU public data
module that SRCE runs for the ministry. 18 constituent faculties, roughly 9,500 courses, academic
years back to the late 1990s/2000s depending on the faculty.

WHAT THIS IS FOR
Teaching data: what a course covers, its ECTS, semester, workload, prerequisites, and its required
and recommended literature; whole curricula semester by semester with elective groups; comparing how
different faculties teach the same subject; and the catalog half of horizontalna mobilnost.

HORIZONTALNA MOBILNOST: TAKING COURSES AT ANOTHER SUJJS (OSIJEK) FACULTY
Students ask this often, in both languages, but the answer here is NOT an unconditional yes. Under
article 36(1) of the Pravilnik o studijima i studiranju SUJJS (adopted December 2023), a student may
enrol courses from another smjer, another study, or another sastavnica ONLY if the course's own
nositelj studija has already provided for it in that programme's studijski program. Never answer as
though this is an unconditional right the way UNIZG frames it; say it depends on whether the home
programme has provided for it, and point the student to their nositelj studija / studijski program to
check. Call unios_mobility_rules for the full briefing with citations; the essentials:

- What it is: two separate channels under članak 36. (1) individual courses from another smjer/study/
  sastavnica, conditional on the course's own nositelj having provided for it in the programme; (2) a
  university-wide list of izborni kolegiji that the Senate adopts each academic year on programme
  proposals, open to every nositelj studija at the University. These are not the same mechanism.
- ECTS recognition (čl. 36 st. 3): credits are recognised either as part of the home programme, at the
  ECTS value the course carries where it is taught, or entered as an entirely new izborni kolegij in
  the student record. The host course's nositelj confirms completion by entering the ECTS, grade, and
  their signature. The Pravilnik does not describe UNIZG's three-consent process (home programme body,
  ECTS coordinator, course leader) — do not invent that process for Osijek.
- Capacity (čl. 36 st. 4): the number of students who may enrol a given izborni kolegij is limited by
  the host sastavnica's capacity, decided by its competent body on the course leader's proposal.
- Costs (čl. 36 st. 5): costs for mobility within the University are set by Odluka Senata — a
  centralised, formal mechanism. If asked for a specific figure, say it is regulated by a Senate
  decision that must be looked up separately; never guess a number.
- Between universities, including abroad (čl. 37): governed by posebni ugovori (special agreements);
  the Pravilnik gives no procedural detail here. For the international/Erasmus+ case specifically, the
  University publishes a "Pravilnik o Erasmus+ programu individualne međunarodne mobilnosti odlaznih i
  dolaznih studenata i (ne)nastavnog osoblja u okviru ključne aktivnosti 1" on its popis akata — say
  that document exists and is where the procedure lives, but do not describe its contents, since it
  has not been read.
- Do NOT carry over UNIZG-specific claims: no "established right" framing, no grade-average claim
  either way, no three-consent process, no paralelni studij comparison (e.g. FER's 4.5 threshold), and
  no seven-step referada/molba process. None of that is confirmed for SUJJS.

Source reliability: the confirmed text is the December 2023 Pravilnik (čl. 36-37). A newer March 2025
"pročišćeni tekst" exists but its mobility chapter is unverified (the PDF on gfos.unios.hr is
password-protected) — when it matters, say so and point the student to the Ured za studente or the
faculty to confirm whether that chapter changed.

ISVU answers the catalog half: omitting faculty_id from unios_courses searches all 18 constituents at
once, which is how you answer "where else is this taught" and "what would I actually be signing up
for". Do not offer to filter by teaching language: it is published for only ~10% of courses and marked
English for ~4%, so absence carries no information.

SCOPE LIMIT, PLEASE RESPECT IT
This is not a directory of academics. ISVU prints teacher names on every course page, so they appear
in results, and it is fine to say who teaches a course when answering about that course. Do not use
these tools to build a person index, search or filter by professor, aggregate somebody's teaching
portfolio, rank people, or collect contact details. A name is an attribute of a course, never a row
to query. If asked for people-centric analysis, say it is out of scope here.

DATA COVERAGE, STATE THIS HONESTLY
Semester, programme and obavezni/izborni status are ~100% populated (0 misses in a live 180-course
sample). Course leader ~87%. Descriptions only 24%, learning outcomes (ishodi ucenja) 52%. Prerequisites
for enrolment (preduvjeti za upis) are essentially unpublished at 0%; prerequisites for taking the exam
(preduvjeti za polaganje) about 2%. Learning-outcome coverage is bimodal, not evenly thin: FFOS, FOOZOS
and FPMOI publish ishodi on every sampled course, while EFOS, FAZOS, PRAVOS, FERIT and FDMZ publish
none. When a field comes back empty, say the faculty did not publish it. Never imply the course lacks
the thing.

Learning outcomes are not a separate field. Where present they sit inside the description under
faculty-specific headings that vary; some faculties write "Ciljevi kolegija" and "Sadrzaj kolegija"
and no outcomes at all. Read them out of the description.

A course can belong to several programmes at different semesters with different obavezni/izborni
status, so treat semester as per-programme, never as one value for the course.

BUILDING A PREREQUISITE GRAPH
unios_dag_json returns courses in the exact JSON the companion scheduler web app imports, so a user
can paste it straight in and get a prerequisite DAG with an earliest-completion schedule. Offer this
whenever someone asks to plan or visualise what leads to a course.

Pass `target` when the user wants what feeds into a specific course. Right now that mostly returns
just the course itself: unlike UNIZG, no SUJJS institution currently publishes structured
upis-prerequisites (measured 0% across all 18, including every FERIT programme), so there's usually
no upstream chain to walk. Say that plainly rather than implying a course has no prerequisites.
Omitting `target` exports the entire programme instead, which runs from a few dozen courses (FERIT:
23-47) to 100+ for a large integrated programme (Medicina: 140) — still worth avoiding for size, just
not for the "hairball" a real prerequisite graph would draw. Only omit it when the user explicitly
wants the whole programme laid out.

Tell them prerequisite coverage is patchy: Arhitektonski is the richest in ISVU, PMF and PBF publish
more on their own faculty sites, and FER publishes none anywhere. An empty preduvjeti list means
nothing was published, which is not the same as the course having no prerequisites. Where a faculty
publishes nothing, a target chain comes back as the single course, and you should say why rather than
implying the course has no prerequisites.

Do not hand-edit the course list to fix an import error. Both known causes are handled and reported:
duplicate names are merged (see merged_duplicates) and prerequisites naming courses outside the export
are pruned (dropped_prerequisites). If the app still rejects it, say so instead of patching the JSON.

Search matches Croatian text without diacritics, so "racunarstvo" finds "Racunarstvo".
"""

# ---------------------------------------------------------------- tool schemas

TOOLS = [
    {
        "name": "unios_courses",
        "description": ("Find courses by name across a SUJJS (Osijek) faculty. Diacritic-insensitive, so "
                        "'racunarstvo' matches 'Računarstvo'. Returns course codes to pass to "
                        "unios_course. Omit faculty_id to search all 18 constituents at once, "
                        "which takes about 6 s and is the right way to answer 'where else is "
                        "this taught'. If more matched than the limit, the result says so and "
                        "lists the count per faculty: report that, never imply completeness."),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": ("Course name or fragment, Croatian or "
                                                            "partial. Omit to list a whole faculty.")},
                "faculty_id": {"type": "integer", "description": "ISVU institution id, e.g. 36 for FER."},
                "faculty": {"type": "string", "description": "Faculty name or abbreviation if the id is unknown."},
                "year": {"type": "integer", "description": "Academic year start, e.g. 2025 for 2025/2026."},
                "limit": {"type": "integer", "default": 40},
            },
        },
    },
    {
        "name": "unios_course",
        "description": ("Full detail for one course: description, learning outcomes (inside the "
                        "description), required and recommended literature, ECTS, workload, "
                        "prerequisites, and every programme it belongs to with its semester and "
                        "obavezni/izborni status."),
        "inputSchema": {
            "type": "object",
            "properties": {
                "faculty_id": {"type": "integer"},
                "faculty": {"type": "string", "description": "Faculty name or abbreviation, instead of the id."},
                "code": {"type": "string", "description": "ISVU course code (sifra), from unios_courses."},
                "year": {"type": "integer"},
            },
            "required": ["code"],
        },
    },
    {
        "name": "unios_programmes",
        "description": ("List a faculty's study programmes and modules, with their level, delivery "
                        "mode and the ids needed by unios_curriculum and unios_dag_json. Only "
                        "entries with has_curriculum true can be expanded."),
        "inputSchema": {
            "type": "object",
            "properties": {
                "faculty_id": {"type": "integer"},
                "faculty": {"type": "string"},
                "year": {"type": "integer"},
            },
        },
    },
    {
        "name": "unios_curriculum",
        "description": ("One study programme laid out semester by semester: mandatory courses plus "
                        "each elective group with the minimum ECTS you must choose from it."),
        "inputSchema": {
            "type": "object",
            "properties": {
                "faculty_id": {"type": "integer"},
                "faculty": {"type": "string", "description": "Faculty name or abbreviation, instead of the id."},
                "razina": {"type": "integer", "description": "Study level code from unios_programmes."},
                "izvedba": {"type": "string", "description": "Delivery mode code, usually 'R'."},
                "smjer": {"type": "integer", "description": "Programme id from unios_programmes."},
                "year": {"type": "integer"},
            },
            "required": ["razina", "izvedba", "smjer"],
        },
    },
    {
        "name": "unios_dag_json",
        "description": ("Export courses as the JSON the scheduler web app imports, to build a "
                        "prerequisite DAG and an earliest-completion schedule. Hand the user the "
                        "JSON verbatim in a fenced block and tell them to paste it into the app's "
                        "Zalijepi JSON box. PREFER `target`: it returns just the course and what "
                        "feeds into it, usually a readable handful. Without `target` you get the "
                        "entire programme, which can be 100+ courses and is both slow and an "
                        "unreadable graph."),
        "inputSchema": {
            "type": "object",
            "properties": {
                "faculty_id": {"type": "integer"},
                "faculty": {"type": "string", "description": "Faculty name or abbreviation, instead of the id."},
                "razina": {"type": "integer"},
                "izvedba": {"type": "string"},
                "smjer": {"type": "integer"},
                "target": {"type": "string", "description": (
                    "Course name to build the chain for. Returns that course plus its transitive "
                    "prerequisites only. Use this for 'what do I need before I can take X'.")},
                "max_depth": {"type": "integer", "description": (
                    "With target: how many levels of prerequisites to follow. Omit for the full "
                    "chain; 1 gives only direct prerequisites.")},
                "year": {"type": "integer"},
            },
            "required": ["razina", "izvedba", "smjer"],
        },
    },
    {
        "name": "unios_institutions",
        "description": "The 18 SUJJS (Osijek) constituent faculties with their ISVU ids, cities and course counts.",
        "inputSchema": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "Filter by name fragment."}},
        },
    },
    {
        "name": "unios_mobility_rules",
        "description": ("The rules for taking courses at another SUJJS (Osijek) sastavnica "
                        "(mobilnost studenata unutar Sveučilišta), čl. 36-37 of the Pravilnik "
                        "o studijima i studiranju: what conditions govern it, who confirms "
                        "completion, how ECTS get recognised, what capacity and costs depend "
                        "on, and what the Pravilnik does NOT say. Static text, no network call. "
                        "Call this for any 'can I study at another faculty' question before "
                        "answering, so the answer carries the actual conditions instead of an "
                        "assumed UNIZG-style unconditional right. Unlike UNIZG, this is "
                        "conditional on the student's own programme having provided for the "
                        "course."),
        "inputSchema": {"type": "object", "properties": {}},
    },
]

# --------------------------------------------------------- horizontalna mobilnost
# The rules half of the cross-faculty question. ISVU has none of this, and before it was written in
# here every model got the same question wrong in one of two ways: small ones refused ("not in the
# catalog") and larger ones affirmed unconditionally, importing the UNIZG framing of an established
# right. At SUJJS it is conditional (čl. 36 st. 1), so both readings hurt a student. The text below is
# deliberately specific about what čl. 36-37 actually says versus what UNIZG's text says that does not
# carry over. Sources are cited so answers can be checked; the fuller version with per-faculty detail
# lives in skills/unios-courses/references/horizontalna-mobilnost.md.

MOBILITY_RULES = """\
MOBILNOST STUDENATA UNUTAR SVEUČILIŠTA JOSIPA JURJA STROSSMAYERA U OSIJEKU

Ovo NIJE automatsko pravo studenta. Prema članku 36. stavku 1. Pravilnika o studijima i studiranju
SUJJS (usvojen prosinac 2023.), student može upisati kolegije s drugog smjera, drugog studija ili
druge sastavnice SAMO ako je te kolegije nositelj (matičnog) studija unaprijed predvidio u vlastitom
studijskom programu. Nikad ne tvrdi studentu da ima neuvjetovano pravo na mobilnost; reci da ovisi o
tome je li njegov studijski program to predvidio, i uputi ga da to provjeri kod nositelja studija /
u studijskom programu.

IZVOR I NJEGOVA POUZDANOST — reci ovo kad je relevantno
Postoje tri poznate verzije ovog Pravilnika: srpanj 2015. (stara, čl. 40-41, zamijenjena), prosinac
2023. (usvojena nakon javnog savjetovanja, čl. 36-37 — OVO je tekst ispod, usvajanje potvrđeno preko
popisa akata Pravnog fakulteta Osijek i FDMZ Osijek) i ožujak 2025. ("pročišćeni tekst" koji
konsolidira usvojeni tekst s naknadnim izmjenama — sadržaj NIJE moguće provjeriti jer je PDF na
gfos.unios.hr zaštićen lozinkom). Kad je pitanje takvo da se student stvarno oslanja na odgovor za
upis, reci da postoji noviji pročišćeni tekst iz ožujka 2025. čiji sadržaj o mobilnosti nije
verificiran, i uputi na Ured za studente ili fakultet da potvrde je li poglavlje mijenjano.

DVA ODVOJENA KANALA (čl. 36) — ne miješaj ih
1. "Obična" mobilnost (st. 1): pojedini kolegiji s drugog smjera/studija/sastavnice, uvjetovano time
   da ih je nositelj matičnog studija predvidio u studijskom programu.
2. Sveučilišni popis izbornih kolegija (st. 2): zaseban popis koji svake akademske godine, na
   prijedlog nositelja studija, donosi Senat Sveučilišta, otvoren svim nositeljima studija na
   Sveučilištu. Odvojen mehanizam od st. 1, ne "ista stvar drugim riječima".

PRIZNAVANJE ECTS BODOVA (čl. 36 st. 3)
Ostvareni bodovi priznaju se kao da su ostvareni u okviru matičnog sveučilišnog studija, a bodovna
vrijednost kolegija odgovara onoj na studiju gdje se izvodi — ili kolegij može biti upisan kao posve
novi izborni kolegij u studentsku ispravu. Nositelj kolegija (host) potvrđuje ispunjenje obveza upisom
ECTS bodova, ocjene i svojim potpisom u studentsku ispravu. Pravilnik ne opisuje trostruku suglasnost
(matični program / ECTS koordinator / nositelj) kao na UNIZG-u — ne izmišljaj taj proces za Osijek;
jedino izričito navedeno jest potpis nositelja kolegija.

KAPACITET (čl. 36 st. 4)
Broj studenata koji smiju upisati pojedini izborni kolegij ograničen je kapacitetom sveučilišne
sastavnice, o čemu odlučuje ovlašteno tijelo sastavnice na prijedlog nositelja kolegija.

TROŠKOVI (čl. 36 st. 5)
Troškovi izvedbe kolegija u okviru mobilnosti unutar Sveučilišta određuju se Odlukom Senata —
centraliziranim, formalnim mehanizmom (za razliku od stare verzije iz 2015. koja je to prepuštala
"posebnom ugovoru"). Ako student pita za konkretan iznos, reci da je to regulirano Odlukom Senata
koju treba posebno potražiti (nije dio ovog Pravilnika) — NE izmišljaj broj.

MOBILNOST IZMEĐU SVEUČILIŠTA, UKLJUČUJUĆI INOZEMNU (čl. 37)
Mobilnost studenta među hrvatskim sveučilištima i između hrvatskih i inozemnih sveučilišta uređuje se
na temelju posebnih ugovora. Pravilnik ne daje nikakav detalj o postupku, prijavama ili rokovima.
Ne izvodi zaključke iz ovog teksta niti ga tretiraj analogno čl. 36. Za međunarodnu/Erasmus+
mobilnost konkretno, Sveučilište na svom popisu akata ima objavljen "Pravilnik o Erasmus+ programu
individualne međunarodne mobilnosti odlaznih i dolaznih studenata i (ne)nastavnog osoblja u okviru
ključne aktivnosti 1" — reci studentu da taj dokument postoji i da tamo treba tražiti proceduru; ne
opisuj mu sadržaj, jer nije pročitan. Za mobilnost prema drugom hrvatskom sveučilištu izvan
Erasmus+ okvira, uputi studenta na svoju sastavnicu / Ured za studente, jer Pravilnik ne daje daljnji
detalj.

ŠTO NE TVRDITI (razlike od UNIZG teksta, izbjegavaj analogiju)
- Nema formulacije "utvrđeno pravo bez uvjeta" kao UNIZG čl. 32 — Osijek uvjetuje upis time je li
  nositelj studija to predvidio u programu.
- Nema potvrde o (ne)postojanju uvjeta prosjeka ocjena (GPA) — Pravilnik to jednostavno ne spominje;
  ne tvrdi ni da postoji ni da ne postoji takav uvjet.
- Nema koncepta "tri suglasnosti" (matični program / ECTS koordinator / nositelj kolegija).
- Nema usporedbe s "paralelni studij" ili bilo kakvim pragom prosjeka (npr. FER-ov 4.5 na UNIZG-u).
- Nema sedmokoračnog procesa (referada, molba, potvrda o studiranju) — nije opisano u ovom Pravilniku;
  za konkretan postupak prijave uputi na sastavnicu / Ured za studente.

IZVOR
Pravilnik o studijima i studiranju Sveučilišta Josipa Jurja Strossmayera u Osijeku, čl. 36-37,
usvojen prosinac 2023. Tekst potvrđen preko nacrta iz javnog savjetovanja, rujan 2023.:
https://www.unios.hr/wp-content/uploads/2023/09/2-NACRT-prijedloga-Pravilnika-o-studijima-i-studiranju-javno-savjetovanje-9.2023.pdf
Usvajanje u prosincu 2023. potvrđeno preko popisa akata Pravnog fakulteta Osijek i FDMZ Osijek (oba
navode "Pravilnik o studijima i studiranju... (prosinac 2023.)"); izravan link na usvojeni PDF nije
bio dostupan. Postoji noviji "pročišćeni tekst" (ožujak 2025.) čiji sadržaj o mobilnosti NIJE
verificiran (PDF na gfos.unios.hr zaštićen lozinkom) — prije oslanjanja na ovo u produkciji, provjeri
kod Ureda za studente ili fakulteta je li poglavlje mijenjano.
"""

# ---------------------------------------------------------------- helpers


def _institutions(unios_only=True):
    doc = isvu.fetch("/pretrazivanje")
    import re
    out = []
    for r in re.findall(r"(?s)<tr[^>]*>(.*?)</tr>", doc):
        idm = re.search(r"podaci/(\d+)", r)
        cells = [isvu.strip(c) for c in re.findall(r"(?s)<td[^>]*>(.*?)</td>", r)]
        if idm and len(cells) >= 3:
            out.append({"id": int(idm.group(1)), "naziv": cells[0],
                        "nadredjena": cells[1], "grad": cells[2]})
    if unios_only:
        out = [x for x in out if "Sveučilište Josipa Jurja Strossmayera u Osijeku" in x["nadredjena"]]
    return out


ALIASES = {
    "aukos": 361, "efos": 10, "fazos": 79, "ferit": 165, "mathos": 372, "fpmoi": 372,
    "ftrr": 370, "fdmz": 356, "foozos": 245, "ffos": 122, "gfos": 149, "kbfdj": 2032,
    "kifos": 368, "mefos": 236, "biologija": 285, "fizika": 1312, "kemija": 291,
    "pravos": 111, "ptfos": 113,
}


def resolve_faculty(args):
    """faculty_id wins; otherwise match an alias, then a name substring.

    Either slot accepts either kind of value: models pass the id as a string and the
    name in `faculty_id` often enough that being strict here only produces crashes.
    """
    raw = args.get("faculty_id")
    if raw in (None, ""):
        raw = args.get("faculty")
    if isinstance(raw, bool):
        raw = None
    if isinstance(raw, (int, float)):
        return int(raw), None
    name = str(raw or "").strip()
    if name.isdigit():
        return int(name), None
    if not name:
        return None, "Give faculty_id or faculty. Call unios_institutions to list them."
    key = isvu.fold(name)
    if key in ALIASES:
        return ALIASES[key], None
    hits = [i for i in _institutions() if key in isvu.fold(i["naziv"])]
    if len(hits) == 1:
        return hits[0]["id"], None
    if not hits:
        return None, f"No SUJJS faculty matched {name!r}. Call unios_institutions."
    return None, ("Ambiguous, pick one: "
                  + "; ".join(f"{h['naziv']} (id {h['id']})" for h in hits[:10]))


def _prereqs_from(docs, course):
    """Union the prerequisites across every source page behind this course row."""
    seen, out = set(), []
    for p in course.get("_paths") or []:
        doc = docs.get(p)
        if not doc:
            continue
        for pr in isvu.parse_prereqs(isvu.fields(doc).get("Preduvjeti za upis predmeta")):
            sig = (isvu.fold(pr["kolegij"]), pr["uvjet"])
            if sig not in seen:
                seen.add(sig)
                out.append(pr)
    return out


def _walk_upstream(root, all_courses, max_depth=None):
    """The target course plus everything that feeds into it, transitively — currently just the
    course itself for almost every SUJJS course, since preduvjeti za upis is essentially
    unpublished here (0% measured across all 18 institutions). Exporting a whole programme
    instead gives 23-140+ disconnected course records (FERIT's smallest to Medicina's
    integrated programme) and answers a question nobody asked. Walking level by level costs
    nothing extra today since there's rarely anything to walk, but stays correct if a faculty
    starts publishing prerequisites.
    """
    by_name = {}
    for c in all_courses:
        by_name.setdefault(isvu.fold(c["naziv"]), c)

    limit = int(max_depth) if max_depth not in (None, "") else None
    chosen = {isvu.fold(root["naziv"]): root}
    frontier, levels, unresolved, truncated = [root], 0, [], False
    while frontier:
        if limit is not None and levels >= limit:
            truncated = True
            break
        docs = isvu.fetch_all([p for c in frontier for p in (c.get("_paths") or [])])
        nxt = []
        for c in frontier:
            c["preduvjeti"] = _prereqs_from(docs, c)
            for p in c["preduvjeti"]:
                k = isvu.fold(p["kolegij"])
                if k in chosen:
                    continue
                row = by_name.get(k)
                if row is None:                  # names a course outside this programme
                    unresolved.append({"course": c["naziv"],
                                       "missing_prerequisite": p["kolegij"]})
                    continue
                chosen[k] = row
                nxt.append(row)
        frontier = nxt
        levels += 1
    if truncated:
        for c in frontier:       # boundary nodes: leave their edges unfetched, so the export
            c.pop("_paths", None)  # does not report a wall of prerequisites it deliberately cut
    return {"courses": list(chosen.values()), "levels": levels,
            "unresolved": unresolved, "depth_truncated": truncated}


def _flatten(studies, out, depth=0):
    for s in studies:
        out.append({"smjer": s.get("sifraSmjera"), "naziv": s.get("nazivSmjera"),
                    "tip": s.get("nazivTipaSmjera"), "semestara": s.get("trajeElUstNast"),
                    "has_curriculum": bool(s.get("imaNastavniProgram")), "depth": depth})
        _flatten(s.get("listaPodredjenihStudija") or [], out, depth + 1)
    return out

# ---------------------------------------------------------------- dispatch


# Names a model plausibly reaches for instead of the real one. Silently ignoring an
# unrecognised argument is the worst outcome: an empty `query` matches every course, so
# the caller gets a confident answer about the wrong courses. Normalise, then reject.
ARG_ALIASES = {
    "search": "query", "q": "query", "naziv": "query", "name": "query", "course": "query",
    "institution_id": "faculty_id", "sastavnica": "faculty", "faculty_name": "faculty",
    "sifra": "code", "course_code": "code", "godina": "year", "academic_year": "year",
    "level": "razina", "programme": "smjer", "smjer_id": "smjer",
}


def check_args(tool, args):
    """Normalise aliases in place; return an error string if the call cannot work."""
    props = tool["inputSchema"].get("properties", {})
    for wrong, right in ARG_ALIASES.items():
        if wrong in args and right in props and args.get(right) in (None, ""):
            args[right] = args.pop(wrong)
    unknown = sorted(k for k in args if k not in props)
    if unknown and not props:
        # A tool that takes no parameters returns the same thing whatever it is handed, so a stray
        # argument cannot make the answer wrong. Rejecting it only risks the model giving up on a
        # call it should make. Strictness below exists to stop a dropped filter producing a
        # confident answer about the wrong thing; with no filters there is nothing to drop.
        args.clear()
    elif unknown:
        return (f"Unknown argument(s) {', '.join(unknown)} for {tool['name']}. "
                f"Accepted: {', '.join(sorted(props))}.")
    missing = [k for k in tool["inputSchema"].get("required", []) if args.get(k) in (None, "")]
    if missing:
        return f"Missing required argument(s) {', '.join(missing)} for {tool['name']}."
    return None


def call_tool(name, args):
    args = dict(args or {})
    tool = next((t for t in TOOLS if t["name"] == name), None)
    if tool is None:
        return {"error": f"Unknown tool {name!r}. Available: "
                         + ", ".join(t["name"] for t in TOOLS) + "."}
    bad = check_args(tool, args)
    if bad:
        return {"error": bad}
    year = int(args.get("year") or 2025)

    if name == "unios_mobility_rules":
        return {"rules": MOBILITY_RULES,
                "reminder": ("This is conditional, not an established right: čl. 36(1) requires the "
                             "student's own nositelj studija to have already provided for the course "
                             "in the studijski program. Tell the student to check that first, then "
                             "the form, fee, deadline and capacity are what's left for the referada. "
                             "Do not guess a fee or a deadline, and do not carry over UNIZG's "
                             "unconditional-right framing.")}

    if name == "unios_institutions":
        res = _institutions()
        q = args.get("query")
        if q:
            res = [x for x in res if isvu.fold(q) in isvu.fold(x["naziv"])]
        return {"count": len(res), "institutions": res}

    if name == "unios_courses":
        q = str(args.get("query") or "").strip()
        has_faculty = args.get("faculty_id") not in (None, "") or args.get("faculty") not in (None, "")
        if not q and not has_faculty:
            return {"error": "Give a query, or a faculty to list in full. Both cannot be omitted: "
                             "that would return all ~9,500 courses."}
        if has_faculty:
            fid, err = resolve_faculty(args)
            if err:
                return {"error": err}
            targets = [fid]
        else:
            targets = [i["id"] for i in _institutions()]
        limit = int(args.get("limit") or 40)

        # A search with no faculty needs one page per faculty. Warm them in one concurrent
        # batch, still at 3 req/s overall, so the parse loop below reads from cache: 37
        # sequential round trips took about 67s, which is latency, not rate limiting.
        if len(targets) > 1:
            isvu.fetch_all([isvu.course_list_path(f, year) for f in targets])

        needle = isvu.fold(q)
        hits, per_faculty = [], {}
        for fid in targets:
            try:
                courses = isvu.course_list(fid, year)
            except Exception:
                continue                     # one unreachable faculty must not sink the search
            for c in courses:
                if needle in isvu.fold(c["naziv"]):
                    hits.append({"faculty_id": fid, **c})
                    per_faculty[fid] = per_faculty.get(fid, 0) + 1

        # The old version returned as soon as it hit the limit, which meant a cross-faculty
        # search silently answered from the lowest-numbered faculties only, and said nothing
        # about the rest. Now every faculty is scanned and the truncation is spelled out.
        cross = len(targets) > 1
        if len(hits) > limit:
            out = {"count": limit, "total_matches": len(hits), "courses": hits[:limit],
                   "note": (f"Showing {limit} of {len(hits)} matches"
                            + (f" across {len(per_faculty)} faculties" if cross else "")
                            + ". Raise limit, narrow the query"
                            + (", or pass a faculty" if cross else "")
                            + ". These are NOT all the matches, so do not present them as if "
                              "they were."
                            + (" matches_per_faculty shows where the rest are." if cross else ""))}
            if cross:
                out["matches_per_faculty"] = per_faculty
            return out
        out = {"count": len(hits), "courses": hits}
        if cross:
            out["faculties_matched"] = len(per_faculty)
        return out

    if name == "unios_course":
        fid, err = resolve_faculty(args)
        if err:
            return {"error": err}
        code = str(args.get("code") or "")
        doc = isvu.fetch(f"/podaci/{fid}/akademskagodina/{year}/predmeti/predmet/{code}")
        f = isvu.fields(doc)
        if not f:
            return {"error": f"No course {code} at faculty {fid} in {year}/{year + 1}."}
        import re
        h2 = re.findall(r"(?s)<h2[^>]*>(.*?)</h2>", doc)
        progs = []
        i = doc.find("Predmet u nastavnom programu")
        if i > 0:
            for row in re.findall(r"(?s)<tr[^>]*>(.*?)</tr>", doc[i:]):
                c = [isvu.strip(x) for x in re.findall(r"(?s)<td[^>]*>(.*?)</td>", row)]
                if len(c) >= 5 and c[3].strip().isdigit():
                    progs.append({"programme": c[1], "razina": c[2],
                                  "semestar": int(c[3]), "status": c[4]})
        try:
            ects = float(f.get("ECTS bodovi", ""))
        except ValueError:
            ects = None
        return {
            "faculty_id": fid, "sifra": code, "naziv": isvu.strip(h2[-1]) if h2 else None,
            "ects": ects, "opterecenje": f.get("Opterećenje"),
            "opis": f.get("Opis predmeta"),
            "literatura_obavezna": f.get("Obavezna literatura"),
            "literatura_preporucena": f.get("Preporučena literatura"),
            "jezici": f.get("Jezici izvođenja nastave"),
            "nositelji": f.get("Nositelji"), "izvodaci": f.get("Izvođači"),
            "preduvjeti_upis": isvu.parse_prereqs(f.get("Preduvjeti za upis predmeta")),
            "preduvjeti_polaganje": isvu.parse_prereqs(f.get("Preduvjeti za polaganje predmeta")),
            "programmes": progs,
            "akademskaGodina": year,
            "source": (f"{isvu.BASE}/podaci/{fid}/akademskagodina/{year}"
                       f"/predmeti/predmet/{code}"),
        }

    if name == "unios_programmes":
        fid, err = resolve_faculty(args)
        if err:
            return {"error": err}
        levels = json.loads(isvu.fetch(f"/podaci/{fid}/dohvatirazine/{year}"))
        out = []
        for lv in levels:
            r = lv["sifraRazine"]
            for md in json.loads(isvu.fetch(f"/podaci/{fid}/razina/{r}/dohvatiizvedbe/{year}")):
                try:
                    studies = json.loads(isvu.fetch(
                        f"/podaci/{fid}/razina/{r}/izvedba/{md['oznaka']}/akgodina/{year}"))
                except Exception:
                    continue
                if studies:
                    out.append({"razina": r, "razina_naziv": lv["nazivRazineIVrste"],
                                "izvedba": md["oznaka"], "izvedba_naziv": md["naziv"],
                                "studiji": _flatten(studies, [])})
        return {"faculty_id": fid, "akademskaGodina": year, "razine": out}

    if name in ("unios_curriculum", "unios_dag_json"):
        fid, err = resolve_faculty(args)
        if err:
            return {"error": err}
        for k in ("razina", "izvedba", "smjer"):
            if args.get(k) in (None, ""):
                return {"error": f"Missing {k}. Call unios_programmes for this faculty first."}
        path = (f"/podaci/{fid}/nastavniprogram/{year}/razina/{int(args['razina'])}"
                f"/izvedba/{args['izvedba']}/smjer/{int(args['smjer'])}")
        doc = isvu.fetch(path)
        sems = isvu.split_semesters(doc)
        if not sems:
            return {"error": ("No curriculum published for that programme. Check "
                              "has_curriculum in unios_programmes.")}

        if name == "unios_curriculum":
            out = []
            for sem, chunk in sems:
                entry = {"semestar": sem, "obavezni": [], "izborne_grupe": []}
                for grp, items in isvu._grouped_tables(chunk):
                    if grp is None:
                        entry["obavezni"] = items
                    else:
                        entry["izborne_grupe"].append({"naziv": grp["naziv"],
                                                       "min_ects": grp["min_ects"],
                                                       "predmeti": items})
                out.append(entry)
            return {"faculty_id": fid, "akademskaGodina": year, "smjer": args["smjer"],
                    "semestri": out, "source": isvu.BASE + path}

        seen, courses = set(), []
        for sem, chunk in sems:
            for grp, items in isvu._grouped_tables(chunk):
                for it in items:
                    if not it["sifra"] or it["sifra"] in seen:
                        continue
                    seen.add(it["sifra"])
                    try:
                        ects = float(it["ects"])
                    except (TypeError, ValueError):
                        ects = 0.0
                    courses.append({"naziv": it["naziv"],
                                    "semestar": "zimski" if sem % 2 else "ljetni",
                                    "godina": (sem + 1) // 2,
                                    "status": "izborni" if grp else "obavezni",
                                    "ects": ects,
                                    "preduvjeti": [],
                                    "_paths": [f"/podaci/{fid}/akademskagodina/{year}"
                                               f"/predmeti/predmet/{it['sifra']}"]})

        # Merge before anything else looks at the list. A year-long course appears as a 0 ECTS
        # placeholder row and a credit-bearing row, and resolving `target` against the raw list
        # picked whichever came first: the placeholder, at 0 ECTS in the wrong semester.
        courses, merged = isvu.merge_duplicates(courses)

        target, chain = args.get("target"), None
        if target:
            hits = [c for c in courses if isvu.fold(str(target)) in isvu.fold(c["naziv"])]
            exact = [c for c in courses if isvu.fold(c["naziv"]) == isvu.fold(str(target))]
            if exact:
                hits = exact[:1]
            if not hits:
                near = sorted({c["naziv"] for c in courses})
                return {"error": f"No course in this programme matches {target!r}.",
                        "courses_in_programme": near}
            if len(hits) > 1:
                return {"error": f"{target!r} matches several courses; pass one exactly.",
                        "candidates": sorted({c["naziv"] for c in hits})}
            chain = _walk_upstream(hits[0], courses, args.get("max_depth"))
            courses = chain["courses"]

        # One concurrent batch rather than a round trip per course. Same 3 req/s ceiling;
        # it just stops waiting out ISVU's ~0.7s latency one course at a time. In target
        # mode _walk_upstream already fetched what it needed, so this only fills gaps.
        docs = isvu.fetch_all([p for c in courses for p in (c.get("_paths") or [])])
        for c in courses:
            if not c["preduvjeti"]:
                c["preduvjeti"] = _prereqs_from(docs, c)
            c.pop("_paths", None)
        courses, dropped = isvu.prune_dangling(courses)
        # Only report merges the caller can actually see in kolegiji.
        kept_names = {isvu.fold(c["naziv"]) for c in courses}
        merged = [m for m in merged if isvu.fold(m["naziv"]) in kept_names]
        missing = sum(1 for c in courses if not c["preduvjeti"])
        per_sem = {}
        for c in courses:
            per_sem.setdefault((c["godina"], c["semestar"]), 0.0)
            per_sem[(c["godina"], c["semestar"])] += c["ects"]
        return {
            # kolegiji sits at the top level on purpose: the app imports anything with a
            # `kolegiji` key, so this whole response is directly pasteable. Nesting it under
            # a wrapper key meant the import failed unless the model extracted exactly the
            # right sub-object first, which is not a thing to depend on.
            "kolegiji": courses,
            "how_to_use": ("Hand the user this response as pretty-printed JSON in a fenced code "
                           "block, then tell them to open the scheduler app, click 'Zalijepi "
                           "JSON', paste and confirm. Pasting the whole object is fine, the app "
                           "reads the kolegiji key and ignores the rest. Do not rewrite, reorder "
                           "or summarise the course objects; the app validates them strictly."),
            "summary": {
                "scope": f"prerequisite chain for {target!r}" if target else "whole programme",
                "courses": len(courses),
                "with_prerequisites": len(courses) - missing,
                "without_prerequisites": missing,
                "ects_per_semester": {f"godina {g} {s}": round(v, 1)
                                      for (g, s), v in sorted(per_sem.items())},
                **({"prerequisite_levels": chain["levels"],
                    "depth_truncated": chain["depth_truncated"]} if chain else {}),
            },
            "merged_duplicates": merged,
            "dropped_prerequisites": dropped,
            "caveat": ("An empty preduvjeti list means the faculty published nothing, not that the "
                       "course has no prerequisites. For a whole programme, ECTS per semester "
                       "should land near 30; for a target chain it will not, because the chain is "
                       "a slice and not a full workload. If dropped_prerequisites is not empty, "
                       "TELL THE USER: those edges pointed at courses outside this programme "
                       "(usually renamed or retired ones) and had to be removed, because the app "
                       "rejects any prerequisite naming a course it cannot find. If "
                       "merged_duplicates is not empty, mention it too: the curriculum listed "
                       "those names twice, typically a year-long course split into a 0 ECTS "
                       "placeholder plus a credit-bearing row, and the credit-bearing row was "
                       "kept. Both lists mean the graph is not a perfect copy of the curriculum."),
            "source": isvu.BASE + path,
        }

    return {"error": f"Unknown tool {name!r}."}


def handle_rpc(msg):
    """Minimal MCP JSON-RPC. Returns a response dict, or None for notifications."""
    mid, method, params = msg.get("id"), msg.get("method"), msg.get("params") or {}

    def ok(result):
        return {"jsonrpc": "2.0", "id": mid, "result": result}

    def err(code, message):
        return {"jsonrpc": "2.0", "id": mid, "error": {"code": code, "message": message}}

    if method == "initialize":
        return ok({
            "protocolVersion": params.get("protocolVersion", "2025-06-18"),
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "unios-courses", "version": "1.0.0"},
            "instructions": INSTRUCTIONS,
        })
    if method in ("notifications/initialized", "notifications/cancelled"):
        return None
    if method == "ping":
        return ok({})
    if method == "tools/list":
        return ok({"tools": TOOLS})
    if method == "tools/call":
        tname = params.get("name")
        try:
            res = call_tool(tname, params.get("arguments"))
        except Exception as e:                                    # surface, don't crash
            res = {"error": f"{type(e).__name__}: {e}"}
        return ok({
            "content": [{"type": "text",
                         "text": json.dumps(res, ensure_ascii=False, indent=2)}],
            "isError": bool(isinstance(res, dict) and res.get("error")),
        })
    return err(-32601, f"Method not found: {method}")
