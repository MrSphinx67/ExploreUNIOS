---
name: unizg-courses
description: >-
  Look up University of Zagreb (UNIZG) courses, curricula, syllabi and course literature from the
  official ISVU public catalog. Use whenever the user asks what a UNIZG course covers, its ECTS or
  semester or workload, its prerequisites (preduvjeti), its required or recommended reading
  (literatura), which courses a study programme contains, what is taught at a given faculty, which
  courses are taught in English, how a curriculum has changed over the years, or how the same
  subject is taught at different UNIZG faculties. Also use for any question about studying at a
  second UNIZG faculty alongside your own: horizontalna mobilnost, taking or enrolling individual
  courses at another faculty, whether that is allowed and what the conditions are, how ECTS get
  recognised, and how it differs from paralelni studij. Covers all 37 UNIZG constituents and ~27,400
  courses. Croatian terms that should trigger this: kolegij, predmet, preduvjeti, ishodi ucenja,
  nastavni program, studijski program, ECTS, semestar, literatura, sastavnica, horizontalna
  mobilnost, paralelni studij, dva fakulteta, drugi faks, referada, molba, priznavanje ECTS-a.
---

# UNIZG course catalog (ISVU)

Queries the ISVU public data module, the official catalog SRCE runs for the ministry. It is the same
database the student offices use, exposed read-only, server-rendered, no auth. `robots.txt` is
`Allow: /` with only `/javno/` disallowed, so `/visokaucilista/` is explicitly permitted.

## Scope: courses, not people

This skill answers questions about **teaching**: courses, curricula, literature, what you can learn
where. It is deliberately not a directory of academics.

ISVU prints `Nositelji` and `Izvođači` on every course page, so teacher names are in the responses
and it is fine to say who teaches a course when answering about that course. That is information the
faculty publishes for students.

Do not use this skill to build a person index, filter or search by professor, aggregate someone's
teaching portfolio, rank or compare people, or collect contact details. **A name is an attribute of
a course, never a row you can query.** If the user wants people-centric analysis, say that is out of
scope here.

## Use the script

`scripts/isvu.py` handles caching, the 3 req/s ceiling, 429 hard-stop, diacritic-insensitive search
and all the parsing traps below. Prefer it over hand-rolling requests.

```bash
export ISVU_CONTACT="you@example.com"      # goes in the User-Agent; set it

python3 scripts/isvu.py institutions --unizg          # 37 constituents + their ids
python3 scripts/isvu.py courses 36 --search racunarstvo --limit 20
python3 scripts/isvu.py course 119 63146              # detail: opis, literatura, preduvjeti, programmes
python3 scripts/isvu.py programmes 54                 # programme/module tree
python3 scripts/isvu.py curriculum 54 3 R 2           # one programme, by semester
python3 scripts/isvu.py dag 54 3 R 2                  # export in the scheduler's kolegiji.json schema
python3 scripts/isvu.py selfcheck                     # verify the undocumented endpoints still work
```

Responses cache to `~/.cache/isvu` (override with `ISVU_CACHE`), so repeat queries are free. Run
`selfcheck` first if anything looks structurally wrong: three endpoints are undocumented internals
and could move without notice.

Institution ids, course counts and per-faculty data-coverage figures: `references/institutions.md`.
Read that before telling a user a field is empty, because at many faculties it never got filled in.

The rules for taking courses at a second UNIZG faculty: `references/horizontalna-mobilnost.md`. **Read
that before answering any question about studying at two faculties**, because ISVU holds none of it and
the answer is "yes, this is an established right" — a student who gets hedged at here is being
misinformed, not protected.

## Endpoints

Base `https://www.isvu.hr/visokaucilista/hr`. `{inst}` is the ISVU institution id, `{yyyy}` the
starting year of the academic year (2025 means 2025/2026).

