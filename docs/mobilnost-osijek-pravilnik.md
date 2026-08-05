# Mobilnost studenta — Sveučilište Josipa Jurja Strossmayera u Osijeku

## Status izvora (bitno pročitati prije korištenja)

Postoje tri poznate verzije Pravilnika o studijima i studiranju SUJJS:

1. **Srpanj 2015.** — stara verzija, članci 40-41 (superseded)
2. **Prosinac 2023.** — usvojena verzija nakon javnog savjetovanja (nacrt iz rujna
   2023.), članci 36-37. **Ovaj tekst je dolje.**
3. **Ožujak 2025.** — noviji "pročišćeni tekst" koji konsolidira usvojeni tekst s
   naknadnim izmjenama. Nije bilo moguće provjeriti sadržaj jer je PDF na
   gfos.unios.hr zaštićen lozinkom za preuzimanje. **Prije korištenja u produkciji,
   provjeriti kod Ureda za studente ili na fakultetu je li poglavlje o mobilnosti
   (čl. 36-37 u verziji iz prosinca 2023.) mijenjano tom konsolidacijom.**

Izvor teksta ispod: nacrt Pravilnika, rujan 2023., javno savjetovanje
(https://www.unios.hr/wp-content/uploads/2023/09/2-NACRT-prijedloga-Pravilnika-o-studijima-i-studiranju-javno-savjetovanje-9.2023.pdf),
potvrđeno da je usvojen u prosincu 2023. (potvrđeno preko popisa akata Pravnog
fakulteta Osijek i FDMZ Osijek, koji obojica navode "Pravilnik o studijima i
studiranju... (prosinac 2023.)").

---

## Mobilnost studenata u okviru Sveučilišta

**Članak 36.**

(1) Student može upisati pojedine kolegije s istog studija drugog smjera ili nekog
drugog studija ako je te kolegije nositelj studija utvrdio u studijskom programu.

(2) Student može upisati pojedine izborne kolegije prema popisu izbornih kolegija
Sveučilišta koje za svaku akademsku godinu na temelju prijedloga nositelja studija na
Sveučilištu donosi Senat Sveučilišta za sve nositelje studija na Sveučilištu.

(3) Ostvareni bodovi prema ECTS-u priznaju se kao da su ostvareni u okviru matičnog
sveučilišnog studija (studijskog programa), a bodovna vrijednost kolegija odgovara
onoj koju taj kolegij ima na studiju odnosno programu u okviru kojeg se izvodi ili
može biti novi izborni kolegij koje se upisuje u studentsku ispravu. Nositelj kolegija
potvrđuje ispunjenje studijskih obveza upisom bodova prema ECTS-u i ocjene te svojim
potpisom u studentsku ispravu.

(4) Broj studenata koji mogu upisati pojedini izborni kolegij ograničen je kapacitetom
sveučilišne sastavnice o čemu odlučuje ovlašteno tijelo sastavnice na prijedlog
nositelja kolegija.

(5) Troškovi izvedbe kolegija u okviru mobilnosti studenta unutar Sveučilišta
određuju se Odlukom Senata.

## Mobilnost studenata među hrvatskim sveučilištima i između hrvatskih sveučilišta i
inozemnih sveučilišta

**Članak 37.**

Mobilnost studenta među hrvatskim sveučilištima i između hrvatskih sveučilišta i
inozemnih sveučilišta uređuje se na temelju posebnih ugovora.

---

## Ključne točke za implementaciju u kodu (unios_mobility_rules alat)

1. **Nije automatsko pravo.** Upis kolegija na drugom smjeru/studiju/fakultetu
   ovisi o tome je li nositelj studija to unaprijed predvidio u studijskom programu
   (čl. 36 st. 1). Alat ne smije sugerirati da je to univerzalno pravo studenta.

2. **Poseban kanal za izborne kolegije.** Postoji zaseban, sveučilišni popis
   izbornih kolegija koji svake godine donosi Senat (čl. 36 st. 2) — to je odvojeno
   od "obične" mobilnosti iz st. 1, i ima svoj mehanizam ograničenja kapaciteta
   (st. 4).

3. **Priznavanje ECTS bodova je fleksibilno** — mogu se priznati unutar matičnog
   programa ili upisati kao potpuno novi izborni kolegij u studentsku ispravu
   (čl. 36 st. 3).

4. **Troškovi se određuju Odlukom Senata** (čl. 36 st. 5) — dakle postoji
   centralizirani, formalni mehanizam (za razliku od stare 2015. verzije koja je to
   prepuštala "posebnom ugovoru"). Ako korisnik pita za konkretan iznos, alat treba
   reći da je to regulirano Odlukom Senata i uputiti na trenutno važeću odluku (koju
   treba posebno tražiti — nije dio ovog Pravilnika), a ne izmišljati broj.

5. **Međusveučilišna/inozemna mobilnost (čl. 37) ostaje oskudno regulirana** —
   sve je prepušteno "posebnim ugovorima" bez detalja o postupku u ovom dokumentu.
   Alat treba jasno reći da nema više detalja u Pravilniku i uputiti na
   fakultet/Erasmus+ ured/Ugovor o studiranju, ne izvoditi zaključke iz ovog teksta.
