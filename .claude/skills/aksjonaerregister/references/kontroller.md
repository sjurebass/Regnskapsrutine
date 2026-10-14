# Kontroller – aksjonærregisteroppgaven (RF-1086)

Utkast – kalibreres mot første klient. ID-ene står også i `docs/kontrollkatalog.md`. Hvert funn rapporteres i funn-formatet
(`docs/skill-mal.md`) med status OK, AVVIK, FORKLART, KJENT eller IKKE AVKLART. Personlige aksjonærer omtales som «aksjonær n (rolle)».

Kildene er fjorårets RF-1086 (Tally-arkivet, lest lokalt), hovedboken, protokoller og aksjeeierbok (`KONTRAKT` i Tally), Brreg og Altinn-innboksen.
Tripletex har ingen aksjonærdata i API eller MCP.

| ID | Kontroll | Utslag | Data (MCP) | Grunnlag |
|---|---|---|---|---|
| AR1 | Selskapsform AS eller ASA, og selskapet er aktivt | Annen form eller slettet → oppgaven er ikke aktuell (etter ja) | Tally `lookup_brreg`, `lookup_company_in_brreg` | sktfvl. § 7-7 |
| AR2 | 2000 UB = antall aksjer × pålydende (fjorårets oppgave ± kapitalendring i året) | Avvik → AVVIK | `get_balance_sheet`, fjorårets oppgave | asl. § 3-1 |
| AR3 | Kapitalendringer (bevegelse på 2000, 2020, 2030) har protokoll og melding til Brreg | Mangler dokument → spørsmål til kunden | `search_ledger_postings`, Tally `list_documents` | asl. kap. 10–12 |
| AR4 | Utbytte: bevegelse på 2800/2050 = vedtatt i protokollen = Σ per aksjonær; skyldig på 2920; utbetalingsdato | Avvik → AVVIK | `search_ledger_postings`, protokoll | asl. §§ 8-1, 8-2; sktl. § 10-11 |
| AR5 | Eierskifter og antall aksjer per aksjonær mot aksjeeierboken og fjorårets oppgave | Endring uten dokument → spørsmål til kunden | fjorårets oppgave, Tally `list_documents` | asl. §§ 4-5, 4-7 |
| E1 | Aksjonærlån per 31.12 (debetsaldo på 13xx/15xx/29xx) rapporteres; låneavtale og renter | Debet uten avtale → AVVIK | `search_ledger_postings` | sktl. § 10-11 (4); asl. § 8-7 |
| AR6 | Egne aksjer (2030): antall og bevegelse i året | Opplysning | `search_ledger_postings` | asl. § 9-2 |
| AR7 | Roller i Brreg (styreleder, daglig leder) er de som signerer; endringer er meldt | Avvik → spørsmål | Tally `lookup_brreg` | – |
| AR8 | Levert innen 31.1 med kvittering i Altinn; feilliste behandlet; fase `rf1086` oppdatert i Tally | Mangler → frist og ansvarlig | Tally `list_altinn_innboks`, `les_altinn_melding`, `get_arsoppgjor_status` | sktfvl. § 7-7; tvangsmulkt sktfvl. § 14-1 |

## Terskler

- Aksjekapital og antall aksjer skal stemme eksakt. Utbytte og lån: avvik fra 1 kr er AVVIK.
- Endring uten dokumentasjon er IKKE AVKLART til kunden har svart; den blir aldri gjettet.
- Kjent avvik i kundeinstruksen med samme beløp: KJENT.
