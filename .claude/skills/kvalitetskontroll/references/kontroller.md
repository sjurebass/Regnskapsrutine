# Kontroller – kvalitetskontroll av oppdraget

Utkast – kalibreres mot første klient. ID-ene står også i `docs/kontrollkatalog.md`. Hvert funn rapporteres i funn-formatet
(`docs/skill-mal.md`) med status OK, AVVIK eller IKKE AVKLART, og med eier og frist når det er åpent.

Periode: siden forrige gjennomgang (`nextReviewDate` i arbeidsflaten), ellers siste 12 måneder. Svarene skrives inn i Tallys kvalitetsgjennomgang;
attestering gjør oppdragsansvarlig. Tripletex leses med `npm run -s <kommando> -- …` (se steg 3 i SKILL.md).

| ID | Kontroll | Utslag | Data (API) | Grunnlag |
|---|---|---|---|---|
| K1 | Oppdragsavtale signert og dekker tjenestene klienten får | Utkast eller mangler → funn | Tally `contract_status`, `get_client` | regnskapsførerl.: skriftlig oppdragsavtale; GRFS |
| K2 | Kundetiltak gjennomført, risikoklasse satt, neste kontroll ikke forfalt (manglende start eller ugyldig dato er blokkering) | Forfalt eller mangler → funn | Tally `client_compliance` (`get_kyc` bare statusfelt, bare ved behov) | hvitvaskingsl. §§ 9–14, 24 |
| K3 | Fullmakter og tilganger (bank, Altinn, Tripletex) er delegert til riktige personer, ingen fratrådte | Avvik → funn | Tally `access_delegations` | GRFS: dokumenterte fullmakter |
| K4 | Registerkontroll mot Brreg: roller, revisor, mva-registrering, status; terminlengden for mva bekreftet av Skatteetaten | Avvik → funn | Tally `run_quality_checks`, `frister_fra_staten`; `/ledger/vatSettings` (mva-registrering i Tripletex) | GRFS: oppdragsdokumentasjon |
| K5 | Pliktig rapportering levert i tide: mva (M6), a-melding (L4), trekk og arbeidsgiveravgift (L2), årsoppgjørsfrister | Forsinket → funn | Tally `list_deadlines`, `list_altinn_innboks`, `arsoppgjor_frister`; `amelding oversikt --ar`, `amelding status --maned`, `status --aar` (mva) | bokf.l. § 7; a-opplysningsl. § 4; mval. § 15-8 |
| K6 | Avstemminger dokumentert per pliktig rapportering: bank (B1–B3), reskontro (R1/R2), mva (M1/M2), lønn (L1), balanse (S1) – fullført oppgave og dokument | Mangler → funn | Tally `list_tasks`, `list_documents`; `status --aar` (bank lukket per måned) | GRFS: dokumentert avstemming; bokf.l. § 11 |
| K7 | Ajourhold: bilagsmottaket, ubokførte bilag, perioder låst (D4, D6) | Etterslep → funn | `status --aar` (bilagsmottak, ikke bokførte bilag, perioder lukket) | bokf.l. § 7 |
| K8 | Kundeinstruksen er oppdatert siste 12 måneder, vesentlighetsgrensen er satt, kjente avvik er fortsatt gyldige | Eldre eller mangler → funn | Tally `hent_instrukser` | GRFS: rutiner og oppdragsdokumentasjon |
| K9 | Åpne avvik og oppfølginger fra forrige gjennomgang er lukket, eller har eier og frist | Åpent uten eier → funn | Tally `list_avvik`, `get_quality_workspace` | GRFS: oppfølging av avvik |
| K10 | Oppdragsansvarlig og team er registrert, og har kapasitet og kompetanse til tjenestene | Mangler → funn | Tally `get_client`, `team_skills` | regnskapsførerl.: oppdragsansvarlig |

## Terskler

- Én forsinket rapportering i perioden er et funn, ikke en blokkering. Gjentatte forsinkelser eller forfalte kundetiltak gir rød konklusjon.
- Statusen kommer fra verktøyene; Claude vurderer ikke kundetiltakene selv og endrer dem aldri.
- K-funn og stikkprøvefunn får grad etter `docs/stikkprover.md`: merknad, avvik eller vesentlig avvik. K2 og K5 er nøkkelkontroller.

## Stikkprøver (U-kontrollene)

Metoden, tabellen for utvalgsstørrelse, arbeidspapiret og bevisstandarden står i `docs/stikkprover.md`. Her står hva som testes i oppdragskontrollen.

| ID | Utvalg | Testtrinn per utvalgsenhet | Data (API) | Bestått når |
|---|---|---|---|---|
| U7 | Systematisk: 2–4 måneder (bank, reskontro, balanse, bilagskontroll) og 2–3 terminer (mva, trekk og AGA) etter risiko | Oppgaven fullført innen fristen · dokument i Tally eller modulen · saldo i dokumentet = hovedbok | Tally `list_tasks`, `list_documents`; `modul -- perioder`, `modul -- linjer`; `/balanceSheet` | Alle tre trinn; differanse < 1 kr |
| U2 | Bilag: systematisk over perioden, antall etter tabellen (per bilag), pluss målrettet over V | Vedlegg eller EHF finnes og er salgs- eller kjøpsdokument | `utvalg`, `dokument --bilag` | Gyldig dokument; formfeil → merknad |
| U3 | Samme | Konto, mva-kode og beløp = dokumentet; mva regnet om | `/ledger/voucher/{id}` med `fields=postings(account(number),vatType(number),amountGross)` | Avvik < 1 kr |
| U4 | Samme, særlig «siste 3 dager» | Fakturadato og leveringsperiode i samme periode som bilagsdatoen | `utvalg.json` (dato), dokumentet | Samme måned; annen mva-termin og ≥ V → vesentlig |
| U5 | Leverandørfakturaer i utvalget | Godkjent med dato før betaling (bare når kundeinstruksen har godkjenningsflyt) | `/supplierInvoice/{id}` med `fields=approvalListElements(status,actionDate),payments(date)` | Godkjent før betalingsdato |
| U6 | Samme | Matchet mot bank, eller åpen post i reskontro på periodeslutt | `/ledger/posting` (`matched`), `/ledger/posting/openPost` | Ett av de to |
| U10 | Målrettet: motparter med samme org.nr. som selskap der roller i Brreg eller aksjonærer har eierskap eller verv | Avtale eller vedtak finnes, markedsmessig pris, riktig konto (ikke drift for private kjøp) | Tally `lookup_brreg`, `run_quality_checks`; `/ledger/posting` med `supplier(organizationNumber)` | Dokumentert; lån til aksjonær følger asl. § 8-7 |
| U9 | Kontroller med avvik i forrige gjennomgang | Samme testtrinn, nytt utvalg, ny seed, ett trinn større | forrige arbeidspapir, Tally `list_avvik` | Ingen avvik |
| U1, U8 | Alle stikkprøvene | Arbeidspapir med populasjon, metode, seed og antall; avvik klassifisert og aggregert; vesentlige avvik meldt | arbeidspapiret | Komplett og meldt |

- Bilagstekster brukes bare av agenten og vises ikke. Personer (aksjonærer, roller) omtales med rolle; ansatte som attestanter er «attestant 1/2».
- Utvalgsenheter som ikke kan testes (dokument mangler i Tripletex), er avvik under U2, ikke «ikke testet».
- Svaret i Tally per spørsmål får én setning per stikkprøve: «U2–U6: 30 bilag (systematisk, seed 20261020), 29 bestått, 1 merknad.»
