# Fradragsregler for inngående merverdiavgift – kunnskapsgrunnlag for bilagsvurdering

Status: september 2026. Reglene er gjennomgått av en research-agent og deretter kontrollert av en verifikator mot lovtekst på Lovdata (mval. LOV-2009-06-19-58, FMVA FOR-2009-12-15-1540, bokf.f. FOR-2004-12-01-1558, skatteforvaltningsforskriften FOR-2016-11-23-1360, kassasystemforskrifta FOR-2015-12-18-1616) og Skatteetatens Merverdiavgiftshåndbok (MVAH, «gjeldende», 2025-utgaven). Filen tar bare med regler som verifikatoren har bekreftet eller rettet. Påstander verifikatoren avviste, er fjernet.

**Merking**
- Uten merke: bekreftet eller rettet, og kan brukes som grunnlag for AVVIK.
- **[USIKKER]**: ikke verifisert i primærkilde, eller uavklart rettslig. Skal aldri gi AVVIK alene, bare «må avklares».
- **[SKJØNN]**: rettsregelen er klar, men utfallet avhenger av fakta eller skjønn. Agenten flagger og begrunner, men konkluderer ikke.

**Forkortelser**
- mval. = merverdiavgiftsloven
- FMVA = mva-forskriften
- bokf.f. = bokføringsforskriften
- sktfvl. = skatteforvaltningsloven
- MVAH x-y = Merverdiavgiftshåndboken kapittel x-y. Grunn-URL: `https://www.skatteetaten.no/rettskilder/type/handboker/merverdiavgiftshandboken/gjeldende/`, der kapittelet legges til, for eksempel `M-8/M-8-3/M-8-3.6/`.

**Kodene** er SAF-T-standardkodene, som Tripletex bruker som `vatType.number`. Det er ikke verifisert per klient at Tripletex følger dem. Bekreft med `GET /ledger/vatType` før bruk.

---

## 0. Satser og beløpsgrenser 2026

| Hva | Verdi | Hjemmel |
|---|---|---|
| Alminnelig sats | 25 % | mval. § 5-1 |
| Næringsmidler | 15 % (ikke alkohol, tobakk, legemidler) | § 5-2 |
| Vann fra vannverk og avløpstjenester, inkl. slamtømming og vannmåler levert med tjenesten | 15 % fra 1.7.2025 (før det 25 %) | § 5-12, FMVA § 5-12-1 |
| Persontransport, ferje, romutleie i hotell, møte- og konferanselokale på hotell, kino, museum og lignende | 12 % | §§ 5-3, 5-4, 5-5, 5-9 |
| Råfisk | 11,11 % (kode 12) | § 5-7 |
| Registreringsgrense | 50 000 kr i omsetning og uttak over 12 måneder, løpende. 140 000 kr for veldedige og allmennyttige | § 2-1 første ledd |
| Betaling via bank er vilkår for fradrag | når samlet betaling er 10 000 kr eller mer (bare «mindre enn 10 000» er unntatt) | § 8-8 |
| Omvendt avgiftsplikt for kjøper som ikke er registrert | når kjøpene i terminen overstiger 2 000 kr eks. mva | §§ 11-3, 11-1 annet og tredje ledd |
| Bagatellgrense for gaver og reklameartikler | 200 kr per enhet fra 1.1.2025. MVAH viser fortsatt 100 kr og er utdatert | FMVA § 1-3-6 |
| Kjøper skal angis ved kontantkjøp fra detaljist | over 1 000 kr inkl. mva, med mindre det er betalt med virksomhetens eget kort | bokf.f. § 5-5-1 annet ledd |
| Kapitalvare, maskiner og inventar | inngående mva ≥ 50 000 kr (tilsvarer ca. 200 000 kr eks. mva) | § 9-1 annet ledd bokstav a |
| Kapitalvare, byggetiltak på fast eiendom | inngående mva ≥ 100 000 kr | § 9-1 annet ledd bokstav b |
| Tilbakegående avgiftsoppgjør | kjøp inntil 3 år før registrering, og kravet må settes fram innen 3 år etter | § 8-6 |
| Retting av tidligere terminer | 3 år etter leveringsfristen | sktfvl. § 9-4. En endring er vedtatt (lov 19.06.2026 nr. 41), men ikke i kraft. Sjekk på nytt |

Satsene er ikke endret for 2026 (statsbudsjettet 2026). Fritaket for elbil er redusert til 300 000 kr fra 1.1.2026, men det påvirker ikke fradraget, fordi personkjøretøy uansett ikke gir fradrag.

---

## 1. Slik gjøres vurderingen (fast rekkefølge)

Ta spørsmålene i denne rekkefølgen for hvert bilag. Stopp når svaret gir «ingen fradrag», men noter eventuelle feil fra senere trinn (for eksempel omvendt avgiftsplikt eller registreringsplikt).

1. **Er klienten registrert på fakturadatoen?** (`/ledger/vatSettings`, Brreg-registreringsdato)
   - Nei: ingen fradrag. Gå til seksjon 7 om klienter som ikke er registrert.
   - Fakturaen er fra før registreringen: § 8-6, tilbakegående oppgjør (seksjon 6.12).
2. **Er det et gyldig salgsdokument fra en registrert selger, stilet til klienten?** (seksjon 2)
3. **Er kjøpet til bruk i den avgiftspliktige virksomheten?** (§ 8-1, tilknytning og tilordning). Kjøp som gjelder eierrollen, aksjer, unntatt eiendomssalg eller private forhold gir ikke fradrag.
4. **Er fradraget avskåret etter § 8-3 eller § 8-4?** (seksjon 3). Kjøp av samme art som klienten selv selger, gir likevel fradrag etter § 8-5.
5. **Brukes kjøpet delvis til noe annet?** Da gis forholdsmessig fradrag etter § 8-2 (seksjon 6.1).
6. **Er satsen og beløpet riktige?** Fradrag gis bare for det som faktisk er mva (§ 11-4). Sjekk at koden passer med satsen, at satsen passer med ytelsen, at det ikke er mva på en unntatt ytelse og at regnestykket stemmer.
7. **Er terminen riktig?** Fakturadatoen avgjør (§ 15-9).
8. **Er betalingen gjort via bank** når beløpet er 10 000 kr eller mer (§ 8-8)?
9. **Gjelder spesialregler?** Omvendt avgiftsplikt, import, kreditnota, kapitalvare, uttak og § 3-26.

Tre ting gjelder uansett:
- En EHF som avstemmer beløpsmessig, beviser bare at beløpet stemmer. Den beviser ikke fradragsretten. Trinn 3–5 må alltid vurderes.
- Kontonavn i NS 4102 som «7350 Representasjon, fradragsberettiget», «7420 Gave, fradragsberettiget» og «7410 Kontingent, fradragsberettiget» gjelder **inntektsskatt**, ikke mva.
- Formfeil vurderes etter om de gir reell tvil om fradragsretten eller risiko for dobbelt fradrag. Agenten flagger og begrunner, men nekter ikke fradrag automatisk der Skatteetaten ville gjort en konkret vurdering.

---

## 2. Hovedregel og dokumentasjonskrav

### 2.1 Hovedregel (§ 8-1)
Bare et registrert avgiftssubjekt har fradrag, og bare for inngående mva på varer og tjenester til bruk i den registrerte virksomheten. Det omfatter også innførselsmva og mva klienten selv beregner ved omvendt avgiftsplikt. Virksomhet med nullsatsomsetning (fritatt, kap. 6) har også fradrag.
- Hjemmel: mval. § 8-1, jf. § 1-3 første ledd bokstav f («påløpt» mva). MVAH 8-1.2.
- Kilde: https://lovdata.no/dokument/NL/lov/2009-06-19-58

### 2.2 Tilknytningskravet
Kjøpet må være relevant for og ha en «naturlig og nær tilknytning» til den avgiftspliktige virksomheten. At kjøpet er bedriftsøkonomisk fornuftig, er ikke nok. Vurderingen gjøres ut fra forholdene da kjøpet ble gjort. Kostnader til en unntatt transaksjon gir i utgangspunktet ikke fradrag. Typiske eksempler er aksjekjøp eller -salg, emisjon, due diligence, generalforsamling, fisjon eller fusjon og salg av fast eiendom.
- Signaler: advokat, revisor, corporate finance eller megler med slike ord i fakturateksten.
- Hjemmel: § 8-1. Rt. 1985 s. 93 (Sira-Kvina), Rt. 2001 s. 1497 (Norwegian Contractors), Rt. 2012 s. 432 (Elkjøp), Rt. 2015 s. 652 (Telenor), HR-2017-1851-A (Skårer Syd Holding), HR-2021-2025-A (Staten II). MVAH 8-1.3 og 8-1.4.
- Kilde: MVAH `M-8/M-8-1/M-8-1.3/`
- **[SKJØNN]** når formålet er uklart.

### 2.3 Tilordning: riktig kjøper
Bare den som har kjøpt ytelsen (kontraktspart eller oppdragsgiver) har fradrag. Kostnader som tilhører eier, aksjonær, et søsterselskap eller ansatte privat, gir ikke fradrag hos klienten. Det gjelder selv om klienten betaler, og selv om fakturaen er stilet til klienten.
- Unntak: fellesregistrering etter § 2-2 tredje ledd. Tilknytningskravet gjelder likevel.
- Hjemmel: § 8-1. Skattedirektoratets uttalelse 23.05.2023 (salgsdokumentet skal utstedes til kontraktsparten). MVAH 8-1.4 og 15-10.2.

### 2.4 Krav til bilaget (§ 15-10, bokf.f. kap. 5)
Fradrag krever **selgers salgsdokument** (bokf.f. § 5-5-1 første ledd) med dette innholdet (§§ 5-1-1, 5-1-2 og 5-1-5):
- nummer og dato
- selger med navn og org.nr., etterfulgt av «MVA» når selger er registrert. AS skal også ha «Foretaksregisteret»
- kjøper med navn og adresse eller org.nr. Ved omvendt avgiftsplikt skal kjøpers org.nr. alltid stå, med «MVA» hvis kjøper er registrert
- ytelsens art og omfang, leveringstid og -sted
- vederlag og forfall
- mva i NOK, spesifisert per sats, og med avgiftspliktig, fritatt og unntatt omsetning og omsetning med omvendt avgiftsplikt hver for seg

Er dokumentet feil eller mangelfullt, skal kjøper be om nytt (§ 5-5-1 siste ledd). Kopi og skannet PDF godtas, og det kreves ikke original.