| Path | Returns |
|---|---|
| `/pretrazivanje` | all 125 institutions with ids |
| `/podaci/{inst}/predmeti` | full course list, one page, no pagination |
| `/podaci/{inst}/predmeti/akademskagodina/{yyyy}` | same, chosen year (back to 1976) |
| `/podaci/{inst}/akademskagodina/{yyyy}/predmeti/predmet/{code}` | course detail |
| `/podaci/{inst}/dohvatirazine/{yyyy}` | study levels, **JSON** |
| `/podaci/{inst}/razina/{r}/dohvatiizvedbe/{yyyy}` | delivery modes, **JSON** |
| `/podaci/{inst}/razina/{r}/izvedba/{i}/akgodina/{yyyy}` | programme tree, **JSON** |
| `/podaci/{inst}/nastavniprogram/{yyyy}/razina/{r}/izvedba/{i}/smjer/{s}` | curriculum by semester |
| `/podaci/{inst}/akademskikalendar` | academic calendar |

Add `/en/` instead of `/hr/` for English. Levels seen: 3 prijediplomski, 4 diplomski, 10 doktorski,
11 specijalistički, but they vary per institution and year so **always ask `dohvatirazine`** rather
than assuming.

## The shortcut that matters

A course detail page ends with a `Predmet u nastavnom programu` table:
`Šifra studija | Naziv studija | Razina | Semestar izvođenja | obavezni/izborni`.

It is a reverse index, so one course fetch tells you every programme the course belongs to, at which
semester, and whether it is mandatory there. For single-course questions you never need to walk the
programme tree. Walk the tree only when the user wants a whole curriculum or the elective-group rules.

Because of this, `semestar` is not a scalar: one course legitimately sits in several programmes at
different semesters with different status. Never flatten it to one value.

## Parsing traps

These all cost me real debugging. The script handles them; respect them if you go direct.

**Course detail fields are a `<dl>`**, as `<dt><span class="karticaDetaljno">Label:</span></dt><dd>value</dd>`.
Every field is optional and renders only when populated, so **read whatever labels are present rather
than looking for a fixed list.** That is how the two prerequisite fields get missed.

**Prerequisites do exist in ISVU**, as `Preduvjeti za upis predmeta` and
`Preduvjeti za polaganje predmeta`. Format is `Course name (položen)` / `Course name (odslušan)`,
which maps onto `polozen` / `odslusan`. Coverage is thin (~10% and ~4% of courses) but spread over
22 of 37 faculties. Absent is not the same as none: many courses genuinely have no prerequisites,
and many faculties simply never filled the field.

**Course list column order is `Naziv` then `Šifra`**, name first. The per-course hrefs sit *outside*
the `<tr>` elements, and some institutions link course names while others do not, so read the code
from its cell and parse off the header row.

**Curriculum semesters are tab panes, not headings.** Split on
`<div id="semestarN" class="tab-pane">`. Do not split on the visible "Semestar N" text: those are
nav-tab labels that all appear before any content, so text-splitting silently assigns every course
to the last semester. Sanity check: a Croatian programme should come out near 30 ECTS per semester.
If every course lands in one semester, this is the bug.

**Curriculum table columns differ per faculty.** FER uses `P A L S TJ`, FHS uses `P S PK LK SJ TJ`.
Parse the header row; never assume fixed columns. A legend at the page bottom expands the letters.

**Only fetch a curriculum when `imaNastavniProgram == 1`.** Parent nodes in the programme tree
frequently have no curriculum of their own; the tree recurses via `listaPodredjenihStudija`.

**Match diacritic-insensitively** (č/c, ć/c, š/s, ž/z, đ→dj) or Croatian search silently fails.

**Prerequisites dangle.** They are free text and routinely name courses outside the programme you are
exporting, usually renamed or retired ones. Real case at Arhitektonski: *Nosive konstrukcije II*
requires *Arhitektonske konstrukcije I*, but the curriculum only contains *Arhitektonske konstrukcije
**i materijali** I*. The scheduler app rejects the entire import if any prerequisite names a course
it cannot find, so `dag` prunes those edges via `prune_dangling()` and reports them on stderr. Never
drop them silently: the resulting graph is genuinely incomplete and the user should know which edges
went missing.

**Course names repeat within one curriculum**, and the scheduler keys its graph by name, so it refuses
the import with `Dvostruki kolegij`. Deduping by šifra is not enough because the rows often carry different
šifre. Across PMF-119's curricula, 91 duplicate-name groups survive a šifra-level dedupe. Causes: a
year-long course split into a placeholder and a credit-bearing row (*Klasična elektrodinamika* is 51520
in semester 5 at 0 ECTS and 51521 in semester 6 at 12 ECTS); a course offered in either of two
semesters; or a relisting under a new šifra after a revision. `merge_duplicates()` keeps the
highest-ECTS row, earliest semester breaking ties, and unions the prerequisites, because the placeholder
row sometimes carries them instead. **Merge before resolving anything by name**, or a name lookup picks
whichever row came first, which is the 0 ECTS placeholder.

