// Mva for én klient og termin (kontroll før innsending) og mva-status på tvers av klienter – KUN LESING.
//
//   npm run -s mva -- "<klient>" --aar 2026 --termin 4 [--gjenbruk] [--json] [--aarlig]
//   npm run -s mva -- status (--client "klient" [--client …] | --alle) --aar 2026 --termin 4 [--json]   (se src/mva/status.js)
//
// Kontrollen leser Tripletex én gang til arbeidsmappa (%TEMP%\rr\mva-<år>-T<n>\<kunde-id>\, eller MVA_ARBEIDSMAPPE),
// kjører de deterministiske kontrollene og skriver:
//   funn.json            alle funn (felles format, se src/mva/felles.js)
//   overlevering.json    bilagsutvalget (unntakslista, maks 10 bilag) til bilagsvurderingen
//   dokumentasjon.json   plan for vedlegg og kommentarer i avstemmingsmodulen
//   beslutning-1.md      beslutningslista til regnskapsføreren
//   state.json           hvor langt flyten har kommet
// Ligger vurdering.json (bilagsvurderingen) i mappa, flettes den inn.
// --gjenbruk bruker datasettene fra forrige kjøring (ingen nye kall mot Tripletex).
//
// Skriver aldri til Tripletex (men oppdaterer den felles leverandørindeksen med fakta fra Enhetsregisteret).
// Modusen UREGISTRERT (klient uten mva-registrering) er implementert. For REGISTRERT kjøres foreløpig bare de
// felles kontrollene (reskontro, bank, bilag, skattekonto).

import { connect, bind } from './tripletex.js';
import { mvaStatus } from './mva/status.js';
import { argumenter, klientutvalg, perKlient, kortFeil } from './valg.js';
import { arbeidsmappe, oppdaterTilstand, lagTermin, lagFunn } from './mva/felles.js';
import { oppsett as lesOppsett, gjeldendeTermSize, uttrekk } from './mva/uttrekk.js';
import { finnKlientmappe, lesProfil, lesKjenteAvvik } from './mva/profil.js';
import { ureg } from './mva/kontroller/ureg.js';
import { grunnlag } from './mva/kontroller/grunnlag.js';
import { reskontro } from './mva/kontroller/reskontro.js';
import { bank } from './mva/kontroller/bank.js';
import { skattekonto } from './mva/kontroller/skattekonto.js';
import { ehfKontroll } from './mva/kontroller/ehfkontroll.js';
import { dempKjente, port, tilVurdering, dokumentasjonsplan, beslutningsliste, fraVurdering } from './mva/liste.js';

try {
  if (process.argv[2] === 'status') await statusKommando(process.argv.slice(3));
  else await kontroll();
} catch (e) {
  console.error(`Feil: ${kortFeil(e)}`);
  process.exitCode = 1;
}

/** mva status: registrering, levert, betalt, rest, forfall, 2740 og skattekonto per klient for terminen. */
async function statusKommando(liste) {
  const a = argumenter(liste);
  const aar = Number(a.aar), termin = Number(a.termin);
  if (!(aar > 2000) || !(termin >= 1 && termin <= 6)) throw new Error('Bruk: npm run -s mva -- status (--client "klient" | --alle) --aar ÅÅÅÅ --termin 1–6 [--json]. Ingenting er gjort.');
  const utvalg = await klientutvalg(a);
  const res = await perKlient(utvalg, (c) => mvaStatus(bind(c), aar, termin));
  const rader = res.map((r) => (r.ok
    ? { klient: r.klient, orgnr: r.orgnr, ...r.data }
    : { klient: r.klient, orgnr: r.orgnr, termin: `${termin}/${aar}`, gruppe: 'kunne ikke leses', feil: r.feil }));
  if (a.json) { console.log(JSON.stringify(rader, null, 1)); return; }
  const kr = (n) => (n == null ? '–' : n.toLocaleString('nb-NO', { minimumFractionDigits: 2, maximumFractionDigits: 2 }));
  for (const x of rader) {
    const detalj = x.aktuell ? ` – levert ${x.levert ?? '–'}, betalt ${x.betalt ?? '–'}, å betale ${kr(x.aaBetale)}, rest ${kr(x.rest)}, forfall ${x.forfall ?? '–'}` : '';
    console.log(`${x.klient}: ${x.gruppe}${x.feil ? ` (${x.feil})` : ''}${detalj}${x.registrert ? `, 2740 ${kr(x.saldo2740)}` : ''}`);
  }
  if (rader.length > 1) {
    const t = {};
    for (const x of rader) t[x.gruppe] = (t[x.gruppe] ?? 0) + 1;
    console.log(`\n${rader.length} klienter: ${Object.entries(t).map(([g, n]) => `${g} ${n}`).join(', ')}`);
  }
}

