# UNIZG institutions in ISVU

37 constituents have ISVU ids. Course counts are for ak. god. 2025/2026, measured 2026-07-29 from
`/podaci/{id}/predmeti`. Total **27,408 courses**.

Get this live with `python3 scripts/isvu.py institutions --unizg`.

| Institution | id | courses | city |
|---|---:|---:|---|
| Filozofski fakultet | 130 | 2,821 | Zagreb |
| Prirodoslovno-matematički fakultet, prirodoslovni odsjeci | 119 | 2,403 | Zagreb |
| Pravni fakultet | 66 | 1,525 | Zagreb |
| Fakultet strojarstva i brodogradnje | 120 | 1,513 | Zagreb |
| Učiteljski fakultet | 131 | 1,440 | Zagreb |
| Kineziološki fakultet | 34 | 1,212 | Zagreb |
| Agronomski fakultet | 178 | 1,113 | Zagreb |
| Fakultet elektrotehnike i računarstva | 36 | 1,042 | Zagreb |
| Ekonomski fakultet | 67 | 857 | Zagreb |
| Akademija dramske umjetnosti | 1053 | 781 | Zagreb |
| Fakultet šumarstva i drvne tehnologije | 68 | 775 | Zagreb |
| Muzička akademija | 1349 | 775 | Zagreb |
| Rudarsko-geološko-naftni fakultet | 195 | 766 | Zagreb |
| Fakultet prometnih znanosti | 135 | 755 | Zagreb |
| Prehrambeno-biotehnološki fakultet | 58 | 750 | Zagreb |
| Katolički bogoslovni fakultet | 203 | 703 | Zagreb |
| Prirodoslovno-matematički fakultet, matematički odsjek | 37 | 645 | Zagreb |
| Fakultet hrvatskih studija | 2223 | 642 | Zagreb |
| Edukacijsko-rehabilitacijski fakultet | 13 | 630 | Zagreb |
| Farmaceutsko-biokemijski fakultet | 6 | 621 | Zagreb |
| Akademija likovnih umjetnosti | 381 | 520 | Zagreb |
| Fakultet organizacije i informatike | 16 | 513 | **Varaždin** |
| Tekstilno-tehnološki fakultet | 117 | 503 | Zagreb |
| Fakultet kemijskog inženjerstva i tehnologije | 125 | 483 | Zagreb |
| Sveučilište u Zagrebu (centralno) | 9996 | 472 | Zagreb |
| Stomatološki fakultet | 65 | 458 | Zagreb |
| Građevinski fakultet | 82 | 364 | Zagreb |
| Fakultet političkih znanosti | 15 | 356 | Zagreb |
| Medicinski fakultet | 108 | 326 | Zagreb |
| Veterinarski fakultet | 53 | 303 | Zagreb |
| Arhitektonski fakultet | 54 | 301 | Zagreb |
| Metalurški fakultet | 124 | 219 | **Sisak** |
| Geodetski fakultet | 7 | 214 | Zagreb |
| Grafički fakultet | 128 | 212 | Zagreb |
| Geotehnički fakultet | 160 | 180 | **Varaždin** |
| Sveučilišni centar za protestantsku teologiju Matija Vlačić Ilirik | 251 | 109 | Zagreb |
| Fakultet filozofije i religijskih znanosti | 2225 | 106 | Zagreb |
| Vojni studiji | 9950 | 0 | Zagreb |

Notes:
- **PMF is two institutions**, 37 (matematički odsjek) and 119 (prirodoslovni odsjeci). Search both
  when a user says "PMF", and label which one results came from.
- **9996 is not an umbrella** over the others. It is the central/rectorate entity and its 472 courses
  are real, separate, mostly cross-faculty and interdisciplinary programmes.
- **9950 Vojni studiji returns zero courses.** Skip it.
- Three constituents are outside Zagreb, marked above.
- In ISVU but **not** UNIZG, despite being in Zagreb: Hrvatsko katoličko sveučilište (331), Tehničko
  veleučilište (246), Zdravstveno veleučilište (1003), Zagrebačka škola ekonomije i managementa (255),
  MUP-Veleučilište kriminalistike (200), Poslovno veleučilište (301), Veleučilište studija sigurnosti
  (257), Veleučilište suvremenih informacijskih tehnologija (297), Sveučilište obrane i sigurnosti (373).
  Filter on `nadredjena == "Sveučilište u Zagrebu"`.

