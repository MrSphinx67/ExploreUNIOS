# explore_unizg MCP server — instructions the client sees (BASELINE / v1)

## Server instructions

Read-only access to the official University of Zagreb (UNIZG) course catalog, the ISVU public data
module that SRCE runs for the ministry. 37 constituent faculties, roughly 27,400 courses, academic
years back to 1976/77.

WHAT THIS IS FOR
Teaching data: what a course covers, its ECTS, semester, workload, prerequisites, and its required
and recommended literature; whole curricula semester by semester with elective groups; comparing how
different faculties teach the same subject; and the catalog half of horizontalna mobilnost.

HORIZONTALNA MOBILNOST, HALF ANSWERABLE
Omitting faculty_id from unizg_courses searches all 37 constituents at once, which answers "where else
is this taught" and "what would I be signing up for". What ISVU does NOT contain is the rules: who may
enrol at another faculty, quotas, deadlines, home-faculty approval, or how ECTS get recognised. Those
are on faculty websites (FKIT publishes them under /horizontalna_mobilnost/) and UNIZG central pages.
Answer the catalog half, then say plainly that eligibility and recognition have to be confirmed with
both faculties' student offices. Do not offer to filter by teaching language: it is published for only
~12% of courses and marked English for ~1%, so absence carries no information.

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

## Tools available

- `unizg_courses` — Find courses by name across a UNIZG faculty. Diacritic-insensitive, so
  'racunarstvo' matches 'Računarstvo'. Returns course codes to pass to unizg_course. Omit faculty_id
  to search all 37 constituents at once, which takes about 15 s and is the right way to answer
  'where else is this taught'. If more matched than the limit, the result says so and lists the count
  per faculty: report that, never imply completeness.
  Args: query, faculty_id, faculty, year, limit.
- `unizg_course` — Full detail for one course: description, learning outcomes (inside the
  description), required and recommended literature, ECTS, workload, prerequisites, and every
  programme it belongs to with its semester and obavezni/izborni status.
  Args: faculty_id, faculty, code (required), year.
- `unizg_programmes` — List a faculty's study programmes and modules, with their level, delivery mode
  and the ids needed by unizg_curriculum and unizg_dag_json.
  Args: faculty_id, faculty, year.
- `unizg_curriculum` — One study programme laid out semester by semester: mandatory courses plus each
  elective group with the minimum ECTS you must choose from it.
  Args: faculty_id, faculty, razina, izvedba, smjer, year.
- `unizg_dag_json` — Export courses as the JSON the scheduler web app imports, to build a prerequisite
  DAG and an earliest-completion schedule.
  Args: faculty_id, faculty, razina, izvedba, smjer, target, max_depth, year.
- `unizg_institutions` — The 37 UNIZG constituent faculties with their ISVU ids, cities and course
  counts. Args: query.