**Dokumenter som IKKE er salgsdokument og ikke gir fradrag:** ordrebekreftelse, tilbud, proforma, purring, kontoutdrag eller saldoliste, betalingsbekreftelse, skjermbilde fra nettbank, e-post, eget internbilag, terminalslipp og kvitteringer merket «IKKJE KVITTERING FOR KJØP» (foreløpig kvittering, treningskvittering, utleveringskvittering ved kredittsalg og kvittering fra betalingsterminal som ikke er integrert). Fradraget kommer først med fakturaen eller salgskvitteringen.
- Hjemmel: mval. § 15-10 første ledd. bokf.f. §§ 5-1-1, 5-1-1a, 5-1-2, 5-1-5, 5-2-1, 5-5-1. Kassasystemforskrifta §§ 2-8-2 fjerde ledd og 2-8-6 til 2-8-8.
- Kilder: https://lovdata.no/dokument/SF/forskrift/2004-12-01-1558 og https://lovdata.no/dokument/SF/forskrift/2015-12-18-1616

**Språk:** Kravet om norsk, svensk, dansk eller engelsk (§ 5-1-1a, bokføringsloven § 12) binder selgere som er bokføringspliktige i Norge. En utenlandsk faktura på for eksempel tysk eller polsk er ikke ugyldig i seg selv, men kontrollmyndighetene kan kreve oversettelse. Klassifiseres som **TRENGER DOKUMENTASJON**, ikke AVVIK.

**KOPI og duplikat:** Kopikvittering skal være merket «KOPI», og kassasystemet kan bare skrive ut én. Samme leverandør og samme fakturanummer skal bare gi fradrag én gang. Sjekk særlig EHF og e-post-PDF av samme faktura, og utleveringskvittering sammen med samlefaktura. **[USIKKER]** om en kvittering merket «KOPI» alene gir fradrag. Godta den når originalen ikke er ført.

### 2.5 Selger må være registrert (§ 15-11, § 11-4)
Bare registrerte avgiftssubjekter og VOEC-tilbydere kan oppgi mva. «Mva» fra en selger som ikke er registrert, er ikke påløpt mva og gir ikke fradrag. Selger må selv betale beløpet (§ 11-4 annet ledd).
- Mens en registrering er til behandling, kan selger ikke fakturere mva. Etterfakturering etter registrering gir fradrag i terminen for den **nye** fakturaen (Skattedirektoratets brev 12.11.2012).
- Mangler «MVA» eller org.nr. og selger **ikke** er registrert: AVVIK. Unntaket er når kjøper kan dokumentere at Merverdiavgiftsregisteret ble sjekket og ga feil opplysning, og ingenting annet burde vekket mistanke (Skattedirektoratets brev 08.04.2008). Uten slike undersøkelser tolkes regelen strengt (Borgarting 26.04.2006).
- Mangler bare «MVA», men selger faktisk **er** registrert på fakturadatoen: formfeil. Be om ny faktura, men ikke automatisk «ingen fradrag». **[SKJØNN]**
- «VAT» alene er ikke nok, men «MVA (VAT)» godtas (Skattedirektoratet 25.09.2006).
- Formriktig faktura med «MVA» fra en selger som ikke er registrert: fradraget beholdes i utgangspunktet, med mindre kjøper visste eller burde visst (kvalifisert uaktsomhet). Rt. 1994 s. 889 (Dybs Fiskeprodukter).
- Utenlandske selgere fra EØS eller UK kan registreres direkte uten representant (§ 2-1 sjette ledd). Manglende representant er da ikke avvik i seg selv. Andre utenlandske selgere som er registrert via representant, skal oppgi representantens navn og adresse.
- «Foretaksregisteret» og hovedkontorets adresse er formkrav, men mangel er ikke i seg selv grunn til å nekte fradrag.
- Hjemmel: mval. § 15-11 første og annet ledd, § 11-4, § 15-10. bokf.f. § 5-1-2. MVAH 8-1.5 og 15-11.3.
- Kilde: MVAH `M-15/M-15-11/M-15-11.3/`
- Kontroll: Brreg `registrertIMvaregisteret` og `registreringsdatoMerverdiavgiftsregisteret`. Brreg viser bare status i dag. Slettede og nylig registrerte selgere må vurderes mot fakturadatoen.

### 2.6 Faktura stilet til feil kjøper
Etter langvarig praksis gir en faktura til en annen enn kjøper **ikke** fradrag. Det gjelder faktura til ansatt privat, eier, søster- eller holdingselskap, selskap med lignende navn og gammelt firmanavn. Feilen rettes med kreditnota og ny faktura. Den kan ikke rettes ved at mottakeren fakturerer videre.

Unntak:
- (a) Ansattes utlegg, for eksempel fly eller hotell i den ansattes navn, når vilkårene i bokf.f. § 5-5-1 fjerde ledd er oppfylt (Skattedirektoratet 23.05.2023).
- (b) Overgangsfase etter fusjon.
- (c) Faktura til en privatperson uten risiko for dobbelt fradrag, etter konkret vurdering (Skattedirektoratets vedtak 02.10.2014). **[SKJØNN]**
- (d) Registrert bedriftsnavn i stedet for foretaksnavn når org.nr. eller adresse er entydig (Skattedirektoratet 02.03.2010).

Tvil om navn eller adresse ved selskaper med nesten likt navn gir normalt ikke fradrag (KMVA 7824). Skadeoppgjør: reparasjonen må være fakturert skadevolderen. Er den fakturert forsikringsselskapet eller skadelidte, gir den ikke fradrag (F 18.06.1970, F 15.06.2001).
- Hjemmel: mval. § 15-10 første ledd. bokf.f. §§ 5-1-2 første ledd, 5-2-7, 5-5-1. MVAH 15-10.2.
- Kilde: MVAH `M-15/M-15-10/M-15-10.2/`
- GDPR: skriv «faktura stilet til privatperson», aldri navnet.

### 2.7 Kontantkjøp, kvitteringer og utlegg
- **Kontantkjøp fra detaljist** over 1 000 kr inkl. mva: kjøper skal angis, med mindre det er betalt med virksomhetens eget kort. Er kjøper ikke angitt, skal formålet fremgå, og bilaget dateres og signeres (bokf.f. § 5-5-1 annet og tredje ledd).
- **Selger skal alltid angi kjøper** når kjøper er bokføringspliktig og kjøpet gjelder
  - varer til videresalg eller direkte innsatsfaktor over 1 000 kr,
  - drivstoff til person- eller varetransport,
  - kontantbetaling på 40 000 kr eller mer (bokf.f. § 5-3-12 tredje ledd).
- Kvitteringen må vise hva som er kjøpt. Varegruppe er nok. En kvittering uten varelinjer gir ikke fradrag.
- **Utlegg fra ansatte:** arbeidsgiver skal stå som kjøper når kjøpet er til videresalg eller direkte innsatsfaktor over 1 000 kr. Ellers kreves en datert og signert oppstilling fra den ansatte med formål, og utlegget bør dokumenteres i samme termin (bokf.f. § 5-5-1 fjerde ledd, §§ 5-9 og 5-10 for bevertning).
- Diett og kilometergodtgjørelse har aldri mva. Utenlandsk mva gir aldri norsk fradrag.
- Kilde: https://lovdata.no/dokument/SF/forskrift/2004-12-01-1558

### 2.8 Betaling via bank (§ 8-8)
Fradrag forutsetter betaling via bank eller betalingsforetak når samlet betaling er 10 000 kr eller mer inkl. mva.
- Flere betalinger for samme leveranse eller kontrakt ses samlet (§ 8-8 første ledd).
- Løpende ytelser (husleie, lisenser, telefon, vakthold, revisjon, regnskap) ses samlet over året (§ 8-8 første ledd tredje punktum).
- Er fradrag ført før betaling, og betalingen senere skjer kontant, skal fradraget tilbakeføres i betalingsterminen (annet ledd).
- Kort, Vipps og nettbank godtas, og utenlandsk bank likestilles (FMVA § 8-8-1). Motregning er ikke hindret.
- **[USIKKER]** om betaling fra eiers private konto til leverandørens konto godtas. Ordlyden «konto til konto» taler for det.
- Signaler: leverandørgjeld lukket mot 1900 kasse, eller kontantkvitteringer over grensen.
- Kilde: MVAH `M-8/M-8-8/M-8-8.3/`

### 2.9 Feil beregnet mva (§ 11-4)
Fradrag gis bare for beløp som faktisk er mva. Det overskytende gir ikke fradrag. Det gjelder for høy sats, regnefeil, mva på unntatt ytelse (husleie fra utleier som ikke er frivillig registrert, forsikring, finans, helse, undervisning), mva på fritatt ytelse, mva på virksomhetsoverdragelse (§ 6-14) og mva på innenlands klimakvoter eller gull (§ 11-4 første ledd tredje punktum).
- Selger skal betale beløpet og kan rette med kreditnota.
- Skatteetaten etterberegner kjøper bare ved kvalifisert uaktsomhet, men agenten flagger alltid og ber om kreditnota.
- Hjemmel: § 8-1, § 11-4. Rt. 1997 s. 1564 (Naustdal Fiskefarm). Rt. 2000 s. 268 (Brødr. Gjermundshaug Anlegg). Rt. 2008 s. 727 (MMC Tendos). Fellesskriv 09.12.2011 pkt. 4. MVAH 8-1.5.
- Kilde: MVAH `M-8/M-8-1/M-8-1.5/`

### 2.10 Kjøper visste at selger ikke ville betale
Fradrag kan nektes selv med formriktig faktura når kjøper visste at selger ikke ville betale mva, eller når opplegget er illojalt. Typiske tilfeller er nærstående selskaper, salg like før konkurs og kjøpesum som dekker pantegjeld.
- Hovedregelen er likevel fradrag.
- Hjemmel: § 8-1. Rt. 2011 s. 213 (Invex). LA 14.03.2008 (Risør Restaurantdrift). MVAH 8-1.5.
- **[SKJØNN]**. Agenten flagger og konkluderer ikke.

### 2.11 Forskudd og a konto
En salgsfaktura med mva kan ikke utstedes før levering. Unntak gjelder persontransport, servering, abonnement, leie, avgifter og adgang til arrangementer, som kan faktureres inntil ett år fram (bokf.f. § 5-2-6).
- **A konto-fakturaer i bygg og anlegg etter fremdrift er gyldige** (bokf.f. § 8-1-2a, FMVA § 15-9-1 annet ledd) og gir fradrag i fakturaterminen. «A konto» skal ikke gi automatisk flagg.
- Flagg bare forskudd eller depositum for varer eller tjenester som ikke er levert og ikke står i listen i § 5-2-6, for eksempel en maskin.
- **[USIKKER]** hva som er konsekvensen for kjøper. Anbefalt: fradrag først på sluttfakturaen.
- Nettannonsering er ikke «abonnement» (FIN 22.06.2007).
- Hjemmel: mval. § 15-10 tredje ledd. MVAH 15-10.4.

---

## 3. Avskåret fradrag (§§ 8-3 og 8-4)

