# Tripletex-endepunktindeks

Søkbar indeks over Tripletex API v2: alle 802 kall gruppert per fagområde, rundt 450 oppgaveoppskrifter med påkrevde parametere, `fields=` og
fallgruver, og en egen oversikt over byråets avstemmingsmodul (interne kall). Brukes før noen sier at Tripletex «ikke har» et kall, og når en
skill trenger et kall MCP-en ikke dekker.

Bare lokale filer, ingen kall mot Tripletex, ingen token.

```bash
node tripletex-api/finn.js <ord>               # norsk eller engelsk, æøå valgfritt; prøv 2–3 synonymer
node tripletex-api/finn.js --sti /ledger/voucher POST   # alle parametere, enum-verdier og body-felt fra spec
```

| Fil | Innhold |
|---|---|
| `docs/api-v2-oppgaver.md` | Oppgaveoppskrifter per område, fallgruver, kart over hva Tripletex-MCP-en dekker, og «ikke i API v2» |
| `docs/api-v2-oversikt.md` | Alle kall gruppert per tag med beskrivelse og nøkkelord |
| `docs/avstemmingsmodul.md` | Avstemmingsmodulen (lønn, A07, mva, balanse): interne kall, referenceId-er og arbeidsflyt. Interne kall kan endres uten varsel – test lesende først |
| `docs/api-v2-indeks.json` | Maskinlesbar indeks som `finn.js` bruker |
| `docs/openapi.json` | Offentlig spec (2.75.11), brukes av `--sti` |
| `docs/indeks/*.json` | Kildene: nøkkelord, oppgaver og fallgruver per område. Rett her og bygg på nytt |

## Oppdatere

```bash
node tripletex-api/build-index.js              # bygger api-v2-indeks.json, -oversikt.md og -oppgaver.md fra docs/indeks/
node tripletex-api/build-index.js --hent-spec  # henter openapi.json på nytt og viser nye og fjernede kall
```

Nye kall i spec må få oppgave og nøkkelord i `docs/indeks/`. Ingen kundenavn eller ekte id-er i kildene; bruk `<kunde-id>`, «en klient».

## Rekkefølge når et kall mangler

1. Sjekk Tripletex-MCP-ens verktøy (ToolSearch) – den dekker mye som ikke står i v2 (a-melding, skattekort, Brreg, rapporter).
2. `node tripletex-api/finn.js <ord>` med synonymer, og `--sti` for parametere.
3. Test med et lesende kall. 403 betyr manglende tilgang eller modul for klienten, ikke at kallet mangler. 404 på stien betyr feil sti.
4. Står det «IKKE I API v2», si det og bruk MCP-en eller Tripletex-UI.
5. Først da kan du si at noe ikke er tilgjengelig – og si «ikke funnet», ikke «finnes ikke».

Kilde: `C:\Users\Sjur\Tripletex API` (Sjurs CLI). Den interne specen (`openapi-internal.json`, ca. 1900 stier) ligger bare der.
