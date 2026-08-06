# SUJJS (Osijek) institutions in ISVU

18 constituents have ISVU ids. Course counts are for ak. god. 2025/2026, measured 2026-08-06 from
`/podaci/{id}/predmeti`. Total **9,501 courses**.

Get this live with `python3 scripts/isvu.py institutions --unios`.

| Institution | id | courses | city |
|---|---:|---:|---|
| Akademija za umjetnost i kulturu u Osijeku | 361 | 1,555 | Osijek |
| Fakultet agrobiotehničkih znanosti Osijek | 79 | 1,210 | Osijek |
| Filozofski fakultet | 122 | 1,046 | Osijek |
| Ekonomski fakultet u Osijeku | 10 | 901 | Osijek |
| Fakultet elektrotehnike, računarstva i informacijskih tehnologija Osijek | 165 | 778 | Osijek |
| Pravni fakultet Osijek | 111 | 722 | Osijek |
| Fakultet za odgojne i obrazovne znanosti | 245 | 622 | Osijek |
| Medicinski fakultet Osijek | 236 | 493 | Osijek |
| Građevinski i arhitektonski fakultet Osijek | 149 | 466 | Osijek |
| Fakultet za dentalnu medicinu i zdravstvo Osijek | 356 | 411 | Osijek |
| Prehrambeno-tehnološki fakultet Osijek | 113 | 306 | Osijek |
| Katolički bogoslovni fakultet u Đakovu | 2032 | 216 | **Đakovo** |
| Odjel za biologiju | 285 | 188 | Osijek |
| Fakultet turizma i ruralnog razvoja u Požegi | 370 | 143 | **Požega** |
| Kineziološki fakultet Osijek | 368 | 126 | Osijek |
| Fakultet primijenjene matematike i informatike | 372 | 114 | Osijek |
| Odjel za fiziku | 1312 | 112 | Osijek |
| Odjel za kemiju | 291 | 92 | Osijek |

Notes:
- **No institution here is split across two ISVU ids.** Unlike UNIZG's PMF (matematički odsjek /
  prirodoslovni odsjeci as separate ids 37 / 119), every SUJJS constituent above is one id. There is
  also no "central/rectorate" entity analogous to UNIZG's 9996 — all 18 ids are teaching sastavnice.
- **Two constituents are outside Osijek**, marked above: Katolički bogoslovni fakultet u Đakovu and
  Fakultet turizma i ruralnog razvoja u Požegi. Both are still SUJJS constituents (`nadredjena ==
  "Sveučilište Josipa Jurja Strossmayera u Osijeku"`), just not in the city of Osijek itself.
- `fpmoi` and `mathos` are both aliases for id 372 (Fakultet primijenjene matematike i informatike),
  since both names are in real use for it.

## Data coverage per faculty

One sample: 10 pseudo-random courses per institution (`random.seed(42)`, sampled deterministically
before any concurrent fetching — 180 course detail pages total), measured 2026-08-06. Small n, so
treat 0/10 and 10/10 as real signals and single-point differences as noise.

`opis` / `ishodi` / `nositelj` / `jez` (jezici izvođenja nastave) / `jez-en` (marked English) out of
10 each. `Pu` (preduvjeti za upis) / `Pp` (preduvjeti za polaganje) also out of 10 — same 10 courses as
every other column, not a separate sample.

Every one of the 180 sampled courses had semester + programme + obavezni/izborni status populated
(180/180, via the "Predmet u nastavnom programu" table), so that column is omitted here — it carries
no per-institution signal, unlike UNIZG where it varied.

| Institution | id | opis | ishodi | nositelj | Pu | Pp | jez | jez-en |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Odjel za biologiju | 285 | 9 | 9 | 8 | 0 | 0 | 4 | 2 |
| Prehrambeno-tehnološki fakultet Osijek | 113 | 7 | 8 | 8 | 0 | 0 | 1 | 1 |
| Filozofski fakultet | 122 | 6 | 10 | 9 | 0 | 0 | 0 | 0 |
| Katolički bogoslovni fakultet u Đakovu | 2032 | 6 | 5 | 8 | 0 | 0 | 6 | 0 |
| Građevinski i arhitektonski fakultet Osijek | 149 | 5 | 9 | 9 | 0 | 0 | 0 | 0 |
| Odjel za kemiju | 291 | 5 | 5 | 9 | 0 | 1 | 5 | 5 |
| Kineziološki fakultet Osijek | 368 | 2 | 9 | 10 | 0 | 0 | 2 | 0 |
| Akademija za umjetnost i kulturu u Osijeku | 361 | 2 | 8 | 6 | 0 | 0 | 0 | 0 |
| Odjel za fiziku | 1312 | 2 | 5 | 8 | 0 | 0 | 0 | 0 |
| Fakultet za odgojne i obrazovne znanosti | 245 | 0 | 10 | 8 | 0 | 0 | 0 | 0 |
| Fakultet primijenjene matematike i informatike | 372 | 0 | 10 | 10 | 0 | 0 | 0 | 0 |
| Fakultet turizma i ruralnog razvoja u Požegi | 370 | 0 | 4 | 9 | 0 | 1 | 0 | 0 |
| Medicinski fakultet Osijek | 236 | 0 | 1 | 10 | 0 | 0 | 0 | 0 |
| Ekonomski fakultet u Osijeku | 10 | 0 | 0 | 8 | 0 | 0 | 0 | 0 |
| Fakultet agrobiotehničkih znanosti Osijek | 79 | 0 | 0 | 10 | 0 | 0 | 0 | 0 |
| Pravni fakultet Osijek | 111 | 0 | 0 | 6 | 0 | 1 | 0 | 0 |
| Fakultet elektrotehnike, računarstva i informacijskih tehnologija Osijek | 165 | 0 | 0 | 10 | 0 | 0 | 0 | 0 |
| Fakultet za dentalnu medicinu i zdravstvo Osijek | 356 | 0 | 0 | 10 | 0 | 0 | 0 | 0 |

Things to remember when answering:
- **Preduvjeti za upis (Pu) was 0/10 at every single institution** — 0/180 overall. Verified this is a
  genuine absence, not a parser miss: the literal string "Preduvjeti" does not appear anywhere on a
  sampled FERIT course page (165/213725), while the parser correctly picks up the sibling field
  `Preduvjeti za polaganje predmeta` when it *is* present (e.g. Pravni fakultet Osijek 111/111430:
  "Građansko pravo I (položen)"). Structured enrolment prerequisites are, as far as this sample shows,
  essentially unpublished across all of SUJJS in ISVU, not just at FERIT.
- **9 of 18 institutions had 0/10 opis**, more than double UNIZG's rate — descriptions are
  considerably thinner here. Odjel za biologiju (9/10) and Prehrambeno-tehnološki (7/10) are the
  exceptions worth pointing someone to if they want a well-documented course.
- **Ishodi učenja are comparatively well covered** (93/180, 51.7%, well above UNIZG's 34%) and, unlike
  opis, not concentrated in a couple of institutions — 12 of 18 have at least 4/10.
- **jez (jezici izvođenja nastave) is sparse and concentrated**: only 5 of 18 institutions have any at
  all, and Odjel za kemiju (5/10, all marked English) and KBF Đakovo (6/10, none marked English) hold
  most of what exists.