§ 8-3 og § 8-4 avskjærer fradrag **selv om kjøpet har tilknytning til virksomheten**. Formålet avgjøres ut fra leverandøren, fakturalinjene, deltakerne, stedet og vognkortet, ikke ut fra kontoen.

Unntak:
- § 8-5: kjøp av samme art som klienten selv selger, gir fullt fradrag. Da skal det beregnes uttak når kjøpet brukes til avskåret formål (§§ 3-21 til 3-25).
- § 8-3 annet ledd: varer til bruk om bord i luftfartøy i utenriks fart og fartøy på minst 15 m i utenriks fart (dokumentasjon: FMVA § 8-3-3).

Kilde: https://lovdata.no/dokument/NL/lov/2009-06-19-58 og MVAH `M-8/M-8-3/M-8-3.1/`

### 3.1 § 8-3 første ledd

| Bokstav | Avskåret | Unntak og grenser | Hjemmel og kilde |
|---|---|---|---|
| a | **Servering** (mat og drikke der det er lagt til rette for å spise på stedet). Catering er servering når leverandøren også står for personale, dekking eller rydding. Mva gir aldri fradrag, uansett hvem som spiser, og uansett om det er på tjenestereise | Bare § 8-5. Takeaway (15 %) rammes likevel av d eller e | § 8-3 (1) a. FMVA § 5-2-5. MVAH `M-8/M-8-3/M-8-3.3/` |
| b | **Leie av selskapslokaler i forbindelse med servering** | Møterom på hotell uten servering har 12 % og gir fradrag (§ 5-5 annet ledd). Grensen vurderes konkret | § 8-3 (1) b. Utleiers avgiftsplikt følger av § 3-11 annet ledd (bokstaven er ikke kontrollert) |
| c | **Kunst og antikviteter.** Kunst er originale malerier, grafikk signert og nummerert i høyst 300 eksemplarer, skulptur, tekstilkunst og kunstfotografi signert og nummerert i høyst 30. Antikviteter er varer over 100 år (tolltariff 97.06) | Kjøper som selv omsetter slike varer (§ 8-5). Masseproduserte plakater og trykk er vanlig inventar. Kunstnerens eget salg er unntatt (§ 3-7 fjerde ledd) og har derfor ingen mva. **[USIKKER]** om lovteksten også har unntak for bruk i museum eller galleri (verifikatorene er uenige), men det er uansett ikke relevant for små AS | § 8-3 (1) c. FMVA §§ 1-3-2, 1-3-4. MVAH `M-8/M-8-3/M-8-3.4/` |
| d | **Kost og naturalavlønning** til eier, ledelse, ansatte og pensjonister. Innleide likestilles med ansatte. Eksempler: dagligvarer og pålegg, kaffe, frukt, vann, overtidsmat (KMVA 6195), vannkjøler og kaffeautomat utenfor kantine (KMVA 4853), karriereomstilling (SKNS 45/2021), hjelp med skattemelding for ansatte (KMVA 5462), private strømmetjenester, gavekort, trening og privat del av mobil og bredbånd | Faglige kurs, verneutstyr og lovpålagt bedriftshelsetjeneste gir fradrag etter § 8-1. Skattepliktig fordel på lønnsslippen tyder sterkt på naturalavlønning | § 8-3 (1) d. MVAH `M-8/M-8-3/M-8-3.5/` |
| e | **Representasjon** overfor både kunder og ansatte, inkludert julebord og jubileer. Hele arrangementet rammes: lokale, underholdning, billetter, aktivitet, transport og overnatting knyttet til arrangementet, og drikke | Et rent faglig seminar er ikke representasjon, men maten der rammes av a. Et arrangement med både faglig og sosial del splittes | § 8-3 (1) e. MVAH `M-8/M-8-3/M-8-3.6/` |
| f | **Gaver og reklameutdeling** som ikke er av bagatellmessig verdi, uansett mottaker. Eksempler: vin, blomster, gavekort, julekurv, medaljer og diplomer (U 2/73). Premier i konkurranser regnes som utdeling | **Bagatellmessig = 200 kr eller mindre per enhet** (FMVA § 1-3-6 fra 1.1.2025), vurdert per enhet (KMVA 5382). Brosjyrer, kataloger og prislister gir alltid fradrag. Varer som gis og føres ut av landet gir fradrag (FMVA § 8-3-2). Reklametjenester som annonser og byrå er ikke utdeling. Flere bagatellgjenstander til samme mottaker kan gi uttak. **[USIKKER]** om 200-kronersgrensen regnes inkl. mva (tidligere praksis: omsetningsverdi inkl. mva) | § 8-3 (1) f. FMVA §§ 1-3-6, 8-3-2. MVAH `M-8/M-8-3/M-8-3.7/`. https://lovdata.no/forskrift/2009-12-15-1540/§1-3-6 |
| g | **Fast eiendom til bolig- eller velferdsbehov**: oppføring, vedlikehold, innleie og drift, med løsøre og utstyr (møbler, hvitevarer, TV, treningsapparater). Omfatter personal- og pendlerbolig, hytte, feriebolig, trimrom og idrettsanlegg. Gjelder også bolig som bare brukes i næring (LB 29.05.2017 Hamn Eiendom), våningshus (KMVA 2748) og hjemmekontor i privat bolig (KMVA 3070) | **Bedriftskantine:** oppføring, vedlikehold og løst inventar gir fradrag, men **ikke** driften (strøm, mat, operatørhonorar). Setre, skogshusvære og gjeterhytter i primærnæringene (FMVA § 8-3-1). **Brakkerigg og midlertidig innkvartering som er løsøre**, se 3.3 | § 8-3 (1) g. FMVA § 8-3-1. MVAH `M-8/M-8-3/M-8-3.8/` |

### 3.2 § 8-4 Personkjøretøy
- **Definisjon** (FMVA § 1-3-1 bokstav a–h). Personkjøretøy er
  - personbil og varebil klasse 1
  - moped og MC som ikke hovedsakelig er for varetransport
  - beltebil registrert for mer enn to personer
  - campingbil og registrert campingtilhenger
  - buss under 6 m med inntil 17 seter
  - kjøretøy uten motor for persontransport, for eksempel tråsykkel

  Registreringen i motorvognregisteret (vognkortet) avgjør. ATV er personkjøretøy (KMVA 6841). **El-sykkel og ståhjuling er ikke personkjøretøy** (Skattedirektoratet 12.12.2014). Hver virksomhet kan ha én snøscooter som ikke regnes som personkjøretøy, og ny tidligst etter 24 måneder.
- **Avskåret:** anskaffelse, leie og leasing (også korttidsleie og leiebil på tjenestereise), drift og vedlikehold. Drivstoff, lading, parkering (KMVA 7525), verksted, dekk, dekkhotell, vask og tilbehør regnes som «drift» etter praksis og MVAH. Loven nevner dem ikke uttrykkelig, så begrunn med «drift av personkjøretøy, jf. praksis». Forsikring har ingen mva (§ 3-6).
- **Unntak:**
  - (a) salgsvare
  - (b) yrkesmessig utleie. Det krever reell næringsdrift, ikke utleie til eier eller ansatte (KMVA 3776, 3898, 4694)
  - (c) persontransport mot vederlag, som drosje

  For (b) og (c) skal fradraget tilbakeføres forholdsmessig ved salg eller omdisponering innen **8 år** (§ 9-6, for kjøretøy anskaffet fra 1.7.2024. Eldre kjøretøy har 3 år etter overgangsregler). § 9-6 er endret ved lov 19.06.2026 nr. 48, som ennå ikke er i kraft. Sjekk før bruk.
- **Varebil klasse 2, lastebil, vanlig tilhenger, traktor og el-sykkel** gir fradrag etter § 8-1, også når de frakter ansatte. Ved privat bruk fordeles fradraget (§ 8-2). Sjekk alltid vognkortet. Pickup- og varebilmodeller finnes i begge klasser. Omregistrering til personbil kort etter kjøp gir tilbakeføring (KMVA 4613).
- **Elbilfritaket:** fra 1.1.2026 gjelder fritaket bare for den delen av vederlaget som ikke overstiger 300 000 kr. Det som er over, har 25 % mva, og den mvaen gir heller ikke fradrag. Paragrafnummeret er **[USIKKER]**: verifikatoren angir § 6-8, mens § 9-1 annet ledd bokstav a viser til «§ 6-7 første ledd».
- Hjemmel: mval. § 8-4, § 1-3 annet ledd bokstav a, § 9-6. FMVA § 1-3-1. MVAH `M-8/M-8-4/M-8-4.2/` og `M-8-4.3/`

### 3.3 Grensetilfeller som ofte forekommer
- **Hotellregning:**
  - Rom på tjenestereise: 12 %, kode 13, fradrag.
  - Frokost, halv- og helpensjon, restaurant, bar og minibar: 25 %, **ingen fradrag**. Hotellet skal selv splitte prisen (FMVA §§ 5-5-1 og 5-5-2). Bruk hotellets fordeling og ta fradrag bare for 12 %-linjene. Er prisen ikke splittet, skal spesifikasjon innhentes.
  - Overnatting ved julebord eller privat reise: ingen fradrag.
  - Kilde: MVAH `M-5/M-5-5/M-5-5.2/`
- **Kurs, konferanse og dagpakke:** vederlaget skal splittes (prinsipputtalelse 14.10.2007).
  - Møterom og overnatting: 12 %, fradrag.
  - Mat: ingen fradrag.
  - Ren undervisning er unntatt (§ 3-5) og har ingen mva.
  - Konferanse med meningsutveksling: 25 %, fradrag når den er faglig relevant.
  - **[USIKKER]** når en ekstern arrangør tar én samlet konferanseavgift der maten bare er en biytelse.
- **Brakkerigg og midlertidig innkvartering (løsøre):** gir **fradrag** etter § 8-1 når innkvarteringen er knyttet til et konkret prosjekt, bare brukes i arbeids- eller rotasjonsperioden, avsluttes når prosjektet er ferdig, og ikke disponeres fritt av den ansatte. Kilder: Gulating lagmannsrett 04.09.2024 (A/S Norske Shell) og Skatteetatens uttalelse 25.08.2026, https://www.skatteetaten.no/rettskilder/type/uttalelser/uttalelser/merverdiavgift-og-kostnader-til-brakkerigg-o.l/
  - Leid leilighet eller annen fast eiendom til bolig: avskåret etter g.
  - Mat i riggen: avskåret etter d.
  - Registrert campingvogn: personkjøretøy, ingen fradrag.
