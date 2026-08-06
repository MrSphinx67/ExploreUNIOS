# Kolegiji DAG + najraniji raspored

Mali alat: modelira kolegije preddiplomskog studija **Programsko inženjerstvo (redovni), FERIT,
Sveučilište Josipa Jurja Strossmayera u Osijeku** kao **DAG** (čvor = kolegij, usmjereni brid =
preduvjet) i računa **najraniji semestar** u kojem se svaki kolegij može odslušati te **najraniji
završetak svih** kolegija.

`kolegiji.json` u ovom folderu je identičan popisu kolegija u root `kolegiji.json`-u (zadani popis
web-app scheduler-a): ovaj alat postoji da neovisno o pregledniku provjeri isti DAG iz komandne
linije, pa oba fajla namjerno drže isti `kolegiji` niz.

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
Kolegiji, semestri, ECTS i preduvjeti preuzeti iz ISVU javnog kataloga, preko `unios_dag_json` alata
(`faculty_id=165` za FERIT, `razina=3`, `izvedba=R`, `smjer=67`). Vidi komentar na vrhu `js/data.js`
za isti izvor koji koristi web-app scheduler. FERIT u ISVU-u ne objavljuje strukturirane upisne
preduvjete za ovaj program, pa su svi `preduvjeti` u `kolegiji.json` prazni; uređuj slobodno ako želiš
modelirati vlastite pretpostavke o redoslijedu.
