SELECT
    lfa1.LIFNR AS "S_Lieferant.Lieferant",
    lfa1.ADRNR AS "S_Adresse.AdressNr",
    lfa1.NAME1 AS "S_Adresse.Name1",
    adrc.COUNTRY AS "S_Adresse.Staat",
    adrc.CITY1 AS "S_Adresse.Ort",
    adrc.TITLE AS "S_Adresse.Titel",
    adrc.NAME2 AS "S_Adresse.Name2",
    adrc.NAME3 AS "S_Adresse.Name3",
    adrc.POST_CODE1 AS "S_Adresse.PLZ",
    adrc.CITY2 AS "S_Adresse.CityPostfix",
    adrc.STREET AS "S_Adresse.Strasse",
    adrc.HOUSE_NUM1 AS "S_Adresse.Hausnummer",
    adrc.REGION AS "S_Adresse.Bundesland",
    adrc.POST_CODE2 AS "S_Adresse.PLZ_Postfach",
    adrc.PO_BOX AS "S_Adresse.Postfach",
    adr6.SMTP_ADDR AS "S_Adresse.EMail",
    adr2.TEL_NUMBER AS "S_Adresse.Telefon",
    adr3.FAX_NUMBER AS "S_Adresse.Telefax",
    lfa1.TELF2 AS "S_Adresse.Telefon2",
    lfa1.MCOD1 AS "S_Lieferant.Suchbegriff",
    lfa1.MCOD2 AS "S_Lieferant.Selektion",
    lfa1.BRSCH AS "S_Lieferant.Branche",
    lfa1.PLKAL AS "S_Lieferant.Betriebskalender",
    lfa1.SPRAS AS "S_Lieferant.Sprache",
    lfa1.STCD1 AS "S_Lieferant.inlaendische_SteuerNr",
    lfa1.STCEG AS "S_UStID.UStID",
    lfb1.ZWELS AS "S_Lieferant.ZahlungsArt",
    lfb1.ZTERM AS "S_Lieferant.ZahlungsZiel",
    lfa1.STKZU AS "S_UStID.bestaetigt"
FROM
    main.lfa1 AS lfa1
LEFT JOIN main.lfb1 AS lfb1
    ON lfa1.LIFNR = lfb1.LIFNR
LEFT JOIN main.adrc AS adrc
    ON lfa1.ADRNR = adrc.ADDRNUMBER
LEFT JOIN main.adr2 AS adr2
    ON lfa1.ADRNR = adr2.ADDRNUMBER
LEFT JOIN main.adr3 AS adr3
    ON lfa1.ADRNR = adr3.ADDRNUMBER
LEFT JOIN main.adr6 AS adr6
    ON lfa1.ADRNR = adr6.ADDRNUMBER