- **Hotell kontra bolig:** hotell på tjenestereise gir fradrag. Leilighet over lang tid, pendlerbolig og reiser mellom hjem og fast arbeidssted gir ikke fradrag (Rt. 2011 s. 1260 Halliburton, SKD 2/13, KMVA 6798).
- **Arbeidstøy:** gir fradrag når det brukes av vernehensyn, når bedriften eier og holder det, eller når det er påbudt eller har logo. Klær som den ansatte eier og selv velger, er naturalavlønning og gir ikke fradrag (FIN 26.04.1971, Av 8/87).
- **Mobil og bredbånd:** fradrag for bruken i virksomheten. Privat del er naturalavlønning (§ 8-2, § 8-3 (1) d).
  - KMVA 8378 (15.12.2014): en privatandel på 3,5 % ble avvist, og skattekontorets 25 % ble stadfestet med dissens 3–2.
  - KMVA 5088: 75 % fradrag for selgere som måtte være tilgjengelige hele tiden.
  - TV-pakker gir ikke fradrag. Bredbånd hjemme er hovedsakelig privat.
  - **[SKJØNN]**. Silfer bør fastsette en standard privatandel.
- **Velferd og trening:** treningsmedlemskap er unntatt fra mva (§ 3-8 annet ledd) og har derfor ingen mva. Trimrom og treningsapparater: g. Sosiale arrangementer: e. Ergonomiske stoler og hev-senk-pulter på kontoret er driftsmidler og gir fradrag.
- **Sponsing:** en reell reklamemotytelse fra en registrert mottaker gir fradrag etter § 8-1. Støtte uten motytelse er en gave. Kilde: Skatteklagenemndas vedtak om feilaktig fradragsførte sponsorkostnader. **[SKJØNN]** om motytelsen står i forhold til beløpet.
- **Drosje, tog, buss og fly** på tjenestereise: 12 %, kode 13, fradrag. Drosje til julebord: e. **Ferje:** passasjerdelen 12 % med fradrag. For kjøretøydelen av en personbil er det **[USIKKER]** om den regnes som drift av personkjøretøy. Konservativt valg: kode 0, merket usikker, og ikke presentert som feil hos kunden.

---

## 4. Oppslagstabell: kostnadstype

Kode = SAF-T/Tripletex `vatType.number`. «0» betyr ingen mva-behandling. Kontoene er NS 4102. **Alle rader forutsetter at klienten er registrert.** For klienter som ikke er registrert, gjelder alltid kode 0 (se seksjon 7).

| Kostnadstype | Sats | Fradrag | Kode | Typiske kontoer | Signaler i bilaget | Vanlige feil | Hjemmel |
|---|---|---|---|---|---|---|---|
| Fly innenlands, tjenestereise | 12 % | Ja | 13 | 7140/7130 | SAS, Norwegian, Widerøe, innenlands strekning | Kode 1 (25 %). Pendling eller ektefelle ført med fradrag | § 5-3, § 8-1. MVAH 8-1.4 |
| Fly til eller fra utlandet (inkl. tilknytningsstrekning på samme billett) | 0 % fritatt | – | 0 | 7140 | Utenlandsk destinasjon, ingen mva-linje | Kode 13 på beløp uten mva | § 6-28 (1)–(2), § 6-29 |
| Tog, buss, trikk, flybuss, båt | 12 % | Ja | 13 | 7140 | Vy, SJ, Ruter, Skyss, AtB, Flytoget, Entur | Kode 1. Periodekort for pendling ført med fradrag | § 5-3 |
| Taxi, Uber, Bolt (tjenestereise) | 12 % | Ja | 13 | 7140 | Løyvenummer, taxiselskap | Kode 1. Taxi til julebord ført med fradrag | § 5-3, § 8-3 (1) e |
| Hotell i Norge, rom | 12 % | Ja | 13 | 7140/7130 | Hotellkjede, rom-linje | Hele fakturaen ført med kode 13 | § 5-5 |
| Hotell: frokost, restaurant, bar, minibar | 25 % | **Nei** | 0 | 7140/7350 | 25 %-linjer på hotellfaktura | Ført med kode 1 eller 13 | § 8-3 (1) a. FMVA §§ 5-5-1, 5-5-2 |
| Møterom på hotell uten mat | 12 % | Ja | 13 | 6860/7140 | «Møterom», «konferanselokale» | – | § 5-5 annet ledd |
| Hotell eller overnatting i utlandet | utenlandsk mva | Nei | 0 | 7140 | Valuta, «VAT/MwSt/moms» | Kode 13, eller utenlandsk mva ført på 2710 | § 1-2, § 3-30 |
| Airbnb- og Booking-gebyr | – | **[USIKKER]** | 0/86 etter fakturaen | 7140 | «Service fee», VOEC | – | Følg fakturaen. VOEC-mva gir ikke fradrag |
| Leiebil og bildeling (personbil) | 25 % | **Nei** | 0 | 7140/6440 | Hertz, Avis, Sixt, Hyre, Getaround | Kode 1 som «reise» | § 8-4 |
| Personbil og varebil kl. 1: kjøp, leasing, drivstoff, lading, service, dekk, vask | 25 % | **Nei** | 0 | 1230, 6440, 7000–7099 | Circle K, Uno-X, Tesla SC, Mer, leasingselskap, verksted, registreringsnummer | Kode 1 på lading eller leasing. Varebil antatt å være kl. 2 uten kontroll av vognkort | § 8-4. FMVA § 1-3-1 |
| Varebil kl. 2, lastebil, tilhenger: kjøp og drift | 25 % | Ja (fordel ved privat bruk) | 1 | 1230/1240, 7000–7099 | «Klasse 2», «N1 kl. 2», grønne skilt | – | § 8-1, § 8-2 |
| Parkering, personbil | 25 % | **Nei** | 0 | 7090/7140 | EasyPark, Apcoa, Aimo | Kode 1. Kontrollavgift ført som parkering | § 8-4. KMVA 7525 |
| Parkering, varebil kl. 2 | 25 % | Ja | 1 | 7090 | – | – | § 8-1 |
| Bompenger (AutoPASS) | unntatt | – | 0 | 7090/7140 | Fjellinjen, Ferde, Vegfinans | Mva regnet «baklengs» ut av bompengebeløpet. Ferjebillett på samme faktura ikke skilt ut | § 3-11 første ledd. Skattedirektoratets brev 15.12.2005 |
| Ferje | 12 % | Passasjerdel ja. Personbildel **[USIKKER]** | 13 / 0 | 7140/7090 | Fjord1, Norled, Boreal | Kode 1 | §§ 5-3, 5-4, 8-4 |
| Restaurant, kafé, catering, møtemat, overtidsmat | 25 % / 15 % | **Nei** | 0 | 7350, 5990, 6860, 7140 | Restaurant, Foodora, Wolt, «lunsj», «møtemat» | Kode 1 eller 11 | § 8-3 (1) a og d |
| Dagligvarer, kaffe, frukt og vann til ansatte | 15 % | **Nei** | 0 | 5910, 5990, 6800 | Rema, Kiwi, Oda, kaffe- eller fruktordning | Kode 11 som «kontorrekvisita» | § 8-3 (1) d |
| Representasjon, julebord, sommerfest, jubileum | alle | **Nei** | 0 | 7350/7360, 5990 | «Julebord», eventbyrå, billetter, losje, golf | Lokale eller transport skilt ut og ført med fradrag | § 8-3 (1) e |
| Gaver (kunder og ansatte) over 200 kr per enhet | 25 %/15 % | **Nei** | 0 | 7420/7430, 5900 | Vinmonopolet, Interflora, gavekort, «julegave» | Kontonavn «fradragsberettiget» tolket som mva-fradrag | § 8-3 (1) f. FMVA § 1-3-6 |
| Gaver og profilartikler til og med 200 kr per enhet, samt brosjyrer | 25 % | Ja | 1 | 7320, 7420 | Profilfirma. Sjekk antall × enhetspris | Hele profilfakturaen trukket fra uten sjekk av enhetspris | § 8-3 (1) f |
| Gaver til ansatte | – | **Nei** (konservativt) | 0 | 5990/7430 | «Julegave ansatte» | Kode 1 | § 8-3 (1) d og f. **[USIKKER]** om bagatellgrensen gjelder ved naturalavlønning |
| Blomster til egne lokaler | 25 % | Ja | 1 | 6390 | «Pynt resepsjon» | Ført med 15 % | § 5-1, § 8-1 |
| Blomster som gave | 25 % | Nei (over 200 kr) | 0 | 7420/7430 | «Bursdag», «bårebukett» | Kode 1 | § 8-3 (1) f |
| Kontorrekvisita, IT-utstyr, inventar | 25 % | Ja | 1 | 6540, 6550–6552, 6800, 1250/1280 | Staples, Komplett, Elkjøp | TV, spillkonsoll eller privat utstyr ført med fradrag. Privat leveringsadresse | § 8-1, § 8-2 |
| Kunst og antikviteter | 25 %/unntatt | **Nei** | 0 | 1290, 6540 | Galleri, kunstner, auksjon | Ført som inventar med kode 1 | § 8-3 (1) c |
| Programvare, SaaS, annonser fra utenlandsk selger | 25 % (beregnes av kjøper) | Ja (hvis tilknytning) | **86** (87 uten fradrag) | 6420/6552, 7320, 6790 | Meta, Google Ireland, Microsoft Ireland, Adobe, AWS, «reverse charge», EUR/USD | Kode 0 uten 86. Kode 1 på utenlandsk faktura | § 3-30, § 11-3. MVAH 11-3.2 |
| Samme type tjeneste fra norsk forhandler (Crayon, Atea o.l.) | 25 % | Ja | 1 | 6420/6552 | Norsk org.nr. med MVA | 86 i stedet for 1 | § 8-1 |
| VOEC-mva på kvittering til næringsdrivende | – | **Nei** | 86/87 på grunnlaget | 6420/6552 | «VOEC», «Norwegian VAT 25 %» | Kode 1 | § 11-3, § 15-11. Skatteetatens VOEC-veiledning om B2B |
| Varer fra utlandet (import) | tollverdi + toll og avgifter | Ja (registrert) | Grunnlag 81/83 (med fradrag), 82/84 (uten), 85. Kostnad 20/21/22. Kode 14/15 bare når mva er betalt ved innførsel | 4300, 4060/4070 | Speditør (DHL, UPS, Bring, Schenker), tolldeklarasjon | Speditørens mva-utlegg ført med kode 1 i tillegg til 81 (dobbelt). 81 mangler | § 3-29, § 4-11. bokf.f. § 5-5-2 |
| Telefon og mobil | 25 % | Ja, minus privat andel **[SKJØNN]** | 1 / 0 | 6900, 6907 | Telenor, Telia, Ice | Familieabonnement eller bredbånd hjemme ført med 100 % | §§ 8-2, 8-3 (1) d. KMVA 8378, 5088 |
| Strøm og nettleie, egne næringslokaler | 25 % | Ja | 1 | 6200/6340 | Tibber, Fjordkraft, Elvia. Sjekk anleggsadresse | Strøm til bolig eller boliger for salg ført med fradrag | § 8-1, § 8-3 (1) g |
| Strøm i Nord-Norge uten mva | 0 % | – | 0 | 6340 | Fritak i Finnmark, Troms og Nordland | Behandlet som feil. Ikke alltid feil: felles måler og tariff gir fritak også for næringsdelen | § 6-6 første og annet ledd |
| Vann og avløp, inkl. slamtømming (fra 1.7.2025) | **15 %** | Ja (næringsbygg) | **11** | 6320 | Kommunal gebyrfaktura, VA-selskap | Kode 1 (25 %) av gammel vane. Faktura som krysser 1.7.2025 ikke splittet | § 5-12. FMVA § 5-12-1 |
| Renovasjon og næringsavfall | 25 % | Ja | 1 | 6320 | IVAR, avfallsselskap | – | § 8-1 |
| Feiing og tilsyn, eiendomsskatt, byggesaks-, plan- og oppmålingsgebyr, tinglysing, dokumentavgift, Brønnøysund | utenfor/unntatt | – | 0 | 6390, 7790, 1440/1100 | Kommune, Kartverket | Mva regnet «baklengs» | § 3-9. MVAH `M-3/M-3-9/M-3-9.2/` |
| Husleie uten mva | unntatt | – | 0 | 6300 | – | Fradrag beregnet på beløp uten mva | § 3-11 |
| Husleie med mva (frivillig registrert utleier, lokaler brukt i registrert virksomhet) | 25 % | Ja | 1 | 6300/6310 | Mva-linje, frivillig registrering | Kode 0 (tapt fradrag). Mva fra utleier som ikke er frivillig registrert | §§ 2-3, 3-11 |
| Forsikring | unntatt | – | 0 | 7500, 7040 | If, Gjensidige, Tryg, Fremtind | Mva regnet «baklengs» | § 3-6 a |
| Bank, renter, lån, valuta | unntatt | – | 0 | 7770, 8150 | Bank | Kode 1 på gebyr | § 3-6 b–e |
| Leasing, også finansiell (ikke personbil) | 25 % | Ja | 1 | 6400–6440 | Leasingselskap | Ført som «finans» uten mva | § 3-6 b |
| Transaksjonsgebyr i betalingsløsning (Vipps, Stripe, Nets) | unntatt | – | 0 | 7770 | Nettooppgjør | Kode 86 eller 1 | § 3-6 c |
| Terminalleie og programvare i betalingsløsning | 25 % | Ja | 1 (norsk) / 86 (utenlandsk) | 6420 | «Terminal rental», «subscription» | Ført som finans. **[USIKKER]** hvor grensen går per leverandør | § 3-6 c. MVAH `M-3/M-3-6/M-3-6.9/` |
| Porto og pakker innenlands | 25 % | Ja | 1 | 6940 | Posten, Bring | Frimerker uten spesifisert mva ført med kode 1 | § 3-1, § 6-28 sjette ledd |
| Frakt av varer innenlands | 25 % | Ja | 1 | 6100, 4070 | Schenker, DSV | – | § 8-1 |
| Frakt direkte til eller fra utlandet | 0 % | – | 0 | 6100, 4070 | «Import/eksport» | Kode 1 | § 6-28 |
| Aviser (papir og digital) | 0 % | – | 0 | 6840 | DN, Finansavisen | Mva regnet «baklengs» | § 6-1. FMVA § 6-1-1 |
| Bøker og e-bøker | 0 % | – | 0 | 6840 | Bokhandel | Kode 1. Fagdatabaser (Lovdata Pro, Rettsdata) har ofte 25 %, så følg fakturaen | § 6-4. FMVA § 6-4-3 |
| Tidsskrifter på abonnement | 0 % eller 25 % | Følg fakturaen | 0 / 1 | 6840 | – | – | § 6-3 |
| Kurs (undervisning) | unntatt | – | 0 | 6860 | Kursarrangør uten mva | Mva regnet «baklengs» | § 3-5. MVAH `M-3/M-3-5/M-3-5.2/` |
| Konferanse og seminar (faglig) | 25 % | Ja, men ikke matdelen | 1 / 0 | 6860 | «Konferanseavgift» | Hele pakken ført med kode 1 | § 3-5, § 8-3 (1) a |
| Kontingent | ofte unntatt | Følg fakturaen | 0 / 1 | 7400–7411 | NHO, bransjeforening | Mva regnet «baklengs». Golfklubb ført med fradrag | §§ 3-12, 3-13 |
| Sponsing med reell reklamemotytelse fra registrert mottaker | 25 % | Ja | 1 | 7320 | Sponsoravtale | Gave kalt sponsing. Mva fra lag som ikke er registrert | § 8-1, § 8-3 (1) f |
| Reklame og markedsføring i Norge | 25 % | Ja | 1 | 7320/7300 | Finn, byrå, trykkeri | Utenlandske annonser ført med kode 1 | § 8-1 |
| Arbeidstøy og verneutstyr (påbudt, eid av bedriften eller verneutstyr) | 25 % | Ja | 1 | 5990/6550 | Blåkläder, Snickers, Tess | Hverdagsklær ført som arbeidstøy | § 8-1, § 8-3 (1) d |
| Helsetjenester og bedriftshelsetjeneste | unntatt | – | 0 | 5990 | Avonova, legesenter | Mva regnet «baklengs» | § 3-2 |
| Treningssenter | unntatt | – | 0 | 5990 | SATS, EVO | Mva regnet «baklengs» | § 3-8 annet ledd |
| Advokat, revisor, regnskap, konsulent (drift) | 25 % | Ja | 1 | 6700–6790 | – | Bistand ved aksjesalg, eiendomssalg eller eiers private forhold ført med fradrag | § 8-1, § 8-2 |
| Advokat eller rådgiver ved transaksjoner, emisjon, eiendomssalg eller private forhold | 25 % | **Nei** | 0 | 6700–6790 | «Due diligence», «aksjesalg», «emisjon», «skilsmisse» | Fradrag | § 8-1 |
| Eiendomsmegler og salgsmarkedsføring av bolig eller eiendom | 25 % | **Nei** | 0 | 6790, 7320, 1440 | DNB Eiendom, Privatmegleren | Fradrag | § 3-11, § 8-1 |
| Byggetjenester til egne næringslokaler | 25 % | Ja | 1 | 6600, 1100–1130 | Håndverker, entreprenør | Kapitalvare ikke registrert | §§ 8-1, 9-1 |
| Byggetjenester til bolig for salg eller unntatt utleie | 25 % | **Nei** | 0 | 1400–1499, 6600 | Prosjekt «bolig», seksjoner | Fradrag | §§ 3-11, 8-3 (1) g |
| Innleie av arbeidskraft og underentreprise | 25 % | Ja (registrert bruk) | 1 | 4500, 6790 | Bemanningsbyrå | Faktura fra utenlandsk underleverandør som ikke er registrert, med norsk mva | § 8-1, § 2-1 sjette ledd |
| Bøter, kontrollavgift, purregebyr, inkassosalær kreves fra skyldner, forsinkelsesrenter | utenfor | – | 0 | 7790, 8150 | Politi, SI, inkassobyrå | Ført som parkering med mva | § 1-3 (1) a |
| Varer for videresalg | 25 %/15 % | Ja | 1 / 11 | 4000–4300 | Grossist | Mat med 25 % eller alkohol med 15 % | §§ 5-2, 8-5 |
| Klimakvoter og gull (innenlands, omvendt avgiftsplikt) | 25 % (beregnes av kjøper) | Ja | 91 (92 uten fradrag) | 4xxx | «Omvendt avgiftsplikt – Merverdiavgift ikke beregnet» | Mva fra selger trukket fra | § 11-1 (2)–(3). FMVA § 11-1-1 |

