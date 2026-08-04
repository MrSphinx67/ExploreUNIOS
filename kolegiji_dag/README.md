# Kolegiji DAG + najraniji raspored

Mali alat: modelira kolegije preddiplomskog studija **Molekularna biologija (PMF UNIZG)** kao
**DAG** (čvor = kolegij, usmjereni brid = preduvjet) i računa **najraniji semestar** u kojem se
svaki kolegij može odslušati te **najraniji završetak svih** kolegija.

## Datoteke
- **`kolegiji.json`**: izvor istine. Za svaki kolegij: `naziv`, `semestar` (`zimski`|`ljetni`),
  `godina`, `status`, `ects`, `preduvjeti`. Ručno se uređuje.
- **`raspored.py`**: čita `kolegiji.json`, gradi DAG, provjerava (nepoznati preduvjeti, ciklusi) i
  ispisuje raspored. Bez vanjskih ovisnosti (samo Python 3 standardna biblioteka).

## Pokretanje
```bash
python3 raspored.py            # koristi kolegiji.json iz istog foldera
python3 raspored.py put/do.json
```

## Format preduvjeta
```json
"preduvjeti": [
  { "kolegij": "Biokemija 1", "uvjet": "polozen" },
  { "kolegij": "Biokemija 2", "uvjet": "odslusan" }
]
```
- `uvjet: "polozen"` = mora biti položen ispit prije upisa.
- `uvjet: "odslusan"` = mora biti odslušan kolegij prije upisa.
- Za raspored oba znače isto: **preduvjet mora biti u ranijem semestru**. (Podržan je i običan
  string umjesto objekta: `"preduvjeti": ["Biokemija 1"]`.)

## Model rasporeda ("compress")
- Semestri 1,2,3,…; **zimski = neparni**, **ljetni = parni**.
- Kolegij smije biti u semestru `S` ako `S` ima ispravan paritet **i** svi preduvjeti su u strogo
  ranijem semestru.
- Svaki kolegij se gura u **najraniji** dopušteni semestar (nominalna godina iz plana se ignorira),
  pa je rezultat pravi minimalni broj semestara. U ispisu se uz `najraniji` prikazuje i `(plan: N.)`
  gdje se razlikuje od službenog plana.

## Izvor podataka
Preduvjeti i semestri preuzeti iz službenih INFO modala kolegija
(`Preduvjeti za: Upis predmeta`) na
<https://www.pmf.unizg.hr/studiji/preddiplomski_studiji/bioloski_odsjek/molekularna_biologija>.
Provjeri i po potrebi ispravi u `kolegiji.json`.
