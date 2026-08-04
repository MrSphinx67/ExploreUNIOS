// Zadani popis kolegija: podskup preddiplomskog studija Molekularna biologija (PMF UNIZG).
// Izvor preduvjeta: službeni INFO modali kolegija (polje "Preduvjeti za: Upis predmeta").
// semestar: "zimski" = neparni (1,3,5), "ljetni" = parni (2,4,6). godina = ceil(semestar/2).
// uvjet: "polozen" = položen ispit, "odslusan" = odslušan kolegij (oba: preduvjet u ranijem semestru).
(function () {
  const PMF = (window.PMF = window.PMF || {});

  const DEFAULT_KOLEGIJI = [
    { naziv: "Biologija stanice", semestar: "zimski", godina: 1, status: "obavezni", ects: 8, preduvjeti: [] },
    { naziv: "Opća i anorganska kemija", semestar: "zimski", godina: 1, status: "obavezni", ects: 12, preduvjeti: [] },
    {
      naziv: "Organska kemija", semestar: "ljetni", godina: 1, status: "obavezni", ects: 8,
      preduvjeti: [{ kolegij: "Opća i anorganska kemija", uvjet: "odslusan" }],
    },
    {
      naziv: "Bakteriologija i virologija", semestar: "zimski", godina: 2, status: "obavezni", ects: 9,
      preduvjeti: [{ kolegij: "Biologija stanice", uvjet: "polozen" }],
    },
    {
      naziv: "Genetika", semestar: "ljetni", godina: 2, status: "obavezni", ects: 9,
      preduvjeti: [{ kolegij: "Biologija stanice", uvjet: "polozen" }],
    },
    {
      naziv: "Biokemija 1", semestar: "ljetni", godina: 2, status: "obavezni", ects: 9,
      preduvjeti: [
        { kolegij: "Biologija stanice", uvjet: "polozen" },
        { kolegij: "Opća i anorganska kemija", uvjet: "polozen" },
        { kolegij: "Organska kemija", uvjet: "polozen" },
      ],
    },
    { naziv: "Histologija i histokemija", semestar: "ljetni", godina: 2, status: "izborni", ects: 5, preduvjeti: [] },
    {
      naziv: "Biokemija 2", semestar: "zimski", godina: 3, status: "obavezni", ects: 7,
      preduvjeti: [{ kolegij: "Biokemija 1", uvjet: "odslusan" }],
    },
    { naziv: "Imunologija i imunogenetika", semestar: "zimski", godina: 3, status: "izborni", ects: 7, preduvjeti: [] },
    {
      naziv: "Molekularna genetika", semestar: "ljetni", godina: 3, status: "obavezni", ects: 8,
      preduvjeti: [
        { kolegij: "Biokemija 1", uvjet: "polozen" },
        { kolegij: "Genetika", uvjet: "polozen" },
        { kolegij: "Biokemija 2", uvjet: "odslusan" },
      ],
    },
  ];

  PMF.data = {
    DEFAULT_KOLEGIJI,
    SEMESTRI: ["zimski", "ljetni"],
    STATUSI: ["obavezni", "izborni"],
    UVJETI: ["polozen", "odslusan"],
  };
})();