**Kontroll på alle kjøp:** bokført mva skal stemme med mva på fakturaen, og satsen (mva delt på grunnlag) skal stemme med koden: 1 = 25 %, 11 = 15 %, 13 = 12 %, 12 = 11,11 %. Regn aldri ut mva «baklengs» av et bruttobeløp når fakturaen ikke viser mva. EHF-feltene `TaxCategory` (S/Z/E/AE/O/G/K), `Percent` og `TaxSubtotal` er fasiten (bokf.f. § 5-1-1 nr. 6, § 5-1-5).

---

## 5. Tidspunkt og termin (§ 15-9)

- Inngående mva føres i terminen **salgsdokumentet er utstedt** (fakturadato). Levering, mottak, bokføring, forfall og betaling har ingen betydning.
- Et salgsdokument utstedt i de 15 første virkedagene i en måned kan dateres siste dag i forrige måned når leveringen skjedde da (bokf.f. § 5-1-3 tredje ledd).
- Innførsel føres etter ekspedisjonsdatoen på tolldeklarasjonen (Av 6/92).
- Kreditnota føres i terminen den er datert (SKNA-2019-10).
- Etterfakturert mva føres i terminen for den nye fakturaen.
- Glemt eller feilført faktura rettes med **endringsmelding for terminen fakturaen er datert i**, senest 3 år etter leveringsfristen. Den skal ikke føres i en senere termin (sktfvl. § 9-4).
- Omtvistede beløp i tilvirkningskontrakter føres når kravet er avklart eller betalt (FMVA § 15-9-3). Dette gjelder ikke mellom nærstående. **[USIKKER]** om regelen gjelder like direkte på kjøpersiden.
- Hjemmel: mval. § 15-9 første ledd, jf. sktfvl. § 8-3 første ledd. MVAH `M-15/M-15-9/M-15-9.3/`
- Signal: `supplierInvoice.invoiceDate` eller EHF `IssueDate` ligger i en annen termin enn `voucher.date`.

---

## 6. Spesialområder

### 6.1 Forholdsmessig fradrag (§ 8-2)
Hvert bilag plasseres i én av tre grupper:
- bare avgiftspliktig bruk: fullt fradrag
- bare unntatt eller privat bruk: ingen fradrag
- felles bruk: fradrag for antatt andel, vurdert da kjøpet ble gjort

Fordelingsnøkler:
- **Omsetning** (FMVA § 8-2-2): avgiftspliktig omsetning og uttak (inkl. nullsats) delt på all omsetning i forrige år. I nevneren skal også finansinntekter, leie uten frivillig registrering, tilskudd og salg av driftsmidler fra den unntatte delen være med. Øremerkede tilskudd henføres til formålet (FIN 18.12.2020, MVAH 8-2.9). Nøkkelen skal gjenspeile bruken, og ny virksomhet uten fjorårstall bruker antatt bruk.
- **Areal for bygg** (FMVA § 8-2-1): gulvflate. Krever målsatte tegninger og kontrakter.
- **5 %-reglene:**
  - Er avgiftspliktig omsetning normalt 5 % eller mindre, gis ingen fradrag for fellesanskaffelser. Denne regelen gjelder ikke virksomheter som hovedsakelig driver med finans.
  - Er unntatt omsetning normalt 5 % eller mindre, gis fullt fradrag.
  - 5 %-reglene gjelder bare fellesanskaffelser.
