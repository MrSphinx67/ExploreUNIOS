# Answers to the probe set — BASELINE server instructions (v1)

## P1

Da, horizontalna mobilnost unutar UNIZG-a postoji točno za to: slušati i polagati pojedine predmete na drugoj sastavnici uz svoj matični studij.

Katalog mogu pokriti odmah. PMF su u ISVU-u dvije ustanove, 37 (matematički odsjek) i 119 (prirodoslovni odsjeci); molekularna biologija je na 119.

Tool: `unizg_courses(query="molekularna biologija", faculty_id=119)`, pa `unizg_course(faculty_id=119, code=...)` za ECTS, semestar i sadržaj.

Ono što ISVU ne sadrži su pravila: smiješ li se upisati, kvote, rokove, treba li odobrenje FER-a i kako se ECTS priznaju. To potvrdi u obje referade, FER-ovoj i PMF-ovoj — FER-ova strana odlučuje o priznavanju. I napomena: FER ne objavljuje preduvjete nigdje, pa prazan popis ne znači da ih nema.

## P2

Yes, it is a real thing. Horizontalna mobilnost is the UNIZG mechanism for taking individual courses at another constituent faculty while you stay enrolled in your own programme. Faculties publish their own rules for it — FKIT, for instance, under /horizontalna_mobilnost/ — and there are central UNIZG pages as well.

What I cannot tell you from the catalog: whether you specifically qualify, quotas, deadlines, whether your home faculty has to approve it, and how the ECTS get recognised. None of that is in ISVU. Confirm those with both student offices.

The catalog half I can do now. Name the subject and I'll call `unizg_courses(query="...")` with no faculty_id, which searches all 37 constituents and shows everywhere it is taught.

## P3

Iskreno: to je pravni dio, a njega nema u ISVU katalogu koji koristim. Ne mogu ti reći ni traženi prosjek ni cijenu bez izmišljanja, a uvjete propisuje svaka sastavnica zasebno, pa se stvarno razlikuju od fakulteta do fakulteta.

Sam mehanizam postoji i fakulteti ga objavljuju na svojim stranicama (npr. FKIT pod /horizontalna_mobilnost/), uz središnje UNIZG stranice. Provjeri konkretno: uvjete i eventualni prosjek, kvotu, rok prijave, treba li odobrenje matičnog fakulteta i kako se ECTS priznaju. Za to su ti potrebne obje referade.

Ono što ja mogu: točan predmet, ECTS i semestar. Reci koji te zanima i pozvat ću `unizg_courses(query=...)`, pa `unizg_course(faculty_id=..., code=...)`.

## P4

Ni to nije u katalogu. ISVU ima nastavne podatke o predmetu, ne pravila ocjenjivanja i evidencije ocjena po sastavnicama, pa ovdje ne bih zvao nijedan alat.

Ključno je ovo: utjecaj pada na prosjek ovisi o tome kako tvoj matični fakultet evidentira predmet upisan mobilnošću, a ne o fakultetu na kojem ga slušaš. Pravila se razlikuju, pa je odgovor specifičan za tvoj fakultet.

Pitaj svoju referadu unaprijed, prije upisa, i to izričito: kako se predmet evidentira, ulazi li ocjena u prosjek i što se dogodi ako ga ne položiš.

Mehanizam horizontalne mobilnosti postoji i uređen je po fakultetima — samo ISVU te odredbe ne objavljuje.

## P5

Both are real, established routes; they differ in scope.

Horizontalna mobilnost: you stay a student of one programme and take individual courses at another UNIZG faculty, with the ECTS brought back and recognised by your home faculty.

Paralelni studij: you are admitted as a full student to a second programme, carry both sets of obligations, and finish with two degrees. Admission requirements and fees normally apply.

For CS plus biology: mobilnost for a handful of biology courses alongside your degree; paralelni studij if you want the biology degree itself.

Catalog half: `unizg_programmes(faculty_id=119)` for PMF's biology programmes, then `unizg_curriculum(...)` to see the real load. Admission and recognition rules: both student offices.

## P6

Sam postupak nije u ISVU-u, pa ti dajem opći oblik i molim da ga potvrdiš, jer se detalji razlikuju po fakultetima.

Uobičajeno ide tako: prvo svoja referada ili prodekan za nastavu na matičnom fakultetu, jer oni odobravaju upis i kasnije priznaju ECTS. Tek onda referada fakulteta na kojem želiš slušati — zbog kvote, roka i dopuštenja predmetnog nastavnika. Nakon položenog ispita slijedi priznavanje na matičnom fakultetu.

Dakle: prvo se javljaš svojoj referadi. Prije toga pripremi točan naziv predmeta, šifru, ECTS i semestar, jer to obično traže na obrascu.

Tool: `unizg_course(faculty_id=..., code=...)` da ti izvučem upravo te podatke.
