#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
raspored.py, DAG kolegija + izračun najranijeg završetka svih kolegija.

Model:
  - Kolegiji su čvorovi; preduvjeti su usmjereni bridovi (preduvjet -> kolegij).
  - Kolegij se smješta u prvi semestar nakon svih svojih preduvjeta (izravnih i posrednih):
        earliest = max(earliest(preduvjeti)) + 1;  korijeni (bez preduvjeta) = 1.
  - "Pack tight": semestar = dubina u lancu preduvjeta. Sezona (zimski/ljetni) je samo
    oznaka i ne ograničava smještaj. Rezultat = najmanji broj semestara da se sve odsluša.

Ulaz:  kolegiji.json  (vidi format u tom fileu)
Pokretanje:  python3 raspored.py [putanja_do_json]
"""

import json
import math
import sys
from collections import defaultdict


def ucitaj(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    kolegiji = data["kolegiji"]
    po_nazivu = {}
    for k in kolegiji:
        naziv = k["naziv"]
        if naziv in po_nazivu:
            raise ValueError(f"Dvostruki kolegij u podacima: {naziv!r}")
        sem = k["semestar"].strip().lower()
        if sem not in ("zimski", "ljetni"):
            raise ValueError(f"{naziv}: 'semestar' mora biti 'zimski' ili 'ljetni', a je {k['semestar']!r}")
        po_nazivu[naziv] = k
    return kolegiji, po_nazivu


def preduvjeti_naziva(k):
    """Vrati listu naziva preduvjeta (podržava i string i {'kolegij': ...})."""
    out = []
    for p in k.get("preduvjeti", []):
        out.append(p if isinstance(p, str) else p["kolegij"])
    return out


def provjeri(kolegiji, po_nazivu):
    """Provjeri da svi preduvjeti postoje i da nema ciklusa (da je pravi DAG)."""
    for k in kolegiji:
        for pn in preduvjeti_naziva(k):
            if pn not in po_nazivu:
                raise ValueError(f"{k['naziv']}: nepoznat preduvjet {pn!r} (nema ga u kolegiji.json)")

    # detekcija ciklusa (DFS s bojama)
    BIJELA, SIVA, CRNA = 0, 1, 2
    boja = {k["naziv"]: BIJELA for k in kolegiji}
    stack = []

    def dfs(n):
        boja[n] = SIVA
        stack.append(n)
        for pn in preduvjeti_naziva(po_nazivu[n]):
            if boja[pn] == SIVA:
                ciklus = stack[stack.index(pn):] + [pn]
                raise ValueError("Ciklus u preduvjetima: " + " -> ".join(ciklus))
            if boja[pn] == BIJELA:
                dfs(pn)
        stack.pop()
        boja[n] = CRNA

    for k in kolegiji:
        if boja[k["naziv"]] == BIJELA:
            dfs(k["naziv"])


def u_sezoni(sem, k):
    """Prvi semestar >= sem koji je u sezoni kolegija.

    Kolegij se izvodi samo u svojoj sezoni: zimski u neparnim, ljetni u parnim
    semestrima. Ako prvi semestar nakon preduvjeta ima pogrešan paritet, kolegij
    čeka jedan semestar više.
    """
    treba_neparni = k["semestar"] != "ljetni"
    return sem if (sem % 2 == 1) == treba_neparni else sem + 1


def izracunaj_najranije(kolegiji, po_nazivu):
    """earliest[naziv] = prvi semestar u sezoni kolegija nakon svih preduvjeta."""
    najranije = {}

    def rijesi(naziv):
        if naziv in najranije:
            return najranije[naziv]
        k = po_nazivu[naziv]
        m = 0
        for pn in preduvjeti_naziva(k):
            m = max(m, rijesi(pn))
        najranije[naziv] = u_sezoni(m + 1, k)
        return najranije[naziv]

    for k in kolegiji:
        rijesi(k["naziv"])
    return najranije


def nominalni_semestar(k):
    """Semestar prema službenom planu iz godine + pariteta."""
    g = k["godina"]
    return 2 * g - 1 if k["semestar"] == "zimski" else 2 * g


def ispis(kolegiji, po_nazivu, najranije):
    naz = "═"
    print("\n" + naz * 68)
    print("  DAG PREDUVJETA (usmjereni bridovi: preduvjet ──▶ kolegij)")
    print(naz * 68)
    ima_brid = False
    for k in sorted(kolegiji, key=lambda x: x["naziv"]):
        for p in k.get("preduvjeti", []):
            pn = p if isinstance(p, str) else p["kolegij"]
            uvjet = "" if isinstance(p, str) else f"  [{p.get('uvjet','')}]"
            print(f"  {pn}  ──▶  {k['naziv']}{uvjet}")
            ima_brid = True
    if not ima_brid:
        print("  (nema preduvjeta, svi kolegiji su korijeni)")

    print("\n" + naz * 68)
    print("  LISTA SUSJEDSTVA (kolegij : preduvjeti)")
    print(naz * 68)
    for k in sorted(kolegiji, key=lambda x: x["naziv"]):
        pv = preduvjeti_naziva(k)
        print(f"  {k['naziv']}: {pv if pv else '[]'}")

    print("\n" + naz * 68)
    print("  NAJRANIJI RASPORED (dubina lanca preduvjeta + sezona kolegija)")
    print(naz * 68)
    print(f"  {'kolegij':32} {'najraniji':>10} {'godina':>7}  {'(plan)':>7}")
    print("  " + "-" * 62)
    ects_po_sem = defaultdict(int)
    for k in sorted(kolegiji, key=lambda x: (najranije[x["naziv"]], x["naziv"])):
        s = najranije[k["naziv"]]
        god = math.ceil(s / 2)
        parbaba = "Z" if s % 2 == 1 else "Lj"
        plan = nominalni_semestar(k)
        oznaka = "" if plan == s else f"  (plan: {plan}.)"
        print(f"  {k['naziv']:32} {str(s)+'. ('+parbaba+')':>10} {god:>7}  {plan:>6}.{oznaka}")
        ects_po_sem[s] += k.get("ects", 0)

    ukupno = max(najranije.values())
    godina = math.ceil(ukupno / 2)
    print("\n" + naz * 68)
    print("  ECTS opterećenje po semestru (compress raspored)")
    print(naz * 68)
    for s in range(1, ukupno + 1):
        par = "zimski" if s % 2 == 1 else "ljetni"
        print(f"  {s}. semestar ({par}): {ects_po_sem.get(s,0)} ECTS")

    print("\n" + naz * 68)
    print(f"  NAJRANIJI ZAVRŠETAK SVIH KOLEGIJA: {ukupno}. semestar  ({godina}. godina)")
    print(f"  Ukupno semestara: {ukupno}  |  ukupno ECTS: {sum(k.get('ects',0) for k in kolegiji)}")
    print(naz * 68 + "\n")


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "kolegiji.json"
    try:
        kolegiji, po_nazivu = ucitaj(path)
        provjeri(kolegiji, po_nazivu)
        najranije = izracunaj_najranije(kolegiji, po_nazivu)
    except (ValueError, KeyError, FileNotFoundError) as e:
        print(f"GREŠKA: {e}", file=sys.stderr)
        sys.exit(1)
    ispis(kolegiji, po_nazivu, najranije)


if __name__ == "__main__":
    main()