- En enkeltstående unntatt transaksjon i en ellers avgiftspliktig virksomhet er ikke delt virksomhet. Da gjelder tilknytningskravet direkte.
- Innenfor samlet virksomhet gjelder § 8-5 (samme art) bare for tjenester etter §§ 3-23 og 3-26 (§ 8-2 første ledd annet punktum).
- **Tripletex:** relative koder (`parentType` satt, `deductionPercentage` under 100). **[USIKKER]** hvordan den delen som ikke gir fradrag, bokføres og rapporteres. Test på et bilag først.
- Hjemmel: mval. § 8-2. FMVA §§ 8-2-1, 8-2-2. Kilde: https://lovdata.no/forskrift/2009-12-15-1540/§8-2-2 og MVAH `M-8/M-8-2/M-8-2.9/`

### 6.2 Uttak fra registrert virksomhet (§§ 3-21 til 3-25)
Når egne varer eller tjenester som har gitt fradrag, tas ut til privat bruk, gaver over 200 kr, representasjon, kost, bolig eller velferd, eller drift av personkjøretøy (§ 3-25), skal det beregnes utgående mva av alminnelig omsetningsverdi (§ 4-9).
- For varer gjelder det bare i den grad det var fradrag ved kjøpet (§ 3-21 annet ledd).
- Kapitalvarer innenfor samlet virksomhet justeres i stedet (§ 3-21 første ledd annet punktum).
- Byggetjenester og tjenester etter § 3-23 gir uttak også ved bruk i en unntatt del (§ 3-22 annet ledd).
- Ikke uttak når tilsvarende salg ville vært unntatt (§ 3-27).
- Koder: 3/31/33 med spesifikasjonen «uttak».
- § 3-19: salg av varer som ble kjøpt uten fradrag, for eksempel personbil, er unntatt (kode 6, ikke 3). Ga kjøpet delvis fradrag, er salget avgiftspliktig, og kapitalvaren justeres (§ 9-2 annet ledd).
- Kilde: https://lovdata.no/lov/2009-06-19-58/§3-21

### 6.3 Byggearbeid i egen regi (§ 3-26) – særlig viktig for eiendomsutviklere
- **Hva omfattes:** et selskap som *bare* bygger for egen regning for salg eller utleie, skal beregne uttaksmva av egenproduserte tjenester som ville vært avgiftspliktige ved salg, når de brukes til oppføring, oppussing eller modernisering. Det omfatter uttrykkelig **byggeledelse, byggeadministrasjon og annen administrasjon**.
  - Også ikke-fysiske arbeider omfattes når de har sammenheng med et egenregiprosjekt med fysiske arbeider: tomtesøk og kjøpsforhandlinger, regulering og byggesøknad, prosjektering, anbudsinnhenting og oppfølging av entreprenører, og prosjekt- og byggeledelse (BFU 09/2009). Det gjelder også prosjekter som ikke blir realisert.
  - Innleid arbeidskraft regnes som egne ansatte (HR-2022-2253-A Lienveien).
  - Bare rent internadministrative oppgaver (intern regnskapsføring) og selve boligsalget faller utenfor.
  - Rene reparasjoner og vedlikehold uten verdiøkning faller utenfor.
  - Ren tomteutvikling der tomten selges før fysiske arbeider starter, faller utenfor (BFU 18/2008).
- **Viktig rettelse:** det er *ikke* riktig at uttaket blir «lite eller null» når fysisk arbeid kjøpes som totalentreprise. Når egne ansatte eller innleide anskaffer og følger opp entreprenører, er det byggeadministrasjon, og den er uttakspliktig.
- **Registrering:** uttaket er grunnlag for registrering etter § 2-1 første ledd, med grense på 50 000 kr over 12 måneder (Skattedirektoratets prinsipputtalelse, **avgitt 30.11.2023**, publisert 04.12.2023, pkt. 2).
- **Grunnlag:** alminnelig omsetningsverdi, inkludert indirekte kostnader, risiko og fortjeneste (HR-2022-2253-A avsnitt 45).
  - Praksis godtar normalt ikke mindre enn timelønn pluss 75 % påslag (KMVA 7068, Borgarting 21.02.2013). Dette er praksis, ikke en fast lovregel.
  - Kjøpte tjenester av *samme type* som selskapet selv utfører, tas med i grunnlaget med samme påslag (prinsipputtalelsen pkt. 3.2.2).
  - Ved innleie er det tjenesten som tas ut, ikke innleieprisen.
- **Tidspunkt og dokumentasjon:** uttaket beregnes fortløpende i terminen arbeidet utføres. Det dokumenteres med timelister per dag og prosjekt, senest innen utgangen av måneden etter (bokf.f. § 8-1-2, jf. § 5-14).
- **Kode:** SAF-T 3 (25 %) med spesifikasjonen «uttak». Tripletex krever `hasWithdrawalVat`.
- **Fradrag etter registrering:** bare for varer, driftsmidler, innleie og underentreprise knyttet til de tjenestetypene selskapet selv utfører.
  - Ingen fradrag for andre typer byggetjenester, for eksempel elektriker, rørlegger eller totalentreprise når selskapet selv bare driver byggeledelse.
  - Ingen fradrag for salgskostnader som megler, markedsføring og juridisk bistand ved salg (§ 3-11).
  - Utfører selskapet alle tjenestetypene selv, er det fullt fradrag og uttak av alt.
- **Tilvalg og endringsarbeid** som utbygger leverer til kjøperen av boligen, gjør ikke at oppføringen blir fremmed regi (BFU 15/13). Hvordan tilvalget selv behandles, står i seksjon 7 punkt 5a.
- **Avgrensning:** selskaper som også bygger for andre, faller inn under § 3-22 annet ledd. Registrering for annen virksomhet som ikke er bygg, stenger ikke for § 3-26. Bygging på kjøpers tomt eller etter bustadoppføringslova er *fremmed regi*, altså salg av byggetjenester med 25 % (§ 3-1, SKNS1-2024-42). Hjemmelsforholdet til tomten er det viktigste momentet.
- **[SKJØNN]** Agenten flagger «mulig registreringsplikt § 3-26 / § 2-1» og ber om fakta: arbeidsoppgaver for ansatte og innleide, fysiske arbeider og tomteforhold. Den beregner ikke uttaket selv og konkluderer ikke.
- Hjemmel: mval. §§ 3-26, 2-1, 4-9, 8-2 første ledd annet punktum. Kilder: MVAH `M-3/M-3-26/M-3-26.2/` og https://www.skatteetaten.no/rettskilder/type/uttalelser/prinsipputtalelser/merverdiavgiftsloven--3-22-andre-ledd-og--3-26---reglenes-anvendelsesomrade/

### 6.4 Kapitalvarer, justering og tilbakeføring (kap. 9)
- **Hva er kapitalvare:**
  - (a) Maskiner, inventar og andre driftsmidler med **inngående mva ≥ 50 000 kr**. Justeres over 5 år, der anskaffelsesåret regnes med. Personkjøretøy som er fritatt for mva, omfattes ikke.
  - (b) Ny-, på- eller ombygging av fast eiendom med **inngående mva ≥ 100 000 kr**. Justeres over 10 år fra fullføring (ferdigattest, midlertidig brukstillatelse eller ibruktakelse).
  - Egne byggetjenester etter §§ 3-22 og 3-26 regnes med i grunnlaget (FMVA § 9-1-1).
  - Grensen gjelder per anskaffelse eller byggetiltak.
  - Vedlikehold, tomt og ren prosjektering er ikke kapitalvarer.
  - **Rettelse:** grensen er mva-beløpet, ikke kostpris eks. mva. Det er feil å si «50 000 kr eks. mva».
- **Oppstilling:** hver kapitalvare skal føres i en egen oppstilling, som oppbevares i 5 år etter at justeringsperioden er slutt (FMVA § 9-1-2).
- **Justering:** 1/5 eller 1/10 per år når fradragsprosenten endres med minst 10 prosentpoeng. Årlig justering føres i 6. termin. Ved overdragelse eller opphør justeres resten samlet (§§ 9-4, 9-5, FMVA § 9-5-1). Koder 1 og 81 med spesifikasjonen «justering».
- **Hendelser som utløser justering:** leietakerskifte med annen avgiftsstatus, overgang til utleie uten frivillig registrering, opphør av registrering, og salg av (a) som ga delvis fradrag (maks 25 % av vederlaget). Ved salg av (b) justeres resten samlet, med mindre kjøper overtar justeringsplikten etter avtale (§§ 9-2, 9-3, FMVA §§ 9-3-1 til 9-3-5). **[USIKKER]** om tomme lokaler, brann og riving ikke utløser justering.
- **Tilbakeføring:** byggetiltak som selges eller omdisponeres *før fullføring*, gir full tilbakeføring (§ 9-7). Personkjøretøy etter § 9-6, se 3.2.
- Kilde: https://lovdata.no/lov/2009-06-19-58/§9-1

### 6.5 Fast eiendom
- Salg og utleie er **unntatt** (§ 3-11 første ledd). Kostnader til den unntatte aktiviteten gir ikke fradrag.
- Avgiftspliktig likevel (§ 3-11 annet ledd):
  - hotell og overnatting (12 %)
  - selskapslokaler med servering
  - parkering i parkeringsvirksomhet
  - reklameplass og oppbevaringsbokser
  - jakt og fiske
  - frivillig registrert utleie
- **Frivillig registrering (§ 2-3):** utleier kan registrere arealer som brukes av leietakere i registrert virksomhet, eller av kommuner eller fylkeskommuner med kompensasjonsrett. Det krever en ubrutt kjede av frivillig registrerte og dokumentasjon: tegninger, kontrakter, en årlig oversikt og bekreftelse fra leietaker (FMVA §§ 2-3-1 og 2-3-2). Registrerte arealer har 25 % mva og gir fradrag. Fellesarealer fordeles. Mva fakturert for areal som ikke kan registreres, skal likevel betales (§ 11-4).
- **Utbygger:** megler, markedsføring og juridisk bistand ved salg gir ikke fradrag. Renter og byggelånsgebyr er unntatt (§ 3-6) og har ingen mva. Tinglysing og dokumentavgift er utenfor loven.
- Kilde: https://lovdata.no/lov/2009-06-19-58/§3-11

