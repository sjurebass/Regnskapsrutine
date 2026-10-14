// Lønn – KUN LESING.
//
//   npm run -s lonn -- hent --client "Klient" --aar 2026 --termin 4 [--a07 <a07.json>] [--ut <mappe>]
//   npm run -s lonn -- datoer (--client "Klient" [--client …] | --alle) --fra 2026-07 --til 2026-08 [--json]
//
// hent: skriver <ut>/ledger.json (standard %TEMP%\rr\lonn-<år>-T<termin>) i formatet som
// .claude/skills/lonnsavstemming/scripts/lonnsavstemming_a07.py forventer (se ledger_eksempel.json der):
// selskap, orgnr, periode (termin, fra, til, forfall), balanser (IB/bevegelse/UB i terminen), posteringer i terminen og
// pensjon_historikk hittil i år. --a07 (svaret fra Tally hent_amelding_rapport) gir AGA-satsen til pensjonsgrunnlaget.
// Feriepengesats, forklart, merknader og ytelse_konto fylles inn etterpå av den som avstemmer.
//
// datoer: lønnsdato (bilagsdato) per lønnskjøring per klient og måned: [{klient, maaned, dato, antall_slipper}].
// Leser bare id, periode og kjøring fra /salary/payslip – ingen ansattdata.
//
// Terminene: 1 = jan–feb, 2 = mar–apr, 3 = mai–jun, 4 = jul–aug, 5 = sep–okt, 6 = nov–des. Forfall = 15. i måneden etter.
// GDPR: lønnsbilagenes posteringstekster har ikke ansattnavn («Lønnsbilag N-ÅÅÅÅ»), men all tekst maskeres med redactText().
// Konsollen viser bare antall og summer.

