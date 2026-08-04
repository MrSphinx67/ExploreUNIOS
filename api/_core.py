"""Shared MCP core: tool definitions, dispatch, and the server instructions.

Imported by api/mcp.py (remote HTTP, for the Claude web and mobile apps) and by
mcp/stdio_server.py (local stdio, for Claude Desktop and Claude Code). Depends only
on the stdlib plus the ISVU client in skills/unizg-courses/scripts/isvu.py.
"""
import importlib.util
import json
import os
import sys

os.environ.setdefault("ISVU_CACHE", "/tmp/isvu-cache")   # serverless: only /tmp is writable

_HERE = os.path.dirname(os.path.abspath(__file__))
_CANDIDATES = [
    os.path.join(_HERE, "..", "skills", "unizg-courses", "scripts", "isvu.py"),
    os.path.join(_HERE, "skills", "unizg-courses", "scripts", "isvu.py"),
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

INSTRUCTIONS = """\
Read-only access to the official University of Zagreb (UNIZG) course catalog, the ISVU public data
module that SRCE runs for the ministry. 37 constituent faculties, roughly 27,400 courses, academic
years back to 1976/77.

WHAT THIS IS FOR
Teaching data: what a course covers, its ECTS, semester, workload, prerequisites, and its required
and recommended literature; whole curricula semester by semester with elective groups; comparing how
different faculties teach the same subject; and the catalog half of horizontalna mobilnost.

HORIZONTALNA MOBILNOST: TAKING COURSES AT A SECOND UNIZG FACULTY
Students ask this constantly, in both languages, and the answer starts with yes. Studying at a second
UNIZG faculty alongside your own is an established right, set out in the Pravilnik o studiranju
article 32 and in the Smjernice za horizontalnu mobilnost (Odbor za upravljanje kvalitetom,
19 November 2024). Never answer as though it might not be permitted, never tell a student to go find
out WHETHER it is possible, and never invent an eligibility bar. Call unizg_mobility_rules for the
full briefing with citations and links; the essentials, so you are never stuck without it:

- What it is: while enrolled on your home programme you additionally enrol individual courses from
  other UNIZG programmes that your own does not teach, with passed exams and ECTS recognised. You stay
  a normal student of your home faculty. Foreign-language courses inside UNIZG count too, including
  ones aimed at incoming exchange students. Not Erasmus, which is a different university.
- Conditions are few: the level must match (prijediplomska/diplomska/poslijediplomska; the LEVEL
  governs, not sveucilisni vs strucni), and the course must not be taught on your own programme.
  There is NO grade-average requirement at university level. The only real constraint is the host
  faculty's capacity for that course, and uptake is low enough that it rarely binds.
- Approval is three consents the student collects: their home programme's competent body, the host
  faculty's ECTS coordinator, and the course leader. A potvrda then names the course and its ECTS.
- Failing costs nothing. A course taken this way carries no penalty at home and does not hurt the home
  average, which makes one course a cheap way to test a field. Say this; students do not expect it.
- ECTS recognition is opt-in and the student starts it through their own referada: counted toward the
  degree and entered in the dopunska isprava o studiju if the learning outcomes match, otherwise
  recorded as additional credits outside the degree total. Do not say the grade lands in the home
  programme automatically.
- Paralelni studij is the other route: the whole second programme, two degrees, a strict entry bar
  (FER's pravilnik sets 4.5). Horizontalna mobilnost has no such bar, and you can switch to paralelni
  later, so starting small closes nothing.

What is genuinely local, and the only thing to send them to the referada for: the form, the fee, the
deadline, and whether that course has room. Many faculties publish none of this. The Smjernice audited
every constituent's website in 2024 and found the information mostly absent, buried or stale, so a
missing web page is evidence about that faculty's website and not about the student's rights. Say it
that way. If you do not know a fee or a deadline, say the faculty sets it. Do not guess a number.

ISVU answers the catalog half: omitting faculty_id from unizg_courses searches all 37 constituents at
once, which is how you answer "where else is this taught" and "what would I actually be signing up
for". Do not offer to filter by teaching language: it is published for only ~12% of courses and marked
English for ~1%, so absence carries no information.

SCOPE LIMIT, PLEASE RESPECT IT
This is not a directory of academics. ISVU prints teacher names on every course page, so they appear
in results, and it is fine to say who teaches a course when answering about that course. Do not use
these tools to build a person index, search or filter by professor, aggregate somebody's teaching
portfolio, rank people, or collect contact details. A name is an attribute of a course, never a row
to query. If asked for people-centric analysis, say it is out of scope here.

DATA COVERAGE, STATE THIS HONESTLY
Semester, programme and obavezni/izborni status are ~98% populated. Course leader ~82%. Descriptions
only 46%, learning outcomes (ishodi ucenja) only 34%, and prerequisites about 10%. Coverage is
bimodal, not evenly thin: FSB and PMF-matematicki fill in nearly everything, while Agronomski, FOI,
MEF, Kinezioloski, EFZG and Pravni publish no learning outcomes at all. When a field comes back
empty, say the faculty did not publish it. Never imply the course lacks the thing.

Learning outcomes are not a separate field. Where present they sit inside the description under
headings such as "OCEKIVANI ISHODI UCENJA NA RAZINI PREDMETA:" (PMF) while other faculties write
"Ciljevi kolegija" and "Sadrzaj kolegija" and no outcomes at all. Read them out of the description.

A course can belong to several programmes at different semesters with different obavezni/izborni
status, so treat semester as per-programme, never as one value for the course.

PMF is two separate institutions, 37 (matematicki odsjek) and 119 (prirodoslovni odsjeci). When the
user says "PMF" search both and say which one a result came from. Institution 9996 is the central
university entity, not an umbrella: its courses are real, separate, mostly interdisciplinary.

BUILDING A PREREQUISITE GRAPH
unizg_dag_json returns courses in the exact JSON the companion scheduler web app imports, so a user
can paste it straight in and get a prerequisite DAG with an earliest-completion schedule. Offer this
whenever someone asks to plan or visualise what leads to a course.

Pass `target` in almost every case. It returns the named course plus only what transitively feeds
into it, which is what "what do I need before X" actually means and is normally 5-20 courses: a
graph someone can read. Omitting `target` exports the entire programme, which for Fizika/istrazivacki
is 103 courses and draws an unusable hairball. Only omit it when the user explicitly wants the whole
programme laid out. `max_depth` bounds the walk if even the chain is too big; max_depth 1 gives just
the direct prerequisites.

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
        "name": "unizg_courses",
        "description": ("Find courses by name across a UNIZG faculty. Diacritic-insensitive, so "
                        "'racunarstvo' matches 'Računarstvo'. Returns course codes to pass to "
                        "unizg_course. Omit faculty_id to search all 37 constituents at once, "
                        "which takes about 15 s and is the right way to answer 'where else is "
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
        "name": "unizg_course",
        "description": ("Full detail for one course: description, learning outcomes (inside the "
                        "description), required and recommended literature, ECTS, workload, "
                        "prerequisites, and every programme it belongs to with its semester and "
                        "obavezni/izborni status."),
        "inputSchema": {
            "type": "object",
            "properties": {
                "faculty_id": {"type": "integer"},
                "faculty": {"type": "string", "description": "Faculty name or abbreviation, instead of the id."},
                "code": {"type": "string", "description": "ISVU course code (sifra), from unizg_courses."},
                "year": {"type": "integer"},
            },
            "required": ["code"],
        },
    },
    {
        "name": "unizg_programmes",
        "description": ("List a faculty's study programmes and modules, with their level, delivery "
                        "mode and the ids needed by unizg_curriculum and unizg_dag_json. Only "
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
        "name": "unizg_curriculum",
        "description": ("One study programme laid out semester by semester: mandatory courses plus "
                        "each elective group with the minimum ECTS you must choose from it."),
        "inputSchema": {
            "type": "object",
            "properties": {
                "faculty_id": {"type": "integer"},
                "faculty": {"type": "string", "description": "Faculty name or abbreviation, instead of the id."},
                "razina": {"type": "integer", "description": "Study level code from unizg_programmes."},
                "izvedba": {"type": "string", "description": "Delivery mode code, usually 'R'."},
                "smjer": {"type": "integer", "description": "Programme id from unizg_programmes."},
                "year": {"type": "integer"},
            },
            "required": ["razina", "izvedba", "smjer"],
        },
    },
    {
        "name": "unizg_dag_json",
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
        "name": "unizg_institutions",
        "description": "The 37 UNIZG constituent faculties with their ISVU ids, cities and course counts.",
        "inputSchema": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "Filter by name fragment."}},
        },
    },
    {
        "name": "unizg_mobility_rules",
        "description": ("The rules for taking courses at a second UNIZG faculty (horizontalna "
                        "mobilnost) and how it differs from paralelni studij: what the right is, the "
                        "conditions, who approves, how ECTS get recognised, what failing costs, the "
                        "step-by-step process, and verified official links. Static text, no network "
                        "call. Call this for any 'can I study at two faculties / another faculty' "
                        "question before answering, so the answer carries the actual rules and "
                        "citations instead of guesses. Cross-faculty study IS permitted; what varies "
                        "per faculty is only the paperwork."),
        "inputSchema": {"type": "object", "properties": {}},
    },
]

# --------------------------------------------------------- horizontalna mobilnost
# The rules half of the cross-faculty question. ISVU has none of this, and before it was written in
# here every model got the same question wrong in one of two ways: small ones refused ("not in the
# catalog") and larger ones affirmed but invented the fee, the deadline and the recognition rule.
# Both readings hurt a student, so the text below is deliberately specific about what is settled
# university-wide versus what is genuinely per-faculty. Sources are cited so answers can be checked;
# the fuller version with per-faculty detail lives in
# skills/unizg-courses/references/horizontalna-mobilnost.md.

MOBILITY_RULES = """\
HORIZONTALNA MOBILNOST: TAKING COURSES AT ANOTHER UNIZG FACULTY

This is an established right, not a favour granted case by case. It is set out in the Pravilnik o
studiranju Sveucilista u Zagrebu, article 32, and FOI's own procedure opens by saying "studentu se
odobrava ostvarenje PRAVA na horizontalnu mobilnost". Answer the student on that footing. Never imply
cross-faculty enrolment might not be allowed, and never send them off to find out whether it is
possible; what they need to confirm is the paperwork.

WHAT IT IS
Official definition, Smjernice za horizontalnu mobilnost, Odbor za upravljanje kvalitetom, 19 November
2024, KLASA 602-03/24-29/12: "Horizontalna mobilnost podrazumijeva mogucnost studenata da tijekom svog
maticnog studija upisuje pojedine kolegije drugih studija (studijskih programa) unutar Sveucilista,
koji se ne izvode na maticnom studiju, uz priznavanje polozenih ispita i ostvarenih bodova prema
ECTS-u."

You stay a normal student of your home faculty and nothing about that status changes; you additionally
enrol, attend and sit exams in individual courses elsewhere in UNIZG. It also covers foreign-language
courses inside UNIZG, including ones aimed at incoming exchange students. It is not Erasmus, which
means another university entirely.

CONDITIONS, AND HOW FEW THERE ARE
- The level must match: prijediplomska / diplomska / poslijediplomska. The LEVEL governs, not the type
  of study: "mjerodavna je razina ..., a ne vrsta studija (sveucilisni, strucni)". Basis: ZVOZD art.
  67(3), Zakon o HKO art. 7(6).
- The course must not be taught on your own programme. That is what makes it mobility.
- There is NO grade-average requirement at university level. Do not invent one.
- The only real constraint is the host faculty's capacity for that course, decided by its competent
  body on the course leader's proposal. Uptake is low university-wide ("prisutna ... ali ne u
  znacajnijoj mjeri"), so capacity rarely binds in practice.

WHO APPROVES: three consents, and the student collects them
1. the competent body of the student's home programme,
2. the ECTS coordinator of the host sastavnica,
3. the nositelj of the chosen course.
A potvrda is then issued naming the course and fixing its ECTS value. The host course leader enters
the grade and ECTS into the information system.

FAILING COSTS NOTHING
A course taken this way carries no penalty at the home faculty if not passed, and does not damage the
home average. Tell students this: it turns one course into a cheap experiment in a new field, and they
do not expect it.

ECTS RECOGNITION IS OPT-IN, TWO ROUTES
The student starts it through their own referada, proving the credits with a certified transcript.
- Counted toward the degree, and entered in the dopunska isprava o studiju, if the course's learning
  outcomes match the home programme's.
- Otherwise recognised as additional credits: recorded, but outside the degree total.
If they never ask, the credits simply sit at the host faculty as a separate record. Do not tell a
student the grade lands in their home programme automatically.

VERSUS PARALELNI STUDIJ
Paralelni studij means enrolling the entire second programme and ending with two degrees, behind a
strict entry bar (FER's pravilnik sets a 4.5 average). Horizontalna mobilnost means picking individual
courses, keeps one degree, and has no such bar. A student can move from horizontalna mobilnost to
paralelni studij later, so starting with one or two courses closes nothing off.

THE PROCESS
1. Choose courses: browse the programmes that interest you and read the real syllabi, since much of
   what sounds interesting turns out not to be. Order candidates by prerequisites. ISVU answers this
   part; use the other tools here.
2. Check it physically fits: lay the host timetable over your home one. If it does not fit, drop a
   course or push it a year. Expect an exam collision eventually.
3. Contact the nositelj of the course and agree how you will attend and sit the exam.
4. Ask your own referada what they need. Some faculties require nothing of the student here.
5. Apply to the host faculty's referada: what you want to enrol and why, a short motivation, plus a
   potvrda o studiranju and that faculty's official molba form from its website. Some charge a small
   fee for the molba. Forms and fees are per-faculty.
6. Time it to the regular enrolment window. FOI requires it "prije upisa u semestar u kojem ostvaruje
   mobilnost". Mailing the referada during normal enrolment is when they can actually enrol you.
7. The student then appears on Studomat with two faculties.
Transport is a real hidden cost when the two faculties are far apart, and the student bears it.

WHY THE STUDENT CANNOT FIND THIS WRITTEN DOWN
The Smjernice audited every constituent's website in 2024 and found, in the University's own words,
that most publish no detailed enrolment conditions online, only a minority document the approval
procedure, ECTS-recognition information is rare and buried inside pravilnici, capacity limits are
"gotovo uopce nije dostupna online", information is often stale, and some faculties link only
international mobility. A faculty having no page is therefore evidence about that faculty's website,
not about the student's rights. Say it that way rather than letting the gap read as a prohibition.
Named good practice: Farmaceutsko-biokemijski fakultet, Pravni fakultet, Fakultet organizacije i
informatike.

WHAT TO SEND THEM TO THE REFERADA FOR
The form, the fee, the deadline, and whether that course has room. Nothing else. Not whether
cross-faculty study is allowed, not whether they need a certain average, not whether their faculty
"permits" it. Those are settled university-wide. If you do not know a fee or a deadline, say the
faculty sets it and let them ask. Do not guess a number.

ANSWERING IN CROATIAN
Most students ask this in Croatian, so answer in Croatian, and copy the terms from this list rather
than transliterating the folded spellings used above. Smaller models measurably mangle these: one
answered "okoncana prava" (concluded rights) for an established right, wrote the Serbian "zavisi" for
"ovisi", and leaked Cyrillic characters into a Croatian sentence. Correct forms, with diacritics:

  horizontalna mobilnost · paralelni studij · matični studij · matični fakultet · sastavnica
  kolegij · predmet · nositelj kolegija · ECTS koordinator · referada · studentska služba
  prijediplomski · diplomski · poslijediplomski · razina studija · vrsta studija
  položeni ispiti · priznavanje bodova · dopunska isprava o studiju · prosjek ocjena
  potvrda o studiranju · molba · obrazac · rok · upis · kapacitet · Studomat
  utvrđeno pravo (NOT "okončano") · ovisi o fakultetu (NOT "zavisi") · ishodi učenja

Croatian uses č ć š ž đ. Do not drop them, and never mix in Cyrillic.

OFFICIAL LINKS, all verified 2026-08-02
- UNIZG central page:
  https://www.unizg.hr/studiji-i-studiranje/upisi-stipendije-priznavanja/horizontalna-mobilnost/
- Smjernice za horizontalnu mobilnost (PDF): https://www.unizg.hr/fileadmin/rektorat/\
Studiji_studiranje/Studiji/Kvaliteta/Kvaliteta1/Smjernice_za_horizontalnu_mobilnost_za_web.pdf
- FKIT, a fully worked section:
  https://www.fkit.unizg.hr/horizontalna_mobilnost/horizontalna_mobilnost_studenata_fkit-a
- FOI procedure: https://www.foi.unizg.hr/hr/horizontalna-mobilnost
- Pravni fakultet, with per-year course lists in Croatian and in foreign languages:
  https://www.pravo.unizg.hr/studiji/horizontalna-mobilnost
Faculty URLs rot. If one 404s, say so and point at the UNIZG central page and the referada rather
than guessing a replacement path.
"""

# ---------------------------------------------------------------- helpers


def _institutions(unizg_only=True):
    doc = isvu.fetch("/pretrazivanje")
    import re
    out = []
    for r in re.findall(r"(?s)<tr[^>]*>(.*?)</tr>", doc):
        idm = re.search(r"podaci/(\d+)", r)
        cells = [isvu.strip(c) for c in re.findall(r"(?s)<td[^>]*>(.*?)</td>", r)]
        if idm and len(cells) >= 3:
            out.append({"id": int(idm.group(1)), "naziv": cells[0],
                        "nadredjena": cells[1], "grad": cells[2]})
    if unizg_only:
        out = [x for x in out if "Sveučilište u Zagrebu" in x["nadredjena"]]
    return out


ALIASES = {
    "fer": 36, "pmf": 119, "pmf-mat": 37, "pmf matematicki": 37, "pmf-prir": 119,
    "ffzg": 130, "fsb": 120, "efzg": 67, "pbf": 58, "fkit": 125, "foi": 16,
    "mef": 108, "pravni": 66, "arhitektonski": 54, "agronomski": 178, "erf": 13,
    "fpzg": 15, "fpz": 135, "rgn": 195, "kif": 34, "vef": 53, "adu": 1053,
    "alu": 381, "muza": 1349, "ttf": 117, "grad": 82, "grf": 128, "geof": 7,
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
        return None, "Give faculty_id or faculty. Call unizg_institutions to list them."
    key = isvu.fold(name)
    if key in ALIASES:
        return ALIASES[key], None
    hits = [i for i in _institutions() if key in isvu.fold(i["naziv"])]
    if len(hits) == 1:
        return hits[0]["id"], None
    if not hits:
        return None, f"No UNIZG faculty matched {name!r}. Call unizg_institutions."
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
    """The target course plus everything that feeds into it, transitively.

    Exporting a whole programme gives an unreadable graph: Fizika/istrazivacki is 103
    courses, and answers a question nobody asked. What you actually want is "what do I
    need before I can take X", which is the upstream closure of X and usually a handful of
    courses. Walking it level by level also fetches far fewer pages than the whole
    programme, since it only touches courses that turn out to matter.
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

    if name == "unizg_mobility_rules":
        return {"rules": MOBILITY_RULES,
                "reminder": ("Cross-faculty study is permitted university-wide. Only the form, the "
                             "fee, the deadline and course capacity are per-faculty. Do not tell the "
                             "student to check whether it is allowed, and do not guess a fee or "
                             "deadline.")}

    if name == "unizg_institutions":
        res = _institutions()
        q = args.get("query")
        if q:
            res = [x for x in res if isvu.fold(q) in isvu.fold(x["naziv"])]
        return {"count": len(res), "institutions": res}

    if name == "unizg_courses":
        q = str(args.get("query") or "").strip()
        has_faculty = args.get("faculty_id") not in (None, "") or args.get("faculty") not in (None, "")
        if not q and not has_faculty:
            return {"error": "Give a query, or a faculty to list in full. Both cannot be omitted: "
                             "that would return all ~27,400 courses."}
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

    if name == "unizg_course":
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

    if name == "unizg_programmes":
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

    if name in ("unizg_curriculum", "unizg_dag_json"):
        fid, err = resolve_faculty(args)
        if err:
            return {"error": err}
        for k in ("razina", "izvedba", "smjer"):
            if args.get(k) in (None, ""):
                return {"error": f"Missing {k}. Call unizg_programmes for this faculty first."}
        path = (f"/podaci/{fid}/nastavniprogram/{year}/razina/{int(args['razina'])}"
                f"/izvedba/{args['izvedba']}/smjer/{int(args['smjer'])}")
        doc = isvu.fetch(path)
        sems = isvu.split_semesters(doc)
        if not sems:
            return {"error": ("No curriculum published for that programme. Check "
                              "has_curriculum in unizg_programmes.")}

        if name == "unizg_curriculum":
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
            "serverInfo": {"name": "unizg-courses", "version": "1.0.0"},
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