### 6.6 Omvendt avgiftsplikt: tjenester fra utlandet (§§ 3-30, 11-3)
- **Fjernleverbare tjenester** (programvare, SaaS, annonser, lisenser, rådgivning levert på avstand) fra en selger utenfor Norge, og som ville vært avgiftspliktige her: kjøper beregner mva selv.
  - Registrert kjøper: ingen beløpsgrense. Kode 86 (25 %) eller 88 (12 %) med fradrag, 87/89 uten fradrag, for eksempel når tjenesten går til representasjon, velferd eller en unntatt del. Tidfestes etter dokumentdato.
- **Ikke omfattet:**
  - Tjenester som utføres fysisk i Norge, for eksempel bygging eller montering. Da skal selger registrere seg og fakturere norsk mva. EØS- og UK-selgere kan registrere seg uten representant (§ 2-1 sjette ledd).
  - Unntatte tjenester som finans og undervisning.
  - Hotell, taxi og konferanse i utlandet (kode 0).
- **Norge har ikke innenlands omvendt avgiftsplikt for byggetjenester.** AE på EHF fra en norsk byggeleverandør skal flagges.
- **Nytt fra 1.7.2026:** ny § 8-9 gir registrerte fradrag for mva på fjernleverbare tjenester som brukes utenfor mva-området, og § 10-5 gir refusjon til næringsdrivende som ikke er registrert. I tillegg er § 3-30 annet og tredje ledd endret (lov 22.12.2025 nr. 121, endret ved lov 23.06.2026 nr. 70). Dette gjelder sjelden små AS. **[USIKKER]** hva de utfyllende forskriftsvilkårene er, og henvisningen til «FMVA § 15-9-4» er ikke verifisert.
- Kilde: MVAH `M-11/M-11-3/M-11-3.2/`

### 6.7 VOEC og utenlandsk mva
VOEC gjelder bare salg til forbrukere. Næringsdrivende skal ikke belastes VOEC-mva. Kjøper beregner selv etter § 11-3 og krever refusjon fra selger. Norsk VOEC-mva gir **ikke** fradrag, og det gir heller ikke utenlandsk mva (moms, MwSt, VAT). Konfidens: sikker for kjernen, ifølge Skatteetatens veiledning om B2B-salg i VOEC-ordningen, https://www.skatteetaten.no/en/business-and-organisation/vat-and-duties/vat/foreign/e-commerce-voec/. Én av verifikatorene fant ikke formuleringen i MVAH. Klassifiser derfor som «må avklares» og ikke som AVVIK, til regelen er bekreftet i MVAH `M-14/M-14-4/M-14-4.2/`.

### 6.8 Omvendt avgiftsplikt: klimakvoter og gull (§ 11-1 annet og tredje ledd)
- Gjelder innenlands salg av klimakvoter og gull (finhet minst 325/1000, uansett form). Gyldige gullmynter og samleobjekter er ikke omfattet (FMVA § 11-1-1).
- Kjøper beregner mva. Registrert kjøper bruker kode 91 med fradrag eller 92 uten. Kjøper som ikke er registrert, beregner over 2 000 kr per termin og bruker 92.
- Selgers faktura skal være merket «Omvendt avgiftsplikt – Merverdiavgift ikke beregnet» (bokf.f. § 5-1-1 nr. 7), og kjøpers org.nr. skal stå på den.
- Norsk mva fakturert på slike salg er uriktig (§ 11-4 første ledd tredje punktum) og gir ikke fradrag.

### 6.9 Innførsel av varer
- Registrerte beregner innførselsmva selv i mva-meldingen. Grunnlaget er **tollverdien** (rubrikk 46, statistisk verdi) pluss toll og avgifter (rubrikk 47), jf. § 4-11 og vareførselsloven §§ 6-2 flg.
- Mva føres i terminen for ekspedisjonsdatoen og avstemmes mot deklarasjonsoversikten i Altinn.
- Speditørens mva-utlegg er ikke inngående mva fra speditøren. Kode 14/15 brukes bare når mva faktisk er betalt ved innførsel.
- Dokumentasjon: innførselsdeklarasjon og grunnlagsdokumenter (bokf.f. § 5-5-2).
- **[USIKKER]** om frakt fram til bestemmelsesstedet inngår i grunnlaget. Bruk tolldeklarasjonen som fasit.
- Kilde: https://www.skatteetaten.no/en/business-and-organisation/vat-and-duties/vat/foreign/import/calculating-and-reporting-vat-on-goods-imports/

### 6.10 Tap på fordringer (§ 4-7)
- Utgående mva kan korrigeres når fordringen er **endelig konstatert tapt** (FMVA § 4-7-1 bokstav a–d):
  - inkasso har vært forgjeves,
  - fordringen er ikke betalt 6 måneder etter forfall, med minst tre purringer og nødvendig oppfølging,
  - konkurs, akkord eller avvikling viser at det ikke blir dekning, eller
  - det ellers er helt klart at fordringen ikke kan innfris.
- Avsetning eller nedskrivning gir ikke korrigering. Det gjør heller ikke ettergivelse av andre grunner eller konvertering til lån. Sikret del (pant, kausjon) er ikke tapt.
- **Nytt fra 1.1.2026:** gjelder fordringen et nærstående selskap (minst 90 % eierskap direkte eller indirekte, eller felles eier), faller retten bort 24 måneder etter at mva ble eller skulle vært fakturert. Fristen forlenges under gjeldsforhandling, konkurs og rekonstruksjon (FMVA § 4-7-2). **Overgangsregel:** 24-månedersgrensen gjelder bare mva beregnet for terminer fra og med 2026 (lov 22.12.2025 nr. 121 del III).
- Koder 1/11/12/13 med spesifikasjonen «tapPåKrav». Kommer det inn betaling senere, skal tilsvarende mva betales. **[USIKKER]** om det skal føres med kode 3.
- Hos **kjøper** påvirker manglende betaling ikke fradraget. Tilbakeføring skjer bare ved heving med kreditnota eller ved senere kontantbetaling over grensen i § 8-8.
- Kilde: https://lovdata.no/lov/2009-06-19-58/§4-7 og https://lovdata.no/forskrift/2009-12-15-1540/§4-7-2

### 6.11 Kreditnota, rabatt og bonus
- Kreditnota fra leverandør reduserer fradraget i terminen den er datert, med **samme kode og sats som originalen**. Kreditnota og original skal vise til hverandre (bokf.f. §§ 5-2-7 og 5-12).
  - Mangler henvisningen, men originalen kan identifiseres entydig (samme leverandør, prosjekt og beløp) og koden er riktig, er det en **formfeil**: konklusjon `ok_formmerknad`, med anbefaling om å be leverandøren rette. Kan originalen ikke identifiseres, eller er det risiko for at kreditnotaen er ført mot feil faktura eller termin: `manglende_dokumentasjon`. Gjelder også klienter som ikke er registrert (bokføringskrav, ikke fradragskrav).
- Når en ny faktura erstatter en gammel, skal den gamle krediteres, ellers blir fradraget dobbelt. Ved heving tilbakeføres fradraget fullt ut.
- Forhåndsavtalte betingede rabatter reduserer grunnlaget når de blir effektive (§ 4-2 annet ledd).
- Bonus via kjede eller mellomledd: kreditnotaen skal vise leverandøren med org.nr. og MVA (Skattedirektoratet 19.02.2020).
- Betaling for en motytelse, for eksempel markedsføringsbidrag, er eget salg med utgående mva. **[SKJØNN]**
- **[USIKKER]** hvordan etterskuddsbonus behandles hos kjøper (MVAH ikke lest).
- Kilde: MVAH `M-15/M-15-9/M-15-9.3/` og https://lovdata.no/forskrift/2004-12-01-1558/§5-2-7

### 6.12 Tilbakegående avgiftsoppgjør (§ 8-6)
- Nyregistrerte kan trekke fra mva på kjøp inntil 3 år før registrering når kjøpene har direkte sammenheng med den registrerte omsetningen. Det gjelder ikke varer som er solgt videre eller brukt opp i unntatt eller privat aktivitet (HR-2017-1851-A).
- Oppgjøret gjelder kjøp før tomånedersterminen registreringen skjedde i. Kjøp i registreringsterminen tas med i første ordinære melding.
- Kravet føres i hovedmeldingen for registreringsterminen, med merknad, og senest 3 år etter registreringen (FMVA § 8-6-1).
- For byggetiltak (b) gjelder ikke 3-årsgrensen bakover.
- Frivillig registrert utleier: omsetningen må ikke ha passert grensen før registreringsterminen, og bygget må være leid ut innen 6 måneder etter fullføring (FMVA § 8-6-2).
- Kilde: MVAH `M-8/M-8-6/M-8-6.2/`

### 6.13 Kostnadsdeling og viderefakturering mellom selskaper
- Ved felles innkjøp (kostnadsdeling) fakturerer selger én av kjøperne. Den som kjøper inn, fordeler kostnaden med kopi av fakturaen og en fordelingsoversikt, og hver deltaker trekker fra sin andel (Skattedirektoratet 16.03.2015, «Rundskriv nr. 40». Datoen for rundskrivet er ikke verifisert).
- Viderefakturering som omsetning skal ha utgående mva (Skattedirektoratet 04.11.2024).
- Det er feil når hele mvaen trekkes fra i det selskapet som kjøper inn, og andelene belastes videre uten mva.
- Konserninterne tjenester (prosjektledelse, management fee) er avgiftspliktig omsetning (§ 3-1), og grunnlaget er minst markedsverdi ved interessefellesskap (§ 4-4). Et konsernselskap som ikke er registrert og fakturerer uten mva, kan ha registreringsplikt. **[SKJØNN]**

---

## 7. Klienter som IKKE er mva-registrert (for eksempel en eiendomsutvikler som bygger for salg)

**Grunnregel:** ingen fradrag, aldri (§ 8-1, bare «registrert avgiftssubjekt»). All mva er kostnad eller en del av anskaffelsen, også på byggekostnader som aktiveres på prosjekt, tomt eller lager (1400–1499, 1130). Kilde: https://lovdata.no/dokument/NL/lov/2009-06-19-58

Agenten skal sjekke dette:

