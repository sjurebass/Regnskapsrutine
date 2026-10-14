// Klientene nøkkelen har tilgang til – ett kall per nøkkel, ingen kall per klient.
//
//   npm run -s klienter                      tabell: navn, org.nr., id
//   npm run -s klienter -- --sok <tekst>     bare klienter der navn, org.nr. eller id inneholder teksten
//   npm run -s klienter -- --json            [{id, navn, orgnr, konto}]
//
// Brukes som steg 0 før en klient angis med --client i de andre kommandoene. Kun lesing.

import { clients } from './tripletex.js';
import { accounts } from './auth.js';
import { argumenter } from './valg.js';

const norm = (s) => String(s ?? '').toLowerCase().replace(/\s/g, '');

try {
  const a = argumenter(process.argv.slice(2));
  const sok = typeof a.sok === 'string' ? norm(a.sok) : '';
  const alle = await clients();
  const treff = alle
    .filter((c) => !sok || norm(c.name).includes(sok) || norm(c.organizationNumber) === sok || String(c.id) === sok)
    .map((c) => ({ id: c.id, navn: c.name, orgnr: c.organizationNumber ?? '', konto: c.account }));
  if (a.json) {
    console.log(JSON.stringify(treff, null, 1));
  } else if (!treff.length) {
    console.log(sok ? `Ingen klient passer på «${a.sok}» (${alle.length} tilgjengelige).` : 'Nøkkelen har ikke tilgang til noen klienter.');
    process.exitCode = 1;
  } else {
    const flere = accounts().length > 1;
    const b = Math.min(48, Math.max(...treff.map((t) => t.navn.length)));
    for (const t of treff) console.log(`${t.navn.padEnd(b)}  ${String(t.orgnr || '-').padEnd(9)}  id ${t.id}${flere ? `  (via ${t.konto})` : ''}`);
    console.log(`\n${treff.length}${sok ? ` av ${alle.length}` : ''} klienter.`);
  }
} catch (err) {
  console.error(`Feil: ${err.message.split('\n')[0]}`);
  process.exitCode = 1;
}
