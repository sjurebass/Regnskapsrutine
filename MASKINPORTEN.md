# Maskinporten: kan A07 og offentlige brev hentes automatisk?

Undersøkt 17.09.2026. Kort svar: **ja, teknisk mulig – men det er et
integrasjonsprosjekt, ikke en innstilling som skrus på.** Og for A07 spesifikt er
API-et Skatteetaten bygger ennå ikke ferdig.

---

## 1. Hva Maskinporten er, og hvorfor det ikke holder alene

Maskinporten er Digdirs løsning for maskin-til-maskin-autentisering mot offentlige
API-er. Den gir et token som sier «dette systemet, fra denne virksomheten, har
dette scopet».

Det den *ikke* gjør alene, er å si at du har lov til å hente data om **klientene
dine**. Til det trengs Altinn-autorisasjon oppå, og det er der jobben ligger for
et regnskapskontor.

## 2. Klientdelegering – biten som gjør dette mulig for regnskapsfører

Den relevante mekanismen heter **systembruker med klientdelegering**
([Digdir](https://docs.digdir.no/docs/Maskinporten/maskinporten_func_systembruker.html),
[Altinn](https://docs.altinn.studio/nb/authorization/guides/system-vendor/system-user/userscenarios/)).

Poenget er at én systembruker kan betjene mange klientforhold. Klientadministrator
hos regnskapsføreren knytter kunden til systembrukeren, og tilgangen videredelegeres
automatisk – bygget på regnskapsfører- (REGN) og revisorrollen (REVI) i
Enhetsregisteret. Du slipper altså å sette opp én integrasjon per kunde.

Teknisk ber systemet Maskinporten om et systembrukertoken med
`urn:altinn:systemuser` og kundens organisasjonsnummer i ISO6523-format
(`0192:<orgnr>`). API-tilbyderen validerer så mot Altinn Autorisasjon 3.0 før data
gis ut.

Alternativet, vanlig API-delegering, gir hele scopet til leverandørens
organisasjonsnummer. Det er for vidt for dette formålet – systembruker er den
riktige veien.

## 3. Hva som konkret må gjøres

Skatteetaten lister seks faser for systemleverandører
([oppkobling](https://www.skatteetaten.no/samarbeidspartnere/reetablering-altinn/systemleverandor/oppkobling/)):

| Steg | Hva | Hvem |
|---|---|---|
| 1 | Maskinporten-integrasjon i Samarbeidsportalen, avtale med Digdir | Silfer |
| 2 | Be om nødvendige Altinn-scopes via registreringsskjema | Silfer |
| 3 | Registrere systemet i Altinns systemregister, koblet til client_id | Silfer |
| 4 | Søke Skatteetaten om tilgang til de aktuelle tjenestene | Silfer |
| 5 | Sette opp systembruker med tilgangspakker – «tar noe tid» | Silfer + kundene |
| 6 | Teste mot testmiljø, så produksjon | Silfer |

Kundene må godkjenne systembrukeren i Altinn. Det er en dialog de klikker seg
gjennom, uten avtale med Digdir – men det er ti kunder som må gjøre det.

**Tilgangspakkene** som gjelder for a-meldingen og avstemmingsinformasjon
([Skatteetaten](https://www.skatteetaten.no/bedrift-og-organisasjon/arbeidsgiver/a-meldingen/siste-fra-a-ordningen/nye-tilgangspakker-for-a-meldingen/)):
A-ordningen, Regnskapsfører lønn, Regnskapsfører med signeringsrettighet,
Regnskapsfører uten signeringsrettighet, Ansvarlig revisor, Revisormedarbeider.

## 4. A07: API-et er ikke ferdig

Skatteetaten bygger **avstemmingsrapport a-melding API** (tidligere A06/A07). Per i
dag finner jeg bare en tidlig OpenAPI-spesifikasjon (versjon 0.0.1) på
[SwaggerHub](https://app.swaggerhub.com/apis/skatteetaten/avstemmingsrapport-amelding-api/0.0.1)
og en dokumentasjonsside på
[GitHub](https://skatteetaten.github.io/api-dokumentasjon/api/avstemmingsrapport-amelding),
med forbehold om at «her kan det fortsatt komme noen endringer»
([nyhetssak](https://www.skatteetaten.no/samarbeidspartnere/sluttbrukersystemer/sbs-nyheter/dokumentasjon-avstemmingsrapport-a-melding-api/)).

Verken endepunkt, scope-navn eller produksjonsstatus er publisert der jeg finner
dem. **Dette må bekreftes direkte med Skatteetaten før noe bygges.**

## 5. Andre brev fra det offentlige: Dialogporten

For brev og meldinger til virksomhetens Altinn-innboks er svaret
[Dialogporten](https://docs.altinn.studio/nb/dialogporten/) – Altinn 3s
erstatning for de gamle lese-API-ene. Meldinger sendt via Altinn 3 Correspondence
finnes gjennom Dialogporten, som tilbyr både OpenAPI og GraphQL, med søk etter
dialoger og oppslag på referanse.

Dialogporten er i drift, men datamigreringen fra Altinn 2 pågår fortsatt. Dette er
den modneste delen av det du spør om.

## 6. Frister som presser

Fra Skatteetatens oversikt over tilgangspakker:

| Dato | Hva |
|---|---|
| 19.06.2026 | Altinn-rolledelegering opphørte – bare tilgangspakker kan delegeres (passert) |
| 31.12.2026 | Tidligere delegerte Altinn-roller utløper |
| Januar 2027 | Riktige tilgangspakker blir obligatorisk for fortsatt tilgang |

Dette gjelder **uavhengig av om du bygger noen integrasjon**. Tilgangene dere har i
dag på klientene, bygget på gamle Altinn-roller, slutter å virke ved årsskiftet om
tilgangspakkene ikke er på plass. Det er tre og en halv måned unna, og er en jobb
som må gjøres uansett.

## 7. Anbefaling

**Gjør nå, uavhengig av alt annet:** sørg for at tilgangspakkene er på plass på alle
ti klientene før 31.12.2026. Dette er ikke valgfritt.

**Ikke bygg Maskinporten-integrasjon for A07 ennå.** Tre grunner:

1. API-et er ikke ferdig. Å bygge mot en 0.0.1-spesifikasjon som «fortsatt kan
   endres» betyr å bygge to ganger.
2. Kost/nytte. Seks faser med Digdir-avtale, systemregistrering og godkjenning hos
   ti kunder – mot å laste ned én XML per klient per termin. Det er 60 nedlastinger
   i året, kanskje to timer totalt.
3. Løpet er laget for systemleverandører som selger programvare til mange
   regnskapskontorer, ikke for ett kontor med ti klienter.

**Hva Tripletex allerede gir – testet 17.09.2026:** Tripletex har egen
a-meldingsintegrasjon mot Altinn, og MCP-connectoren eksponerer
`get_amelding_status`. Den returnerer `accrued` og `notPaid` for forskuddstrekk,
arbeidsgiveravgift, finansskatt og pliktig innskudd per termin – altså det
Skatteetaten har registrert. På Livity august 2026 ga den 151 064 i påløpt trekk
og 66 503 i påløpt AGA, med 0 ubetalt.

Det dekker nøkkeltallene i lønnsavstemmingen, og er faktisk en **bedre kilde** enn
å utlede skyldig trekk og AGA fra kontobevegelser, som månedskontrollens L2 gjør
i dag.

Men det stopper der. Jeg testet om connectoren kan gi **ytelser per
inntektsmottaker**, som er grunnlaget for «Per ansatt»-arket:

| Verktøy | Gir | Duger til A07-detaljen? |
|---|---|---|
| `get_amelding_status` | totaler per termin | nei, ingen personfordeling |
| `search_employees` | ansattliste med id og navn | nei, ingen beløp |
| `search_my_payslips` | kun innlogget brukers lønnsslipper | nei |
| `search_wage_type_registrations` | timelistetillegg, ikke a-meldingsdata | nei |

**Konklusjon: A07-filen trengs fortsatt** til per-ansatt-kontrollen. Connectoren
erstatter den ikke.

Verdt å merke seg: REST-API-et har `/salary/payslip` med filter på `employeeId`,
som MCP-connectoren ikke eksponerer. Det gir lønnsslipper per ansatt fra
regnskapssiden. Det er ett konkret argument for å beholde REST-klienten ved siden
av connectoren – og det er allerede implementert i `tools/hent.py`.

**Dialogporten er verdt en nærmere kikk uansett**, uavhengig av A07. Å få brev fra
Skatteetaten og Brønnøysund inn i en felles oversikt over ti klienter er en reell
gevinst, og den delen er faktisk i produksjon.

---

## Kilder

- [Systembruker for virksomheter – Digdir](https://docs.digdir.no/docs/Maskinporten/maskinporten_func_systembruker.html)
- [Systembruker, brukerscenarier – Altinn](https://docs.altinn.studio/nb/authorization/guides/system-vendor/system-user/userscenarios/)
- [Systembruker – Altinn Studio](https://docs.altinn.studio/nb/authorization/getting-started/systemuser/)
- [Nye tilgangspakker for a-meldingen – Skatteetaten](https://www.skatteetaten.no/bedrift-og-organisasjon/arbeidsgiver/a-meldingen/siste-fra-a-ordningen/nye-tilgangspakker-for-a-meldingen/)
- [Dokumentasjon avstemmingsrapport a-melding API – Skatteetaten](https://www.skatteetaten.no/samarbeidspartnere/sluttbrukersystemer/sbs-nyheter/dokumentasjon-avstemmingsrapport-a-melding-api/)
- [Oppkobling for systemleverandører – Skatteetaten](https://www.skatteetaten.no/samarbeidspartnere/reetablering-altinn/systemleverandor/oppkobling/)
- [Avstemmingsinformasjon – Skatteetaten](https://www.skatteetaten.no/skjema/avstemmingsinformasjon/)
- [Dialogporten – Altinn](https://docs.altinn.studio/nb/dialogporten/)
- [Slik bruker du Maskinporten som API-tilbyder – Digdir](https://docs.digdir.no/docs/Maskinporten/maskinporten_guide_apitilbyder)