1. **Ingen fradragskoder.** Ingen posteringer skal ha kodene 1, 11, 12, 13, 14, 15, 81, 83, 86, 88 eller 91. Ingen utgående koder (3, 31, 33, 5) skal forekomme på ordinære salg. Kontoene **2700–2749 skal være tomme**. Unntaket er skyldig mva ved omvendt avgiftsplikt med kode 87, 89 eller 92. Merk at 2770/2785 er arbeidsgiveravgift og ikke mva. `amount` skal være lik `amountGross` på kostnadslinjene.
2. **Kontoplanens standardkoder.** Kostnadskontoer med standardkode 1 er en feilkilde ved manuell føring og fakturamottak. Hos testklienten gjaldt det 4500, 6420, 6430, 6705, 6790 og 7790 ved første gjennomgang. Piloten for T4 2026 fikk treff på 6420, 6430, 6705 og 6790 (kontoer med bevegelse i terminen). Listen hentes på nytt fra `account.vatType` hver kjøring. Flagg dette som risiko, men ikke som avvik i seg selv, og rapporter det **én gang per konto** (antall bilag og sum), ikke per bilag.
3. **Omvendt avgiftsplikt:** fjernleverbare tjenester fra utlandet (og klimakvoter eller gull) der samlet grunnlag i terminen **overstiger 2 000 kr eks. mva**.
   - Kode 87 (25 %) eller 89 (12 %), eventuelt 92, uten fradrag.
   - Rapporteres i en **egen kvartalsvis mva-melding for omvendt avgiftsplikt** (januar–mars, april–juni, juli–september, oktober–desember), med frister 10.5, 31.8, 10.11 og 10.2.
   - Kodene 86 og 88 skal aldri forekomme.
   - Under grensen er det ingen plikt.
   - Hjemmel: mval. § 11-3 første ledd annet punktum, § 11-1 annet og tredje ledd. Skatteforvaltningsforskriften §§ 8-3-9 og 8-3-10. Kilder: https://lovdata.no/forskrift/2016-11-23-1360/§8-3-9 og https://lovdata.no/forskrift/2016-11-23-1360/§8-3-10
4. **Innførsel:** mva betalt til Tolletaten eller speditør er ren kostnad. Den skal *ikke* ha mva-kode, og kodene 81–85 er ikke relevante (§ 11-1 første ledd annet punktum).
5. **Registreringsplikt:**
   - Summer løpende 12 måneder med avgiftspliktig omsetning og uttak. Grensen er 50 000 kr (§ 2-1).
   - Typiske kilder til avgiftspliktig omsetning: viderefakturering, management fee eller prosjektledelse for konsernselskaper, parkering i parkeringsvirksomhet, salg av tjenester, tilvalg og endringsarbeid (se 5a), bygging på kjøpers tomt (fremmed regi, § 3-1) og salg av driftsmidler. Salg og utleie av bolig eller tomt er unntatt og teller ikke.
   - Salgsfakturaer med mva fra en klient som ikke er registrert, er et avvik (§ 15-11, § 11-4 annet ledd).

5a. **Tilvalg og endringsarbeid hos boligutbygger [SKJØNN]** (BFU 15/13, avgitt 01.08.2013):
   - Utgangspunkt: tilvalg og endringer som utbygger (bygging i egen regi) leverer til **den samme kjøperen som kjøper boligen**, følger normalt eiendomssalget. De faktureres uten mva, på linje med kjøpesummen, og er unntatt etter § 3-11. Endringer innenfor bustadoppføringslova § 9 endrer normalt ikke dette.
   - Tilvalget er **avgiftspliktig omsetning** (§ 3-1) med registreringsplikt (§ 2-1) når kjøperen av tilvalget ikke er den samme som kjøperen av eiendommen. BFU 15/13 gjaldt tilvalg til andelseiere der eiendommen ble solgt til borettslaget.
   - Skjønnsmomenter som kan trekke mot unntak også ved selveierseksjon: tilvalget er avtalt eller levert etter overtakelse eller hjemmelsoverføring (da er det byggetjeneste på kjøpers eiendom, fremmed regi), det er avtalt direkte mellom kjøper og entreprenør med utbygger som mellomledd, eller det er fakturert som en egen tjeneste uavhengig av kjøpekontrakten.
   - Tilvalg gjør ikke at selve oppføringen blir fremmed regi, og endrer ikke vurderingen etter § 3-26.
   - Signaler i Tripletex: oppgjørsbilag fra megler på 3xxx med egen linje for tilvalg, eller et tilvalgsbeløp som tilsvarer entreprenørens tilvalgsfaktura med 25 % mva.
   - Agenten konkluderer `maa_avklares` og ber om kjøpekontrakten, tilvalgsavtalen (parter og dato), tidspunktet for overtakelse og hjemmelsoverføring og hvem som har fakturert kjøperen. Er det dokumentert at kjøperen er den samme og at tilvalget er avtalt før overtakelse som del av kontrakten, kan agenten foreslå `ok` med sikkerhet `middels`.
   - Hjemmel: mval. §§ 3-1, 3-11, 2-1. Kilde: https://www.skatteetaten.no/rettskilder/type/uttalelser/bfu/utbyggers-avgiftsplikt-ved-levering-av-tilleggsytelser-til-kjopere-av-nye-andelsleiligheter/
6. **§ 3-26 byggearbeid i egen regi (seksjon 6.3):** lønn (5000–5999), innleie av prosjektleder, byggeleder eller håndverkere, og boligprosjekter under arbeid, men ingen registrering, gir **høy risiko for registreringsplikt**. Flagg saken og be om fakta. Selskapet må registreres selv om alt fysisk arbeid kjøpes, dersom egne folk administrerer eller følger opp byggingen. Utleie av fast eiendom (unntatt) endrer ikke dette.
   - Dette er et funn **på klientnivå** og vurderes én gang per termin, ikke per bilag. Byggekostnader kan være ført på prosjektkontoer i 4xxx (for eksempel 4500–4599) og ikke bare på 1400–1499/1130. Klientprofilen skal angi prosjektkontoene.
   - Ord som «byggherre», «innleide» eller «prosjektledelse» i **entreprenørens** fakturatekst viser hva entreprenøren leverer, ikke hva klientens egne folk gjør. De er relevante fakta for vurderingen (hvor mye administrasjon som er kjøpt), men de er ikke bevis for egen byggeledelse. Tekstreffene legges ved klientflagget som dokumentasjon, og bilaget vurderes ellers på vanlig måte.
7. **Selgers mva-kategori (Z) på bygge- og anleggstjenester fra norsk leverandør:** det er uvanlig. Tomt eller eiendom skal ha E/O, og en byggetjeneste skal normalt ha 25 %. Får ingen fradragskonsekvens for klienten, men flagges for vurdering av § 3-26 og for leverandørens feil.
8. **Søker (VAT_APPLICANT):** ingen fradrag før registrering. Bilagene må dokumenteres slik at de kan brukes i et tilbakegående oppgjør (§ 8-6). Kostnader til boliger for salg gir uansett ikke fradrag.
9. **Registrert senere:** vurder § 8-6 (seksjon 6.12). Kjøp til unntatt boligsalg gir aldri fradrag.
10. **Dokumentkrav gjelder fullt ut.** Bokføringsforskriften gjelder uavhengig av mva-status. Purring, inkassovarsel, kontoutskrift eller betalingsbekreftelse som ligger i innboksen som «faktura», er ikke salgsdokument (seksjon 2.4) og skal ikke bokføres. Hos en klient som ikke er registrert gir det ingen mva-feil, men **dobbel kostnad**. Kontrollen skal også omfatte bilag som ikke er bokført. Renter og gebyr fra purring er unntatt eller utenfor loven og føres uten kode (§ 3-6, § 1-3 første ledd bokstav a).
11. **Kjøpers mva-nummer på innkommende faktura.** Selgere skriver ofte «NO<orgnr>MVA» som kjøpers ID selv om kjøperen ikke er registrert. Det er selgers formfeil og har ingen konsekvens for klienten. Det er aldri et tegn på at klienten er registrert. Fasit er `vatSettings` og Brreg.
12. **Selgers «MVA» er ikke bevis for registrering.** Offentlige enheter (for eksempel innkrevingsmyndigheter) kan oppgi en ID som slutter på «MVA» uten å være registrert. Registreringsstatus hentes alltid fra Brreg (seksjon 2.5). Når mva-beløpet på fakturaen er 0, er avviket ufarlig.

---

## 8. Kjente usikkerheter (samlet)

| # | Tema | Hva er usikkert |
|---|---|---|
| U1 | Tripletex `vatType.number` | Om nummeret alltid følger SAF-T, og hva kodene 20/21/22 og spesifikasjonskodene for uttak, justering, tilbakeføring og tap heter. Verifiser per klient. **Pilot T4 2026 (testklienten):** `number` fulgte SAF-T, men `id` er ikke det samme som `number` (id 12 = kode 13, id 111 = kode 12). Bruk alltid `number`. Spesifikasjonskodene (JUST, TAP, TILB, UTTAK) har `parentType` satt med 100 % fradrag, så en kode er bare relativ når `parentType` er satt **og** `deductionPercentage` er under 100 |
| U2 | Relative koder i Tripletex | Hvordan den delen som ikke gir fradrag, bokføres og rapporteres |
| U3 | Ferje med personbil | Om kjøretøydelen regnes som drift av personkjøretøy |
| U4 | Konferansepakke | Samlet pris fra ekstern arrangør der maten er en biytelse |
| U5 | Gave til ansatt | Om 200-kronersgrensen gjelder når gaven samtidig er naturalavlønning. Konservativt: nei |
| U6 | 200-kronersgrensen | Om den regnes inkl. mva (tidligere praksis sier inkl.) |
| U7 | VOEC-mva hos næringsdrivende | Sikker kjerne etter Skatteetatens veiledning, men ikke funnet i MVAH. Behandles som «må avklares» |
| U8 | Airbnb- og Booking-gebyr | Om de er fjernleverbare |
| U9 | Forskuddsfaktura | Konsekvensen for kjøper |
| U10 | Kopikvittering | Om «KOPI» alene gir fradrag |
| U11 | Betaling fra eiers private konto | Om det oppfyller § 8-8 |
| U12 | Kapitalvarer | Om tomme lokaler, brann og riving ikke utløser justering |
| U13 | § 8-9 og § 10-5 | Forskriftsvilkårene er ikke lest |
| U14 | Elbilfritaket | Paragrafnummer (§ 6-7 eller § 6-8) |
| U15 | Tap på fordring | Om senere innbetaling føres med kode 3 |
| U16 | Frakt i importgrunnlaget | Om den inngår |
| U17 | Omtvistede krav (§ 15-9-3) | Om regelen gjelder på kjøpersiden |
| U18 | Etterskuddsbonus hos kjøper | Behandlingen er ikke lest i MVAH |
| U19 | Rundskriv R 40 | Datoen er ikke verifisert |
| U20 | Kunst brukt i museum eller galleri | Om lovteksten har dette unntaket |
| U21 | Betalingsløsninger | Grensen mellom transaksjonsgebyr og teknisk tjeneste per leverandør |
| U22 | sktfvl. § 9-4 | Vedtatt endring er ikke i kraft. Sjekk treårsfristen på nytt |
| U23 | Tilvalg ved salg av selveierseksjon (seksjon 7 punkt 5a) | BFU 15/13 bygger på at kjøper av tilvalg og kjøper av eiendom var ulike. Hvordan tilvalg til samme kjøper behandles når det avtales eller leveres etter overtakelse, eller gjøres opp via megler som egen post, er ikke avklart i MVAH-teksten som er lest. [SKJØNN] |
