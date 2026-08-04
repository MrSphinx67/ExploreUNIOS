# UNIZG course catalog: feasibility findings & implementation plan

**Status:** research complete, nothing implemented. Written 2026-07-28.
**Goal:** a searchable/filterable catalog of *every* course at every University of Zagreb
constituent, with faculty, study programme, semester, ECTS, obavezni/izborni status, the main
professor (nositelj), and a description / ishodi učenja, so you can find courses you're
interested in.

This is a **different app** from the scheduler in this repo. The scheduler (`js/`, `kolegiji_dag/`)
is a single-programme prerequisite DAG. This is a university-wide catalog. See
[Relationship to the existing app](#relationship-to-the-existing-app).

---

## TL;DR

Feasible, and it needs **one scraper, not 33**. Everything comes from a single central source (ISVU),
which is server-rendered, unauthenticated, robots-allowed, and even has a few JSON endpoints. The only
question is coverage: learning outcomes and prerequisites are present but thin, and faculty sites fill
some of that in.

- **27,408 courses** across 37 UNIZG constituents for ak. god. 2025/2026 (measured, see table).
- Faculty + programme + **semester** + obavezni/izborni: **98%** coverage.
- Nositelj (main prof): **82%**.
- Description: **46%**. Ishodi učenja: **34%**: and unstructured. This is the weak spot in ISVU.
- **Preduvjeti do exist in ISVU**, as two optional fields, at **~10%** (upis) and **~4%**
  (polaganje), thin, but spread over 22 of 37 faculties and enough to build a real prerequisite
  graph. **PMF and PBF** publish richer, link-based versions on their own sites (verified). A second
  scraper tier also recovers **ishodi for FER, Stomatološki, PBF and ERF**, all of which ISVU has at
  ~0%. Verified per-faculty results in
  [gap 2](#2-preduvjeti-prerequisites-are-thin-in-isvu--and-richer-on-faculty-sites).
- Delivery can be a **skill** (live API calls, no hosting, no MCP) and/or a **static dataset**
  (needed for corpus-wide search). They solve different jobs, see
  [Skill vs. dataset](#skill-vs-dataset).

---

## Source of truth: the ISVU public data module

<https://www.isvu.hr/visokaucilista/hr/pocetna>

The Informacijski sustav visokih učilišta, run by SRCE for MZOM. Used by 110+ Croatian HEIs. The
`/visokaucilista/` path is a public read-only browser over the same database the student offices use.

Why it's the right source:

| Property | Finding |
|---|---|
| Rendering | Server-rendered HTML (jQuery + Bootstrap + select2 + DataTables). **No SPA, no headless browser needed.** |
| Auth | None. |
| `robots.txt` | `User-Agent: * / Allow: / / Disallow: /javno/`: `/visokaucilista/` is **allowed**. |
| Maintained | Footer reports version `2026.03.2`. |
| History | Academic years selectable back to **1976/77**; **2026/2027** already present. |
| Pagination | None server-side, full course lists ship in one response (FFZG = 2,821 rows, 214 KB). |
| Languages | `/hr/` and `/en/` variants of every path. |

### Verified endpoint catalog

Base: `https://www.isvu.hr/visokaucilista/hr`

| # | Path | Returns | Format |
|---|---|---|---|
| 1 | `/pretrazivanje` | All 125 institutions with numeric IDs, parent institution, city | HTML table |
| 2 | `/vrsta`, `/mjesto` | Institution lists by type / location | HTML |
| 3 | `/podaci/{inst}` | Institution landing page + links to the sections below | HTML |
| 4 | `/podaci/{inst}/predmeti` | **Full course list** (current ak. god.), code + name, each linked | HTML table |
| 5 | `/podaci/{inst}/predmeti/akademskagodina/{yyyy}` | Same, for a chosen year | HTML table |
| 6 | `/podaci/{inst}/akademskagodina/{yyyy}/predmeti/predmet/{code}` | **Course detail** | HTML |
| 7 | `/podaci/{inst}/dohvatirazine/{yyyy}` | Study levels offered | **JSON** |
| 8 | `/podaci/{inst}/razina/{r}/dohvatiizvedbe/{yyyy}` | Delivery modes for a level | **JSON** |
| 9 | `/podaci/{inst}/razina/{r}/izvedba/{i}/akgodina/{yyyy}` | **Nested programme/module tree** | **JSON** |
| 10 | `/podaci/{inst}/nastavniprogram/{yyyy}/razina/{r}/izvedba/{i}/smjer/{s}` | **Curriculum**, grouped by semester | HTML |
| 11 | `/podaci/{inst}/nastavnici` | Teachers & associates | HTML |
| 12 | `/podaci/{inst}/organizacijskastruktura` | Departments | HTML |
| 13 | `/podaci/{inst}/akademskikalendar` | Academic calendar | HTML |

The three JSON endpoints (#7–#9) were found by reading the inline `$.getJSON` calls on
`/podaci/{inst}/nastavniprogram`; they are what the dropdowns on that page call. They are not
documented anywhere, so treat them as unstable, but they are plain GET, no tokens.

#### #7 `dohvatirazine`: example (FER, 2025)

```json
[{"sifraRazine":3,"nazivRazineIVrste":"sveučilišni prijediplomski"},
 {"sifraRazine":4,"nazivRazineIVrste":"sveučilišni diplomski"},
 {"sifraRazine":10,"nazivRazineIVrste":"doktorski"},
 {"sifraRazine":11,"nazivRazineIVrste":"sveučilišni specijalistički"}]
```

Levels are **per institution and per year**: do not hardcode them. Known codes so far:
`3` prijediplomski, `4` diplomski, `10` doktorski, `11` specijalistički.

#### #8 `dohvatiizvedbe`: example

```json
[{"oznaka":"R","naziv":"redovni"}]
```

Returns `[]` for a level the institution doesn't offer, use this to prune the crawl.

#### #9 programme tree: example (FER, razina 3, izvedba R, 2025)

```json
[{"sifraSmjera":71, "nazivSmjera":"Elektrotehnika i informacijska tehnologija i Računarstvo",
  "sifraNadredjenogSmjera":null, "redniBrojRazine":0, "nazivTipaSmjera":"Studij",
  "trajeElUstNast":6, "brElUpisPod":null, "imaNastavniProgram":1,
  "listaPodredjenihStudija":[ { "...": "Studij / Modul children, recursive" } ]}]
```

Recursive via `listaPodredjenihStudija`. `nazivTipaSmjera` is `Studij` or `Modul`.
`trajeElUstNast` = duration in semesters. **Only fetch #10 when `imaNastavniProgram == 1`**: parent nodes are often `0` and have no curriculum of their own.

#### #10 curriculum page: structure

Grouped by `Semestar 1 … N`. Per semester: one table of mandatory courses, then zero or more
`Izborna grupa: <name>` blocks each with `Opis: broj ECTS bodova koje je potrebno odabrati:
najmanje N` and its own table. Columns: `Šifra | Naziv | Polaže se | ECTS | P | A | L | S | TJ`
(the hour columns vary per institution: FHS had `P S PK LK SJ TJ`, FER had `P A L S TJ`;
**parse the header row, don't assume fixed columns**). Legend at the bottom expands the letters.

#### #6 course detail: fields

Observed labels (all optional except šifra/ECTS/opterećenje):

`Šifra` · `Kratica` · `Visoko učilište` · `ECTS bodovi` · `Opterećenje` (P/A/L/S/… hours) ·
`Nositelji` · `Izvođači` (each with role markers `(P)`, `(L)`, `(S)`, `(V)`) ·
`Opis predmeta` (free text) · `Jezici izvođenja nastave` ·
`Obavezna literatura` · `Preporučena literatura` · `Predmet u nastavnom programu`

**The `Predmet u nastavnom programu` table is the single most useful thing on the site.** Columns:

```
Šifra studija | Naziv studija | Razina studija | Semestar izvođenja | obavezni/izborni
```

e.g. for FER 183357 *Uvod u programiranje*:
`71 | Elektrotehnika i informacijska tehnologija i Računarstvo | prijediplomski | 1 | obavezni`

It's a **reverse index**: every programme the course belongs to, with its semester and mandatory
status. This means the whole catalog can be built from endpoint #4 + #6 alone, no need to walk
#7→#8→#9→#10 at all. Walking the programme tree is only needed if you also want the *izborna grupa*
groupings and their ECTS minimums (which the scheduler would eventually want).

---

## Institutions and scale

37 UNIZG constituents have ISVU IDs. Course counts are for ak. god. 2025/2026, measured
2026-07-28 via endpoint #4 (distinct `predmet/{code}` links per institution page):

| Institution | ID | Courses |
|---|---:|---:|
| Filozofski fakultet | 130 | 2,821 |
| PMF – prirodoslovni odsjeci | 119 | 2,403 |
| Pravni fakultet | 66 | 1,525 |
| Fakultet strojarstva i brodogradnje | 120 | 1,513 |
| Učiteljski fakultet | 131 | 1,440 |
| Kineziološki fakultet | 34 | 1,212 |
| Agronomski fakultet | 178 | 1,113 |
| Fakultet elektrotehnike i računarstva | 36 | 1,042 |
| Ekonomski fakultet | 67 | 857 |
| Akademija dramske umjetnosti | 1053 | 781 |
| Fakultet šumarstva i drvne tehnologije | 68 | 775 |
| Muzička akademija | 1349 | 775 |
| Rudarsko-geološko-naftni fakultet | 195 | 766 |
| Fakultet prometnih znanosti | 135 | 755 |
| Prehrambeno-biotehnološki fakultet | 58 | 750 |
| Katolički bogoslovni fakultet | 203 | 703 |
| PMF – matematički odsjek | 37 | 645 |
| Fakultet hrvatskih studija | 2223 | 642 |
| Edukacijsko-rehabilitacijski fakultet | 13 | 630 |
| Farmaceutsko-biokemijski fakultet | 6 | 621 |
| Akademija likovnih umjetnosti | 381 | 520 |
| Fakultet organizacije i informatike | 16 | 513 |
| Tekstilno-tehnološki fakultet | 117 | 503 |
| Fakultet kemijskog inženjerstva i tehnologije | 125 | 483 |
| Sveučilište u Zagrebu (centralno) | 9996 | 472 |
| Stomatološki fakultet | 65 | 458 |
| Građevinski fakultet | 82 | 364 |
| Fakultet političkih znanosti | 15 | 356 |
| Medicinski fakultet | 108 | 326 |
| Veterinarski fakultet | 53 | 303 |
| Arhitektonski fakultet | 54 | 301 |
| Metalurški fakultet | 124 | 219 |
| Geodetski fakultet | 7 | 214 |
| Grafički fakultet | 128 | 212 |
| Geotehnički fakultet | 160 | 180 |
| Sveučilišni centar za protestantsku teologiju | 251 | 109 |
| Fakultet filozofije i religijskih znanosti | 2225 | 106 |
| Vojni studiji | 9950 | 0 |
| **TOTAL** | | **27,408** |

Notes:
- PMF is **two** ISVU institutions (37 matematički, 119 prirodoslovni): must be merged or clearly
  labelled in the UI.
- Vojni studiji (9950) returns 0 courses; skip it.
- 9996 "Sveučilište u Zagrebu" is the central/rectorate entity, not an umbrella over the others: its 472 courses are real and separate (cross-faculty/interdisciplinary programmes).
- FOI (16) and Geotehnički (160) are in **Varaždin**, Metalurški (124) in **Sisak**: worth a
  location field.
- Not UNIZG but present in ISVU and in Zagreb (exclude): Hrvatsko katoličko sveučilište (331),
  Tehničko veleučilište (246), Zdravstveno veleučilište (1003), ZŠEM (255), and others.

---

## Field coverage: measured, not assumed

Method: 10 pseudo-random courses per institution (`random.seed(42)`), 370 course detail pages
fetched 2026-07-28. Script in [Appendix A](#appendix-a-coverage-measurement-script).

| Field | Coverage |
|---|---:|
| semester + programme + obavezni/izborni | **98%** (361/370) |
| nositelj | **82%** (302/370) |
| opis predmeta (>60 chars) | **46%** (170/370) |
| ishodi učenja (any `ishod` match) | **34%** (125/370) |

Per institution (out of 10 each):

| Institution | ID | opis | ishodi | nositelj | semestar |
|---|---:|---:|---:|---:|---:|
| Agronomski | 178 | 0 | 0 | 9 | 10 |
| ADU | 1053 | 8 | 7 | 10 | 10 |
| ALU | 381 | 0 | 4 | 5 | 10 |
| Arhitektonski | 54 | 7 | 6 | 7 | 10 |
| ERF | 13 | 7 | 8 | 10 | 10 |
| EFZG | 67 | 6 | 0 | 10 | 10 |
| FER | 36 | 7 | 0 | 10 | 10 |
| FFRZ | 2225 | 6 | 5 | 9 | 10 |
| FHS | 2223 | 4 | 2 | 9 | 10 |
| FKIT | 125 | 8 | 8 | 9 | 10 |
| FOI | 16 | 0 | 0 | 10 | 10 |
| FPZG | 15 | 4 | 1 | 9 | 10 |
| FPZ (promet) | 135 | 8 | 6 | 9 | 10 |
| FSB | 120 | **10** | **10** | 10 | 9 |
| Šumarstvo | 68 | 6 | 0 | 8 | 10 |
| FBF | 6 | 0 | 0 | 10 | **3** |
| FFZG | 130 | 3 | 1 | 9 | 9 |
| Geodetski | 7 | 9 | 9 | 7 | 10 |
| Geotehnički | 160 | 1 | 2 | 10 | 10 |
| Građevinski | 82 | 1 | 0 | 10 | 10 |
| Grafički | 128 | 9 | 8 | 8 | 10 |
| KBF | 203 | 5 | 5 | 7 | 10 |
| Kineziološki | 34 | 0 | 0 | 10 | 10 |
| MEF | 108 | 0 | 0 | **0** | 10 |
| Metalurški | 124 | 0 | 0 | 10 | 10 |
| Muzička akademija | 1349 | 6 | 5 | **0** | 10 |
| Pravni | 66 | 8 | 0 | 9 | 10 |
| PBF | 58 | 4 | 0 | 10 | 10 |
| PMF-mat | 37 | **10** | **10** | 10 | 10 |
| PMF-prir | 119 | 7 | 3 | 7 | 10 |
| RGN | 195 | 6 | 6 | 7 | 10 |
| Stomatološki | 65 | 4 | 0 | 10 | 10 |
| Protestantski | 251 | 0 | 0 | 8 | 10 |
| TTF | 117 | 3 | 8 | 9 | 10 |
| Učiteljski | 131 | 3 | 3 | **1** | 10 |
| Veterinarski | 53 | 6 | 7 | 10 | 10 |
| UNIZG centralno | 9996 | 4 | 1 | 6 | 10 |

Measurement caveats:
- `opis` required >60 chars between the `Opis predmeta` and `literatura` labels; `ishodi` was a
  plain case-insensitive `ishod` regex over the whole page. TTF shows ishodi 8 / opis 3, so ishodi
  sometimes appear outside the block the opis heuristic measured: the real opis number may be
  slightly understated for some institutions.
- n=10 per institution → ±~15pp per-institution error. The 0/10 and 10/10 rows are trustworthy
  signals; a 6 vs 7 difference is noise.
- FBF semestar 3/10 is a genuine outlier worth investigating before trusting FBF data.
- MEF 0/10 nositelj, Muzička 0/10, Učiteljski 1/10: these institutions don't publish course
  leaders to ISVU. Fallback: endpoint #11 `nastavnici` gives the teacher list, but not the
  course→teacher link.

---

## The two real gaps

### 1. Ishodi učenja are not a structured field

There is no `Ishodi učenja` field in the ISVU public view. Where outcomes exist, they're prose
inside `Opis predmeta`, under institution-specific headings. Real example (PMF, predmet 63146):

```
CILJEVI PREDMETA:
1. osposobiti studente za izvođenje istraživački usmjerene nastave fizike …
OČEKIVANI ISHODI UČENJA NA RAZINI PREDMETA:
1. objasniti i primijeniti ključne fizikalne …
```

FFZG instead uses `Ciljevi kolegija : … Sadržaj kolegija : … Studentske obveze : …` with no
outcomes at all.

Implication: extraction is a **text-segmentation problem**, not a parsing problem. Two tiers:
- Regex/heuristic split on known headings (`ISHODI`, `OČEKIVANI ISHODI`, `Ciljevi`, `Sadržaj`,
  `Studentske obveze`, `Literatura`): cheap, gets most of the 34%.
- LLM pass over the raw `opis` to normalize into `{ciljevi[], ishodi[], sadrzaj, obveze}`: better recall on odd formats. ~170 of 370 sampled courses have any opis at all, so university-wide
  that's roughly 12k non-empty descriptions to process. Batchable, one-time, cacheable by content hash.

For the 0%-ishodi institutions (Agronomski, FOI, MEF, Kineziološki, Metalurški, FBF, Protestantski,
and EFZG/Pravni/PBF/Stomatološki/Šumarstvo/Građevinski which have opis but no outcomes), ISVU simply
does not have the data. Only per-faculty scrapers can fill it, and those are bespoke, I checked FER's
own site and an anonymous fetch of a course page returns nav chrome without the syllabus body.
**Recommend: don't do this in v1.** Ship with honest "nema podataka" and see if it actually bothers you.

### 2. Preduvjeti (prerequisites) are thin **in ISVU**: and richer on faculty sites

> **Corrected 2026-07-30.** This section previously said prerequisites do not exist in ISVU at all.
> That was wrong, twice over. They are two real fields on the course detail page,
> `Preduvjeti za upis predmeta` and `Preduvjeti za polaganje predmeta`, formatted as
> `Course name (položen)` / `Course name (odslušan)`. I missed them because the detail page renders
> its `<dl>` with **only the populated fields**, and I was checking against a fixed list of labels
> instead of reading whichever labels were present. Coverage is ~10% (upis) and ~4% (polaganje), but
> it spans 22 of 37 faculties, and the shipped exporter builds its whole graph from these fields.
> Arhitektonski is the richest source in ISVU; FER publishes none anywhere.
>
> One caveat that follows from the format: the target is a **free-text course name**, not an id, so
> it routinely names courses outside the programme being exported, renamed or retired ones. Those
> edges have to be pruned and reported, which is why the exporter has `prune_dangling()`.

**The faculty sites publish a better version.** PMF's own course pages
(`https://www.pmf.unizg.hr/{odsjek}/predmet/{slug}`) contain exactly the field `js/data.js` cites:

```html
<tr><td colspan="2"><b>Preduvjeti za:</b></td></tr>
<tr><td width="2%" colspan="2"><blockquote>
  <strong>Upis predmeta :</strong><br/>
  Odslušan : <a target="_parent" href="/geof/predmet/dinmet3_a">Dinamička meteorologija 3</a><br/>
```

That is a machine-readable edge: condition kind (`Upis predmeta`), condition type
(`Odslušan` / `Položen`), and the target course as a **link carrying its slug**: a stable ID, not a
name string. It maps 1:1 onto the scheduler's `preduvjeti: [{ kolegij, uvjet }]`.

The same pages also carry a much richer `Opis predmeta` than ISVU, with explicit
`ISHODI UČENJA:` sections plus `CILJ KOLEGIJA`, `PLAN I PROGRAM`, `NAČIN UČENJA`,
`METODE POUČAVANJA`, `ISPITNI ROKOVI`, `UVJETI ZA DOBIVANJE POTPISA`,
`NAČIN PROVJERE ZNANJA`, `POPIS OBAVEZNE LITERATURE`.

So **both gaps close on the same source**: for the faculties that run this CMS.

#### How far does it scale? **Verified 2026-07-28.**

Method: crawled each candidate faculty site from its `/studiji` (or a known course page), collected
all `/predmet/` URLs found, then fetched a random 15 of them and counted how many contain
`Preduvjeti za:` and `Ishodi učenja`. Sampling 15 matters: a course page only renders
`Preduvjeti za:` if that course *actually has* prerequisites, so a single sample proves nothing.

| Faculty | course pages found | sampled | **preduvjeti** | **ishodi** | ISVU ishodi (for contrast) |
|---|---:|---:|---:|---:|---:|
| **PBF** | 64 | 15 | **8/15** | **15/15** | 0/10 |
| **PMF** | 91 | 15 | **5/15** | 5/15 | 3/10 (prir) · 10/10 (mat) |
| FER | 146 | 15 | 0/15 | **13/15** | 0/10 |
| ERF | 69 | 15 | 0/15 | **15/15** | 8/10 |
| Stomatološki | 112 | 15 | 0/15 | **15/15** | 0/10 |
| Kineziološki | 271 | 15 | 0/15 | 1/15 | 0/10 |
| FPZG | 145 | 15 | 0/15 | 0/15 | 1/10 |

No `/predmet/{slug}` route at all, course info exists but in bespoke page structures, each needing
its own scraper:

| Faculty | Actual structure |
|---|---|
| FKIT | `/zavod/{dept}/predmeti`: per-department course lists |
| Građevinski | programme pages only (`/studiji/sveucilisni_prijediplomski_studij_gradevinarstvo/`) |
| RGN | different CMS entirely (`/hr/…`): `/studiji/*/predmeti`, `/doktorski-studij/opisi-predmeta` |
| FHS | none, only a lifelong-learning course catalog |

Inconclusive: **ADU, MUZA**: both unreachable from this network (TLS `UNEXPECTED_EOF` / timeouts).
Not evidence of absence.

**Conclusions:**

1. **Preduvjeti on faculty sites: only PMF and PBF.** Not a third of UNIZG, two faculties. 0/15 at
   each of FER/ERF/Stomatološki/Kineziološki/FPZG is strong evidence those sites don't render the
   field at all (across 15 courses, some would have prerequisites). This is about the *faculty-site*
   tier only; ISVU itself carries prerequisites for 22 of 37 faculties, thinly, see the correction
   in gap 2.
2. **Ishodi: the bigger win, and it lands exactly where ISVU is empty.** FER, Stomatološki and PBF
   are all **0/10 in ISVU** but **13/15, 15/15, 15/15** on their own sites. That's ~2,250 courses
   (FER 1,042 + PBF 750 + Stomatološki 458) whose learning outcomes are only obtainable this way.
3. **Earlier claim that FER is login-gated was wrong** (twice). FER's `/predmet/{slug}` pages are
   fully public and unusually rich: numbered `Ishodi učenja`, ECTS, per-type teaching hours, grading
   thresholds, even a `Sličan kolegij` cross-reference to courses at EPFL / TU München. The bad call
   came from one wrong slug that resolved to an unrelated page.
4. **Two template variants, one extraction rule.** PMF uses a legacy `<table>`/`<blockquote>` layout,
   PBF a Bootstrap-5 `<h5>`/`<div class="ms-3">` one, but the inner markup is identical:

   ```html
   <strong>Upis predmeta :</strong><br/>
   Položen : <a target="_parent" href="/predmet/anakem_c">Analitička kemija</a><br/>
   Položen : <a target="_parent" href="/predmet/bio_c">Biologija</a><br/>
   ```

   One regex covers both: `(Položen|Odslušan)\s*:\s*<a[^>]*href="[^"]*/predmet/([^"]+)"[^>]*>([^<]+)</a>`.
   Both condition types occur in the wild, matching the scheduler's `polozen`/`odslusan` enum exactly.
5. **Course discovery has no cheap shortcut.** No faculty site has a usable `sitemap.xml` or
   `robots.txt` (mostly 404; FHS serves its homepage for any path). Course URLs must be found by
   crawling programme pages. Costs ~5–30 page fetches per faculty before any course fetch.

Revised bottom line: the faculty tier **automates the scheduler's DAG edges for PMF and PBF only**.
Its real value is **ishodi učenja for FER, Stomatološki, PBF and ERF**, which ISVU does not have.

### Dead end to avoid: MOZVAG

MOZVAG / Preglednik studijskih programa (AZVO) was the obvious source for structured learning
outcomes, HEIs recorded them there for accreditation. **It was shut down on 1 February 2025**
(<https://www.azvo.hr/2025/02/11/obavijest-korisnicima/>). `mozvag.srce.hr` now 301s to a dead
`srce.unizg.hr/mozvagpreglednik/` (404). Its replacement, ISPiK, has no public browser yet.
Don't spend time here.

---

## Skill vs. dataset

Two delivery shapes. **No MCP server in either**: the ISVU endpoints are unauthenticated plain GET,
so MCP's value-adds (auth, session state, connection pooling, wrapping a proprietary SDK) don't
apply. A hosted MCP would be pure overhead.

| Job | Skill (live calls) | Static dataset (crawl) |
|---|---|---|
| "Prereqs for Biokemija 1 at PMF?" | ✅ ideal | ✅ |
| "Show FER's prijediplomski curriculum" | ✅ ideal | ✅ |
| "Who teaches X?" | ✅ ideal | ✅ |
| "All izborni, 4–6 ECTS, zimski, anywhere in UNIZG, mentioning 'strojno učenje'" | ❌ needs whole corpus | ✅ |
| Interactive browse/filter UI | ❌ | ✅ |
| Freshness | always current | snapshot + refresh |
| Build cost | ~1 hour (endpoints already mapped) | crawl + pipeline + UI |
| Infra | none | none (static JSON) |

**A skill is mostly already written**: this document *is* its content. It would be a `SKILL.md`
with the endpoint catalog, the razina/izvedba codes, the institution ID table, the parsing gotchas
(header-row-driven tables, `imaNastavniProgram == 1` guard), and a small Python helper.

**Recommended sequencing: skill first.** It's cheap, it validates every endpoint end-to-end against
the live service, it's immediately useful for targeted lookups, and it becomes the reference
implementation the batch crawler reuses. Then build the dataset only if corpus-wide search is what
you actually want, which the original ask ("a list of all, so I can find ones I'm interested in")
suggests it is.

One risk to design around: endpoints #7–#9 are undocumented internals. A skill that hardcodes them
should include a cheap self-check (fetch a known institution, assert the JSON shape) so breakage is
loud rather than silent.

## Proposed implementation

### Architecture

```
scraper/                     Python, stdlib + BeautifulSoup (or lxml)
  isvu/
    client.py                HTTP: session, retry/backoff, on-disk cache, rate limit
    institutions.py          #1 → institution list
    courses.py               #4/#5 → course list; #6 → course detail
    programmes.py            #7→#8→#9→#10 → programme tree + curriculum
    parse.py                 header-row-driven table parsing (no fixed columns)
    segment.py               opis → {ciljevi, ishodi, sadrzaj, obveze} heuristics
  build.py                   → catalog.sqlite  +  catalog.json / per-faculty shards
  cache/                     raw HTML, keyed (inst, year, kind, id), never re-fetch
web/                         static browse/filter UI (same no-build ethos as this repo)
```

Deliberately **not** a framework. Same constraint as the existing app: static output, no server.

### Two-phase crawl

**Phase A: spine (cheap, do first).** Endpoint #1 → 37 institutions. Endpoint #4 per institution
→ 27.4k course codes (37 requests). Endpoint #6 per course → everything including the
programme/semester/status reverse index (27.4k requests).

That's **~27.4k requests total** and yields the full catalog at the coverage measured above.
At a polite 3 req/s with 4 workers: **~2.5 hours**. Cache raw HTML so re-runs are incremental
and parser changes need zero refetching.

**Phase B, programme structure (optional).** #7→#8→#9→#10 per institution/level/mode/smjer, to get
*izborna grupa* groupings and their ECTS minimums. Order of a few thousand requests. Only needed if
you want the catalog to feed the scheduler with proper elective-group rules.

### Politeness

- Descriptive `User-Agent` with a contact address.
- ≤3 req/s, single connection pool, exponential backoff on 5xx, hard stop on 429.
- Full on-disk cache; a re-run with a warm cache makes zero network calls.
- Crawl in off-peak hours. This is a public read-only service run by SRCE: the whole job is
  ~27k GETs, comparable to one person browsing for an afternoon, but don't parallelize hard.

### Proposed schema

```jsonc
// course
{
  "id": "36:183357",              // "{institutionId}:{isvuCode}", stable, unlike naziv
  "sifra": "183357",
  "naziv": "Uvod u programiranje",
  "kratica": "UUP",
  "institution": { "id": 36, "naziv": "Fakultet elektrotehnike i računarstva",
                   "kratica": "FER", "grad": "Zagreb" },
  "ects": 7.0,
  "opterecenje": { "P": 60, "A": 0, "L": 18, "S": 0 },
  "nositelji": ["prof. dr. sc. Gordan Gledec", "prof. dr. sc. Igor Mekterović"],
  "izvodaci": [{ "ime": "prof. dr. sc. Ljiljana Brkić", "role": ["P"] }],
  "jezici": ["hrvatski"],
  "opis_raw": "…",               // verbatim, always keep
  "opis": {                       // segmented; nulls where absent
    "ciljevi": null, "ishodi": [], "sadrzaj": null, "obveze": null
  },
  "literatura": { "obavezna": [], "preporucena": [] },
  "programmes": [                 // from "Predmet u nastavnom programu"
    { "sifraStudija": 71, "naziv": "Elektrotehnika i informacijska tehnologija i Računarstvo",
      "razina": "prijediplomski", "semestar": 1, "status": "obavezni" }
  ],
  "akademskaGodina": 2025,
  "source": "https://www.isvu.hr/visokaucilista/hr/podaci/36/akademskagodina/2025/predmeti/predmet/183357",
  "scrapedAt": "2026-07-28"
}
```

Key decisions baked in:
- **`(institutionId, isvuCode)` as the identity**, never `naziv`. The existing scheduler joins by
  name string; that will not survive 27k courses (many duplicate names across faculties).
- `programmes` is a **list**: one course legitimately sits in several programmes at different
  semesters with different mandatory status. A single `semestar` field would be wrong.
- Keep `opis_raw` forever. Segmentation heuristics will change; the source text shouldn't be refetched.
- Every record carries `source` URL + `scrapedAt` so the UI can link out and show staleness.

### Search UI: what actually needs to be filterable

Given the point is "easily find which ones I'm interested in":
faculty · study level · semester (1–N, or zimski/ljetni parity) · ECTS range · obavezni/izborni ·
has-description · professor name · **full-text over naziv + opis**.

27k records ≈ a few MB of JSON gzipped, fine to ship entirely client-side with a prebuilt
inverted index, no server. Shard per faculty and lazy-load if it gets heavy. Croatian
diacritic-insensitive matching is a must (`č/c`, `ć/c`, `š/s`, `ž/z`, `đ/dj`).

---

## Relationship to the existing app

This repo is a **single-programme prerequisite DAG + earliest-semester scheduler**. The catalog is a
**university-wide browse/filter tool**. Different data shapes, different jobs. Proposal:

- Build the catalog as a sibling (`catalog/` here, or its own repo).
- Add a one-way bridge: *"load this programme into the scheduler"*, the curriculum data
  (endpoint #10) maps almost 1:1 onto the existing `{naziv, semestar, godina, status, ects}` schema.
- `preduvjeti` come from ISVU's own two fields wherever they are filled in (~10%, but across 22 of
  37 faculties), and from the faculty-site tier for **PMF and PBF**, which publish a richer
  slug-linked version. So the scheduler's DAG *edges* are automatable too, not just its nodes, which is what the shipped `unizg_dag_json` does. Where a faculty published nothing, edges stay
  hand-entered.
- If the bridge happens, the scheduler should migrate from name-matching to the catalog's stable
  `id`: worth doing regardless.

Note: `feature/kolegiji-raspored` is the Vercel **production** branch; keep catalog work off it
until we decide whether this deploys as part of the same site or separately.

---

## Open questions to discuss

1. **Scope of v1**: all 37 constituents, or start with 2–3 you actually care about (PMF? FER?) to
   validate the parser before a 2.5-hour crawl?
2. **Skill first, dataset later?** Or straight to the dataset?
3. **Ishodi**: accept 34% and label gaps honestly, or invest in the LLM segmentation pass, or go
   after per-faculty scrapers for the 0% institutions? (My recommendation: accept 34% in v1,
   add the LLM pass in v2, and do the Ekorre faculty-site tier only for faculties you care about.)
4. ~~**Verify the Ekorre tier**~~, **done 2026-07-28.** Preduvjeti: PMF + PBF only. Ishodi: big
   win at FER / Stomatološki / PBF / ERF. ADU + MUZA still unreachable. See gap 2 for the table.
5. **Language**: Python scraper is the obvious choice, but output must be static JSON so the UI
   stays dependency-free like the current app. Agreed?
6. **Refresh cadence**: one-time snapshot, or a scheduled re-crawl (e.g. yearly when the new
   ak. god. lands, since 2026/2027 is already published)? Affects whether this needs CI.
7. **Historical data**: years back to 1976/77 are available. Any interest, or current year only?
8. **Deployment**: same Vercel project as the scheduler, or separate?
9. **Multi-year / cross-institution dedup**: PMF's two IDs, and courses shared between UNIZG
   central (9996) and faculties. Merge, or show as-is?

---

## Appendix A: coverage measurement script

The script that produced the coverage table. Kept for reproducibility, re-run to check whether
institutions have improved their ISVU data before committing to the extraction strategy.

```python
import re, html, urllib.request, time, random
from concurrent.futures import ThreadPoolExecutor

INST = {178:"Agronomski",1053:"ADU",381:"ALU",54:"Arhitektonski",13:"ERF",67:"EFZG",
36:"FER",2225:"FFRZ",2223:"FHS",125:"FKIT",16:"FOI",15:"FPZG",135:"FPZ-promet",
120:"FSB",68:"Sumarstvo",6:"FBF",130:"FFZG",7:"Geodetski",160:"Geotehnicki",
82:"Gradjevinski",128:"Graficki",203:"KBF",34:"Kinezioloski",108:"MEF",124:"Metalurski",
1349:"MUZA",66:"Pravni",58:"PBF",37:"PMF-mat",119:"PMF-prir",195:"RGN",65:"Stomatoloski",
251:"Protestantski",117:"TTF",131:"Uciteljski",53:"Veterinarski",9996:"UNIZG-centar"}
UA = {"User-Agent": "Mozilla/5.0 (feasibility check; <contact email>)"}

def get(u):
    return urllib.request.urlopen(
        urllib.request.Request(u, headers=UA), timeout=90).read().decode("utf-8", "replace")

def txt(h):
    h = re.sub(r'(?s)<(script|style).*?</\1>', '', h)
    return html.unescape(re.sub(r'<[^>]+>', '\n', h))

N = 10
random.seed(42)

def one(item):
    iid, name = item
    h = get(f"https://www.isvu.hr/visokaucilista/hr/podaci/{iid}/predmeti")
    codes = sorted(set(re.findall(r'predmeti/predmet/(\d+)', h)))
    if not codes:
        return (name, iid, 0, 0, 0, 0, 0)
    pick = random.sample(codes, min(N, len(codes)))
    opis = ish = nos = sem = 0
    for c in pick:
        t = txt(get(f"https://www.isvu.hr/visokaucilista/hr/podaci/{iid}"
                    f"/akademskagodina/2025/predmeti/predmet/{c}"))
        if "Opis predmeta" in t and len(
                t.split("Opis predmeta")[1].split("literatura")[0].strip()) > 60:
            opis += 1
        if re.search(r'(?i)ishod', t): ish += 1
        if "Nositelji" in t: nos += 1
        if "Semestar izvo" in t: sem += 1
        time.sleep(0.15)
    return (name, iid, len(pick), opis, ish, nos, sem)

with ThreadPoolExecutor(max_workers=5) as ex:
    for row in ex.map(one, INST.items()):
        print(row)
```

## Appendix B: sources

- ISVU public module, <https://www.isvu.hr/visokaucilista/hr/pocetna>
- ISVU system overview, <https://www.isvu.hr/sustav/>
- ISVU nastavni program & upisi, <https://www.isvu.hr/sustav/nastavniprogramiupisi>
- SRCE ISVU service page, <https://www.srce.unizg.hr/en/isvu>
- AZVO notice, MOZVAG shutdown 2025-02-01, <https://www.azvo.hr/2025/02/11/obavijest-korisnicima/>
- AZVO MOZVAG (historical), <https://www.azvo.hr/en/evaluation/higher-education/mozvag-information-system/>
