// Zadani popis kolegija: preddiplomski studij Programsko inženjerstvo, izborni blok unutar
// Računarstvo (redovni), FERIT, Sveučilište Josipa Jurja Strossmayera u Osijeku.
// Izvor: ISVU, preko unizg_dag_json (faculty_id=165, razina=3, izvedba=R, smjer=67).
// semestar: "zimski" = neparni (1,3,5), "ljetni" = parni (2,4,6). godina = ceil(semestar/2).
// uvjet: "polozen" = položen ispit, "odslusan" = odslušan kolegij (oba: preduvjet u ranijem semestru).
// FERIT ne objavljuje strukturirane upisne preduvjete za ovaj program, pa su svi preduvjeti prazni.
(function () {
  const PMF = (window.PMF = window.PMF || {});

  const DEFAULT_KOLEGIJI = [
    { naziv: "Inženjerska grafika i dokumentiranje", semestar: "zimski", godina: 1, status: "obavezni", ects: 3, preduvjeti: [] },
    { naziv: "Linearna algebra", semestar: "zimski", godina: 1, status: "obavezni", ects: 5, preduvjeti: [] },
    { naziv: "Matematičke osnove računarstva", semestar: "zimski", godina: 1, status: "obavezni", ects: 5, preduvjeti: [] },
    { naziv: "Matematika I", semestar: "zimski", godina: 1, status: "obavezni", ects: 5, preduvjeti: [] },
    { naziv: "Osnove elektrotehnike i elektronike", semestar: "zimski", godina: 1, status: "obavezni", ects: 6, preduvjeti: [] },
    { naziv: "Programiranje I", semestar: "zimski", godina: 1, status: "obavezni", ects: 5, preduvjeti: [] },
    { naziv: "Tjelesna kultura I", semestar: "zimski", godina: 1, status: "obavezni", ects: 1, preduvjeti: [] },
    { naziv: "Digitalna elektronika", semestar: "ljetni", godina: 1, status: "obavezni", ects: 6, preduvjeti: [] },
    { naziv: "Ekonomika poduzeća", semestar: "ljetni", godina: 1, status: "obavezni", ects: 6, preduvjeti: [] },
    { naziv: "Komunikacijske vještine", semestar: "ljetni", godina: 1, status: "obavezni", ects: 6, preduvjeti: [] },
    { naziv: "Matematika II", semestar: "ljetni", godina: 1, status: "obavezni", ects: 6, preduvjeti: [] },
    { naziv: "Programiranje II", semestar: "ljetni", godina: 1, status: "obavezni", ects: 5, preduvjeti: [] },
    { naziv: "Tjelesna kultura II", semestar: "ljetni", godina: 1, status: "obavezni", ects: 1, preduvjeti: [] },
    { naziv: "Algoritmi i strukture podataka", semestar: "zimski", godina: 2, status: "obavezni", ects: 6, preduvjeti: [] },
    { naziv: "Baze podataka", semestar: "zimski", godina: 2, status: "obavezni", ects: 6, preduvjeti: [] },
    { naziv: "Linearna algebra II", semestar: "zimski", godina: 2, status: "obavezni", ects: 5, preduvjeti: [] },
    { naziv: "Objektno orijentirano programiranje", semestar: "zimski", godina: 2, status: "obavezni", ects: 6, preduvjeti: [] },
    { naziv: "Operacijski sustavi", semestar: "zimski", godina: 2, status: "obavezni", ects: 6, preduvjeti: [] },
    { naziv: "Tjelesna kultura III", semestar: "zimski", godina: 2, status: "obavezni", ects: 1, preduvjeti: [] },
    { naziv: "Engleski jezik I", semestar: "ljetni", godina: 2, status: "obavezni", ects: 2, preduvjeti: [] },
    { naziv: "Komunikacijske mreže", semestar: "ljetni", godina: 2, status: "obavezni", ects: 6, preduvjeti: [] },
    { naziv: "Razvoj programske podrške objektno orijentiranim načelima", semestar: "ljetni", godina: 2, status: "obavezni", ects: 5.5, preduvjeti: [] },
    { naziv: "Signali i sustavi", semestar: "ljetni", godina: 2, status: "obavezni", ects: 5, preduvjeti: [] },
    { naziv: "Teorija informacije", semestar: "ljetni", godina: 2, status: "obavezni", ects: 5.5, preduvjeti: [] },
    { naziv: "Tjelesna kultura IV", semestar: "ljetni", godina: 2, status: "obavezni", ects: 1, preduvjeti: [] },
    { naziv: "Vjerojatnost i statistika", semestar: "ljetni", godina: 2, status: "obavezni", ects: 5, preduvjeti: [] },
    { naziv: "Osnove mainframe tehnologije", semestar: "ljetni", godina: 2, status: "izborni", ects: 2.5, preduvjeti: [] },
    { naziv: "Arhitektura računala", semestar: "zimski", godina: 3, status: "obavezni", ects: 7, preduvjeti: [] },
    { naziv: "Automati i formalni jezici", semestar: "zimski", godina: 3, status: "obavezni", ects: 7, preduvjeti: [] },
    { naziv: "Engleski jezik II", semestar: "zimski", godina: 3, status: "obavezni", ects: 3, preduvjeti: [] },
    { naziv: "Osnove razvoja web i mobilnih aplikacija", semestar: "zimski", godina: 3, status: "obavezni", ects: 6, preduvjeti: [] },
    { naziv: "Programsko inženjerstvo", semestar: "zimski", godina: 3, status: "obavezni", ects: 7, preduvjeti: [] },
    { naziv: "Engleski jezik III", semestar: "ljetni", godina: 3, status: "obavezni", ects: 3, preduvjeti: [] },
    { naziv: "Kibernetička sigurnost", semestar: "ljetni", godina: 3, status: "obavezni", ects: 5, preduvjeti: [] },
    { naziv: "Osnove analize podataka", semestar: "ljetni", godina: 3, status: "obavezni", ects: 6, preduvjeti: [] },
    { naziv: "Osnove strojnog učenja", semestar: "ljetni", godina: 3, status: "obavezni", ects: 6, preduvjeti: [] },
    { naziv: "Završni rad", semestar: "ljetni", godina: 3, status: "obavezni", ects: 10, preduvjeti: [] },
  ];

  PMF.data = {
    DEFAULT_KOLEGIJI,
    SEMESTRI: ["zimski", "ljetni"],
    STATUSI: ["obavezni", "izborni"],
    UVJETI: ["polozen", "odslusan"],
  };
})();