## Data coverage per faculty

Two samples: 10 courses per institution for the description fields, 12 per institution for
prerequisites. Small n, so treat 0/10 and 10/10 as real signals and single-point differences as noise.

`opis` / `ishodi` / `nositelj` out of 10, `preduvjeti upis` (`Pu`) / `polaganje` (`Pp`) out of 12.

| Institution | id | opis | ishodi | nositelj | Pu | Pp |
|---|---:|---:|---:|---:|---:|---:|
| Arhitektonski | 54 | 7 | 6 | 7 | **8** | 4 |
| PMF-matematički | 37 | **10** | **10** | 10 | 6 | 1 |
| FSB | 120 | **10** | **10** | 10 | 1 | 0 |
| Geodetski | 7 | 9 | 9 | 7 | 1 | 0 |
| Grafički | 128 | 9 | 8 | 8 | 0 | 0 |
| FKIT | 125 | 8 | 8 | 9 | 2 | 0 |
| ADU | 1053 | 8 | 7 | 10 | 3 | 0 |
| FPZ (promet) | 135 | 8 | 6 | 9 | 0 | 0 |
| Pravni | 66 | 8 | 0 | 9 | 1 | 0 |
| ERF | 13 | 7 | 8 | 10 | 0 | 0 |
| PMF-prirodoslovni | 119 | 7 | 3 | 7 | 2 | 1 |
| FER | 36 | 7 | 0 | 10 | 0 | 0 |
| FFRZ | 2225 | 6 | 5 | 9 | 0 | 0 |
| EFZG | 67 | 6 | 0 | 10 | 0 | 2 |
| Muzička akademija | 1349 | 6 | 5 | 0 | 0 | 0 |
| RGN | 195 | 6 | 6 | 7 | 3 | 1 |
| Šumarstvo | 68 | 6 | 0 | 8 | 0 | 0 |
| Veterinarski | 53 | 6 | 7 | 10 | 1 | 4 |
| KBF | 203 | 5 | 5 | 7 | 0 | 0 |
| FHS | 2223 | 4 | 2 | 9 | 0 | 0 |
| FPZG | 15 | 4 | 1 | 9 | 0 | 0 |
| PBF | 58 | 4 | 0 | 10 | 2 | 0 |
| Stomatološki | 65 | 4 | 0 | 10 | 0 | 1 |
| UNIZG centralno | 9996 | 4 | 1 | 6 | 1 | 0 |
| FFZG | 130 | 3 | 1 | 9 | 1 | 0 |
| TTF | 117 | 3 | 8 | 9 | 1 | 0 |
| Učiteljski | 131 | 3 | 3 | 1 | 0 | 0 |
| Geotehnički | 160 | 1 | 2 | 10 | 4 | 2 |
| Građevinski | 82 | 1 | 0 | 10 | 0 | 0 |
| Agronomski | 178 | 0 | 0 | 9 | 1 | 0 |
| ALU | 381 | 0 | 4 | 5 | 0 | 0 |
| FBF | 6 | 0 | 0 | 10 | 4 | 1 |
| FOI | 16 | 0 | 0 | 10 | 4 | 1 |
| Kineziološki | 34 | 0 | 0 | 10 | 1 | 0 |
| MEF | 108 | 0 | 0 | **0** | 0 | 0 |
| Metalurški | 124 | 0 | 0 | 10 | 0 | 0 |
| Protestantski | 251 | 0 | 0 | 8 | 0 | 2 |

Things to remember when answering:
- **MEF publishes no nositelj at all**, and Muzička akademija and Učiteljski nearly none.
- **Arhitektonski has by far the best prerequisite data** in ISVU (8/12), enough to build a real DAG.
  Verified: its prijediplomski Arhitektura i urbanizam programme exports 69 courses with 58 carrying
  prerequisites, at exactly 30 ECTS per semester.
- FER has good descriptions but zero ishodi and zero prerequisites in ISVU. FER publishes both,
  plus competencies and publications, on its own site at `fer.unizg.hr/{ime}.{prezime}` and
  `/predmet/{slug}`, which is outside this skill's scope for the people parts.
- PMF and PBF publish prerequisites more completely on their own sites (`/predmet/{slug}`) than in ISVU.
- FBF showed semester data on only 3 of 10 sampled courses, an outlier worth double-checking before
  trusting FBF programme placement.