/** Kontrollen før innsending (én klient og termin). */
async function kontroll() {
const args = process.argv.slice(2);
const opt = (n) => { const i = args.indexOf(n); return i >= 0 ? args[i + 1] : undefined; };
const klientNavn = opt('--client') ?? args.find((a, i) => !a.startsWith('--') && !['--aar', '--termin'].includes(args[i - 1]));
const aar = Number(opt('--aar'));
const termin = Number(opt('--termin'));
const json = args.includes('--json');
// --aarlig: også kontrollene som hører til årsoppgjøret/første kjøring (kontoplan, gamle åpne poster, bank hittil i år, § 3-26 som er avklart).
const aarlig = args.includes('--aarlig');
const logg = (s) => process.stderr.write(`  … ${s}\n`);

if (!klientNavn || !aar || !termin) {
  throw new Error('Bruk: npm run -s mva -- "<klient>" --aar 2026 --termin 4 [--gjenbruk] [--json] [--aarlig]. Ingenting er gjort.');
}

const b = await connect(klientNavn);
logg(`${b.company.name}: oppsett`);
const oppsett = await lesOppsett(b);
// Terminlengden gjelder fra terminstart (den kan endres i løpet av året).
const ts0 = gjeldendeTermSize(oppsett.terminlengder, `${aar}-01-01`);
const ts1 = gjeldendeTermSize(oppsett.terminlengder, lagTermin(aar, termin, ts0).start);
const t = lagTermin(aar, termin, ts1);
const am = arbeidsmappe(aar, termin, b.company.id);
const klientmappe = finnKlientmappe(b.company.name);
const profil = lesProfil(klientmappe);
const kjente = lesKjenteAvvik(klientmappe);
oppdaterTilstand(am, { klient: b.company.name, kundeId: b.company.id, aar, termin, modus: oppsett.modus, stadium: 'OPPSETT_OK', klientmappe: klientmappe ? 'funnet' : 'ikke funnet' });
am.lagre('oppsett.json', { ...oppsett, termin: t });

let manifest = am.les('manifest.json');
const sammeProfil = manifest && JSON.stringify(manifest.profil) === JSON.stringify({ kunde: profil.kontoKunde, leverandor: profil.kontoLeverandor });
if (args.includes('--gjenbruk') && manifest && !sammeProfil) logg('kontoene i klientprofilen er endret – henter på nytt');
if (!args.includes('--gjenbruk') || !manifest || !sammeProfil) {
  manifest = await uttrekk(b, am, t, profil, logg);
}
oppdaterTilstand(am, { stadium: 'DATA_OK' });

const navn = ['kontoer', 'vatTyper', 'posteringer', 'leverandorposteringer12', 'bilag', 'ikkeBokfort', 'innboks', 'leverandorfakturaer', 'saldo', 'saldo12', 'aapnePoster', 'kunder', 'leverandorer', 'bank', 'skattekonto', 'ehf'];
const d = Object.fromEntries(navn.map((n) => [n, am.les(`${n}.json`)]));
const ctx = { t, profil, oppsett, aarlig };

logg('kontroller');
let funn = [
  ...(oppsett.modus === 'REGISTRERT' ? [] : ureg(d, ctx)),
  ...grunnlag(d, ctx),
  ...reskontro(d, ctx),
  ...bank(d, ctx),
  ...skattekonto(d, ctx),
  ...ehfKontroll(d, ctx),
].filter((f) => !profil.deaktiverte.includes(f.kontroll));
// Datasett som ikke kunne hentes: kontrollene som bruker dem er ikke kjørt, og det skal synes (ikke se ut som «ingen funn»).
const manglerData = [
  ...Object.entries(manifest.datasett ?? {}).filter(([, v]) => v.feil).map(([k, v]) => `${k}: ${v.feil}`),
  ...(d.innboks?.feil ? [`innboks: ${d.innboks.feil}`] : []),
  ...(d.bank && !Array.isArray(d.bank.kontoer) ? [`bank: ${d.bank.feil}`] : []),
  ...(d.skattekonto?.feil ? [`skattekonto: ${d.skattekonto.feil}`] : []),
];
if (manglerData.length) {
  const kjent403 = manglerData.every((x) => /403/.test(x) && /9000/.test(x));
  funn.push(lagFunn({ kontroll: 'F0', alvor: kjent403 ? 'INFO' : 'FORKLAR', nivaa: 'klient',
    tittel: `${manglerData.length} datasett kunne ikke hentes – kontrollene som bruker dem er ikke kjørt`,
    detalj: manglerData.map((x) => x.replace(/\{.*$/, '').slice(0, 120)).join('; '),
    handling: kjent403 ? 'Sperret for API-brukeren (403). Sjekk brukerens tilganger hos klienten.' : 'Kjør på nytt. Vedvarer feilen, sjekk tilgangen.' }));
}
// Bilagsvurderingen (S4) legges i vurdering.json av agentene; ved --gjenbruk flettes den inn her.
const vurdering = fraVurdering(am.les('vurdering.json'), funn);
funn = dempKjente(vurdering.funn, kjente);
const portStatus = port(funn);
const utv = tilVurdering(d, funn, { modus: oppsett.modus });
const plan = dokumentasjonsplan(d, funn, { t, modus: oppsett.modus });
am.lagre('funn.json', funn);
am.lagre('overlevering.json', utv);
am.lagre('dokumentasjon.json', plan);
const md = beslutningsliste({ oppsett, t, funn, portStatus, utv, plan, manifest, bilagsvurdering: vurdering.sammendrag });
await import('node:fs').then(({ writeFileSync }) => writeFileSync(am.fil('beslutning-1.md'), md));
const state = oppdaterTilstand(am, { stadium: portStatus === 'RØD' ? 'STOPP' : 'KONTROLLERT', port: portStatus, antallFunn: funn.length, bilagTilVurdering: utv.bilag.length });

if (json) {
  // Kompakt sammendrag – det er dette Claude leser, ikke datasettene.
  const aktive = funn.filter((f) => !f.dempet);
  console.log(JSON.stringify({
    klient: b.company.name, termin: `${termin}/${aar}`, modus: oppsett.modus, port: portStatus, mappe: am.mappe,
    antall: Object.fromEntries(['STOPP', 'BLOKK', 'SPØR_REGNSKAPSFØRER', 'FORKLAR', 'INFO'].map((a) => [a, aktive.filter((f) => f.alvor === a).length])),
    punkter: aktive.filter((f) => f.alvor !== 'INFO').sort((a, c) => ['STOPP', 'BLOKK', 'SPØR_REGNSKAPSFØRER', 'FORKLAR'].indexOf(a.alvor) - ['STOPP', 'BLOKK', 'SPØR_REGNSKAPSFØRER', 'FORKLAR'].indexOf(c.alvor)).map((f) => ({ alvor: f.alvor, kontroll: f.kontroll, tittel: f.tittel, belop: f.belop === null ? null : Math.round(f.belop), noekkel: f.noekkel })),
    tilVurdering: utv.bilag.map((x) => x.bilag), dempet: funn.length - aktive.length,
  }, null, 1));

} else {
  const aktive = funn.filter((f) => !f.dempet);
  const telle = (a) => aktive.filter((f) => f.alvor === a).length;
  console.log(`${b.company.name} – termin ${termin} ${aar} (${t.start}–${t.sisteDag}), modus ${oppsett.modus}`);
  console.log(`Port ${portStatus}: ${telle('STOPP')} stopp, ${telle('BLOKK')} må rettes, ${telle('SPØR_REGNSKAPSFØRER')} spørsmål, ${telle('FORKLAR')} forklares, ${telle('INFO')} info.`);
  console.log(`Bilag til vurdering: ${utv.bilag.length} av ${utv.antallKandidater}. Klientprofil: ${klientmappe ? 'lokal (AVSTEMMINGER_ROT)' : 'standard'}.`);
  console.log(`Beslutningsliste: ${am.fil('beslutning-1.md')}`);
}
}