**A whole programme is usually the wrong export.** Fizika/istraživački is 103 rows and draws an
unreadable graph. What "what do I need for X" means is the upstream closure of X, normally 5–20 courses.
Walk it level by level from the target: smaller *and* cheaper, since you only fetch courses that turn
out to feed in, 8 pages instead of 99 for the Klasična elektrodinamika chain.

**`semestar` is a hard constraint on placement, so get it right.** The scheduler puts a course in the
first slot that is both after all its prerequisites and in the course's own season (zimski = odd slots,
ljetni = even), because a course is only taught in one season. Two consecutive same-season courses
therefore cannot sit in consecutive slots, and a chain of depth *n* can need more than *n* semesters.
Never guess `semestar` to make a schedule look tighter: it changes the answer.

## Coverage honesty

Measured over 370 sampled courses across all 37 constituents:

| field | coverage |
|---|---|
| semester, programme, obavezni/izborni | 98% |
| nositelj | 82% |
| opis predmeta | 46% |
| ishodi učenja | 34% |
| preduvjeti za upis | 10% |
| jezici izvođenja nastave | 12% |

Ishodi učenja are **not a structured field**. Where present they are prose inside `Opis predmeta`
under institution-specific headings such as `OČEKIVANI ISHODI UČENJA NA RAZINI PREDMETA:` (PMF) while
others write `Ciljevi kolegija` / `Sadržaj kolegija` and no outcomes at all. Extract by segmenting
the description text.

Coverage is bimodal, not evenly thin: FSB and PMF-matematički have ishodi on essentially every
course, while Agronomski, FOI, MEF, Kineziološki, EFZG and Pravni have none. **When a field is
missing, say the faculty did not publish it rather than implying the course lacks it.**

## Good questions this answers

- what a course covers, its ECTS, workload and its reading list
- a whole programme laid out semester by semester, with elective groups and their ECTS minimums
- prerequisites, where the faculty published them
- comparing how several faculties teach the same subject, since course lists span all constituents
- **horizontalna mobilnost, both halves.** The catalog half: omit
  `faculty_id` from `courses` to search all 37 constituents at once (one page per faculty, fetched
  concurrently, about 15 s), then read the syllabus, ECTS, workload and semester of anything promising.
  A truncated result reports `total_matches` and `matches_per_faculty`; pass those on rather than
  presenting the first page as the whole answer. The rules half is not in ISVU but it *is* settled, and
  it is written up in `references/horizontalna-mobilnost.md` — **read that before answering any
  "can I take courses at another faculty" question.** Short version: it is an established right under
  the Pravilnik o studiranju article 32, there is no grade-average requirement, failing costs nothing
  at the home faculty, and only the form, the fee, the deadline and course capacity are per-faculty.
  Do **not** answer as though it might not be permitted, and do **not** invent a fee or a deadline.
  Do **not** offer to filter by language of instruction: `Jezici izvođenja nastave` is published for
  ~12% of courses and marked English for ~1% (measured over 120 courses at 10 faculties), and it is
  concentrated, VEF fills it on every course, most faculties on none. An absent value says nothing
  about the actual teaching language.
- how a curriculum changed over time, since years go back to 1976/77 and 2026/2027 is already published
- real cost of a course: `Opterećenje` gives the per-type hours, so hours-per-ECTS is computable and
  nobody else publishes it

## Being a good citizen

Descriptive User-Agent with a real contact address, at most 3 req/s, back off on 5xx, **stop on 429**,
cache everything, prefer off-peak for anything bulk. `fetch_all()` fetches concurrently but shares one
global send-slot queue, so the 3 req/s ceiling holds no matter how many workers run; a 429 in any worker
halts the whole batch. If you fetch by hand, keep both properties. This is a publicly funded service on modest
hardware. Bulk-extracting and republishing the whole catalog raises EU database-right questions
(Directive 96/9/EC) that querying per question does not, so keep to targeted lookups.