import { mkdirSync, writeFileSync, readFileSync, existsSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { connect, list } from './tripletex.js';
import { redactText } from './privacy.js';
import { argumenter, klientutvalg, perKlient, standardUt, erMaaned, nesteMnd } from './valg.js';

const args = process.argv.slice(2);
const kommando = args[0];
const opt = (n) => { const i = args.indexOf(n); return i >= 0 ? args[i + 1] : undefined; };
const r2 = (x) => Math.round(x * 100) / 100;
const pad = (n) => String(n).padStart(2, '0');

try {
  if (kommando === 'datoer') await datoer();
  else if (kommando === 'hent') await hent();
  else throw new Error('Bruk: npm run -s lonn -- hent --client "Klient" --aar ÅÅÅÅ --termin 1–6 [--a07 <a07.json>] [--ut <mappe>]\n' +
    '      npm run -s lonn -- datoer (--client "Klient" | --alle) --fra ÅÅÅÅ-MM --til ÅÅÅÅ-MM [--json]\nIngenting er gjort.');
} catch (e) {
  console.error(`Feil: ${redactText(e.message.split('\n').slice(0, 2).join('\n'))}`);
  process.exitCode = 1;
}

/** Lønnsdato per kjøring: lønnsslippene i perioden gruppert på lønnskjøring (transaction). */
async function datoer() {
  const a = argumenter(args.slice(1));
  if (!erMaaned(a.fra) || !erMaaned(a.til) || a.fra > a.til) throw new Error('Angi --fra ÅÅÅÅ-MM og --til ÅÅÅÅ-MM (fra ≤ til). Ingenting er gjort.');
  const utvalg = await klientutvalg(a);
  const etter = nesteMnd(a.til); // eksklusiv: første måned etter perioden
  const res = await perKlient(utvalg, async (c) => {
    const slipper = await list('/salary/payslip', { companyId: c.id, query: {
      yearFrom: Number(a.fra.slice(0, 4)), monthFrom: Number(a.fra.slice(5, 7)), yearTo: Number(etter.slice(0, 4)), monthTo: Number(etter.slice(5, 7)),
      fields: 'id,year,month,date,transaction(id,date)',
    } });
    const kjoringer = new Map();
    for (const s of slipper) {
      const maaned = `${s.year}-${pad(s.month)}`;
      if (maaned < a.fra || maaned > a.til) continue;
      const nokkel = s.transaction?.id ?? `${maaned}|${s.date}`;
      const k = kjoringer.get(nokkel) ?? { maaned, dato: s.transaction?.date ?? s.date ?? null, antall_slipper: 0 };
      k.antall_slipper++;
      kjoringer.set(nokkel, k);
    }
    return [...kjoringer.values()].sort((x, y) => x.maaned.localeCompare(y.maaned) || String(x.dato).localeCompare(String(y.dato)));
  });
  const rader = res.flatMap((r) => (r.ok ? r.data.map((k) => ({ klient: r.klient, ...k })) : [{ klient: r.klient, maaned: null, dato: null, antall_slipper: null, feil: r.feil }]));
  // Klienter uten lønn i perioden får én rad med antall_slipper 0, så de ikke forsvinner fra lista.
  for (const r of res) if (r.ok && !r.data.length) rader.push({ klient: r.klient, maaned: null, dato: null, antall_slipper: 0 });
  if (a.json) { console.log(JSON.stringify(rader, null, 1)); return; }
  for (const r of rader) {
    console.log(`${r.klient}: ${r.feil ? `kunne ikke leses (${r.feil})` : r.maaned ? `${r.maaned} lønnsdato ${r.dato ?? '–'} (${r.antall_slipper} lønnsslipper)` : 'ingen lønnskjøring i perioden'}`);
  }
}

async function hent() {
const AAR = Number(opt('--aar'));
const TERMIN = Number(opt('--termin'));
if (!opt('--client') || !(AAR > 2000) || !(TERMIN >= 1 && TERMIN <= 6)) {
  throw new Error('Bruk: npm run -s lonn -- hent --client "Klient" --aar ÅÅÅÅ --termin 1–6 [--a07 <a07.json>] [--ut <mappe>]\nIngenting er gjort.');
}

const forsteMnd = TERMIN * 2 - 1;
const D1 = `${AAR}-${pad(forsteMnd)}-01`;
const D2 = TERMIN === 6 ? `${AAR + 1}-01-01` : `${AAR}-${pad(forsteMnd + 2)}-01`; // eksklusiv
const Y1 = `${AAR}-01-01`;
const FORFALL = TERMIN === 6 ? `${AAR + 1}-01-15` : `${AAR}-${pad(forsteMnd + 2)}-15`;

// Kontoområdene lønnsavstemmingen trenger (samme som det tidligere uttrekket via connectoren).
const POSTERINGER = [[1920, 1920], [1950, 1950], [2600, 2600], [2770, 2799], [2900, 2999], [5000, 5999], [7100, 7199], [7740, 7740]];
const SALDOER = [[1950, 1950], [2600, 2600], [2770, 2799], [2900, 2999], [5000, 5999]];
const LONN_I_BANK = /lønn|lonn|skattetrekk|forskuddstrekk|arbeidsgiveravgift|aga|a-melding/i;

const c = await connect(opt('--client'));
const FELT = 'date,amount,description,account(number,name),voucher(number,year,description)';

const hentPost = (fra, til, kFra, kTil) =>
  c.list('/ledger/posting', { query: { dateFrom: fra, dateTo: til, accountNumberFrom: kFra, accountNumberTo: kTil, fields: FELT } });

// Personnavn står i noen tekster: nettolønn til bank («Lønnsbilag N-ÅÅÅÅ. Overføring til <navn> (<kontonr>)»), reiseregninger og
// ansattutlegg («Reiseregning nummer N-N, <navn>. …»). redactText fjerner ikke navn, så de tas bort her. Reisekontoene (71xx)
// trengs bare som beløp, og teksten der (filnavn på kvitteringer) erstattes helt.
function utenNavn(t, konto) {
  if (konto >= 7100 && konto <= 7199) return /^reiseregning|^ansattutlegg/i.test(t) ? t.replace(/^(\S+ nummer [\d-]+).*$/i, '$1') : 'Reise/utlegg';
  return t
    .replace(/(Overføring til )[^(]*(\(|$)/i, '$1ansatt $2')
    .replace(/^((?:Reiseregning|Ansattutlegg) nummer [\d-]+),[^.]*/i, '$1');
}
const tekst = (p) => utenNavn(redactText(p.description || p.voucher?.description || ''), p.account?.number ?? 0);
const rad = (p) => [p.date, String(p.voucher?.number ?? ''), p.account?.number, p.account?.name ?? '', tekst(p), r2(p.amount ?? 0)];

const advarsler = [];
const posteringer = [];
for (const [fra, til] of POSTERINGER) {
  try {
    for (const p of await hentPost(D1, D2, fra, til)) {
      const r = rad(p);
      if (fra === 1920 && !LONN_I_BANK.test(r[4])) continue; // bare bankposter som hører til lønn
      posteringer.push(r);
    }
  } catch (e) { advarsler.push(`Posteringer ${fra}–${til}: ${redactText(e.message.split('\n')[0]).slice(0, 160)}`); }
}
posteringer.sort((a, b) => a[0].localeCompare(b[0]) || a[1].localeCompare(b[1]) || a[2] - b[2]);

const balanser = [];
for (const [fra, til] of SALDOER) {
  try {
    const rader = await c.list('/balanceSheet', { query: { dateFrom: D1, dateTo: D2, accountNumberFrom: fra, accountNumberTo: til,
      fields: 'account(number,name),balanceIn,balanceChange,balanceOut' } });
    for (const b of rader) {
      if (!b.account?.number) continue;
      balanser.push({ a: b.account.number, n: b.account.name ?? '', ib: r2(b.balanceIn ?? 0), ch: r2(b.balanceChange ?? 0), ub: r2(b.balanceOut ?? 0) });
    }
  } catch (e) { advarsler.push(`Saldo ${fra}–${til}: ${redactText(e.message.split('\n')[0]).slice(0, 160)}`); }
}
// /balanceSheet kan utelate kontoer uten IB, bevegelse og UB. 2600 regnes da fra posteringene (IB 0).
if (!balanser.some((b) => b.a === 2600)) {
  const ch = r2(posteringer.filter((p) => p[2] === 2600).reduce((s, p) => s + p[5], 0));
  balanser.push({ a: 2600, n: 'Forskuddstrekk', ib: 0, ch, ub: ch });
  advarsler.push('2600 manglet i saldobalansen – regnet fra posteringene med IB 0. Sjekk IB.');
}
balanser.sort((a, b) => a.a - b.a);

// Pensjon hittil i år: 594x/5950 per måned, og AGA på pensjonsbilag (5400 med tekst som starter med «Pensjon») → grunnlag.
let agaSats = null;
const a07Sti = opt('--a07');
if (a07Sti) {
  try {
    const a07 = JSON.parse(readFileSync(resolve(a07Sti), 'utf8'));
    agaSats = (a07.avgiftsgrunnlag ?? []).find((g) => g.type === 'loenn')?.sats ?? (a07.avgiftsgrunnlag ?? [])[0]?.sats ?? null;
  } catch (e) { advarsler.push(`Kunne ikke lese --a07: ${e.message.slice(0, 120)}`); }
}
const pensjonHistorikk = [];
try {
  const pensjon = await hentPost(Y1, D2, 5940, 5959);
  const agaPensjon = (await hentPost(Y1, D2, 5400, 5400)).filter((p) => /^pensjon/i.test(tekst(p)));
  const maaneder = [...new Set([...pensjon, ...agaPensjon].map((p) => p.date.slice(0, 7)))].sort();
  for (const m of maaneder) {
    const kost = pensjon.filter((p) => p.date.startsWith(m));
    const aga = agaPensjon.filter((p) => p.date.startsWith(m));
    const agaSum = aga.reduce((s, p) => s + (p.amount ?? 0), 0);
    pensjonHistorikk.push([
      m, kost.map(tekst)[0] ?? '', r2(kost.reduce((s, p) => s + (p.amount ?? 0), 0)),
      aga.map(tekst)[0] ?? '', agaSats && agaSum ? Math.round(agaSum / (agaSats / 100)) : 0,
    ]);
  }
  if (!agaSats && agaPensjon.length) advarsler.push('Pensjonsgrunnlaget er 0 fordi AGA-satsen mangler – kjør med --a07.');
} catch (e) { advarsler.push(`Pensjon hittil i år: ${redactText(e.message.split('\n')[0]).slice(0, 160)}`); }

const ledger = {
  selskap: c.company.name,
  orgnr: c.company.organizationNumber ?? '',
  tripletex_id: String(c.company.id),
  periode: { termin: TERMIN, fra: D1, til: D2, forfall: FORFALL },
  kilde_a07: `A07: Skatteetaten via Tally (Maskinporten), ${D1.slice(0, 7)}–${AAR}-${pad(forsteMnd + 1)}`,
  kilde_regnskap: `Regnskap: Tripletex API, posteringer ${D1}–${D2} (eksklusiv)`,
  aga_sats: agaSats,
  feriepenger_sats: null,
  balanser,
  posteringer,
  pensjon_historikk: pensjonHistorikk,
  forklart: [],
  merknader: [],
  advarsler,
};
const UT = resolve(opt('--ut') ?? standardUt('lonn', `${AAR}-T${TERMIN}`));
mkdirSync(UT, { recursive: true });
writeFileSync(join(UT, 'ledger.json'), JSON.stringify(ledger, null, 1));

const sum = (k) => r2(posteringer.filter((p) => p[2] === k).reduce((s, p) => s + p[5], 0));
console.log(`${c.company.name} termin ${TERMIN} ${AAR} (${D1}–${D2}): ${posteringer.length} posteringer, ${balanser.length} saldoer, ` +
  `${pensjonHistorikk.length} pensjonsmåneder. Bevegelse 2600 ${sum(2600)}, 2770 ${sum(2770)}, 5000 ${sum(5000)}.`);
if (advarsler.length) console.log(`Advarsler:\n- ${advarsler.join('\n- ')}`);
console.log(`Skrevet: ${join(UT, 'ledger.json')}. Fyll inn feriepenger_sats (les 5020/5000 i et lønnsbilag), forklart og merknader.`);
}
