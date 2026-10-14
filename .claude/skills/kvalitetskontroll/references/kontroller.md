# Kontroller – kvalitetskontroll av oppdraget

Utkast – kalibreres mot første klient. ID-ene står også i `docs/kontrollkatalog.md`. Hvert funn rapporteres i funn-formatet
(`docs/skill-mal.md`) med status OK, AVVIK eller IKKE AVKLART, og med eier og frist når det er åpent.

Periode: siden forrige gjennomgang (`nextReviewDate` i arbeidsflaten), ellers siste 12 måneder. Svarene skrives inn i Tallys kvalitetsgjennomgang;
attestering gjør oppdragsansvarlig.

| ID | Kontroll | Utslag | Data (MCP) | Grunnlag |
|---|---|---|---|---|
| K1 | Oppdragsavtale signert og dekker tjenestene klienten får | Utkast eller mangler → funn | Tally `contract_status`, `get_client` | regnskapsførerl.: skriftlig oppdragsavtale; GRFS |
| K2 | Kundetiltak gjennomført, risikoklasse satt, neste kontroll ikke forfalt (manglende start eller ugyldig dato er blokkering) | Forfalt eller mangler → funn | Tally `client_compliance` (`get_kyc` bare statusfelt, bare ved behov) | hvitvaskingsl. §§ 9–14, 24 |
| K3 | Fullmakter og tilganger (bank, Altinn, Tripletex) er delegert til riktige personer, ingen fratrådte | Avvik → funn | Tally `access_delegations` | GRFS: dokumenterte fullmakter |
| K4 | Registerkontroll mot Brreg: roller, revisor, mva-registrering, status; terminlengden for mva bekreftet av Skatteetaten | Avvik → funn | Tally `run_quality_checks`, `frister_fra_staten` | GRFS: oppdragsdokumentasjon |
| K5 | Pliktig rapportering levert i tide: mva (M6), a-melding (L4), trekk og arbeidsgiveravgift (L2), årsoppgjørsfrister | Forsinket → funn | Tally `list_deadlines`, `list_altinn_innboks`, `arsoppgjor_frister`; `get_amelding_status` | bokf.l. § 7; a-opplysningsl. § 4; mval. § 15-8 |
| K6 | Avstemminger dokumentert per pliktig rapportering: bank (B1–B3), reskontro (R1/R2), mva (M1/M2), lønn (L1), balanse (S1) – fullført oppgave og dokument | Mangler → funn | Tally `list_tasks`, `list_documents`; `get_bank_reconciliation_periods` | GRFS: dokumentert avstemming; bokf.l. § 11 |
| K7 | Ajourhold: bilagsmottaket, ubokførte bilag, perioder låst (D4, D6) | Etterslep → funn | `get_voucher_inbox_count`, `get_accounting_period_status` | bokf.l. § 7 |
| K8 | Kundeinstruksen er oppdatert siste 12 måneder, vesentlighetsgrensen er satt, kjente avvik er fortsatt gyldige | Eldre eller mangler → funn | Tally `hent_instrukser` | GRFS: rutiner og oppdragsdokumentasjon |
| K9 | Åpne avvik og oppfølginger fra forrige gjennomgang er lukket, eller har eier og frist | Åpent uten eier → funn | Tally `list_avvik`, `get_quality_workspace` | GRFS: oppfølging av avvik |
| K10 | Oppdragsansvarlig og team er registrert, og har kapasitet og kompetanse til tjenestene | Mangler → funn | Tally `get_client`, `team_skills` | regnskapsførerl.: oppdragsansvarlig |

## Terskler

- Én forsinket rapportering i perioden er et funn, ikke en blokkering. Gjentatte forsinkelser eller forfalte kundetiltak gir rød konklusjon.
- Statusen kommer fra verktøyene; Claude vurderer ikke kundetiltakene selv og endrer dem aldri.
