// Resultat og balanse med sammenligning og avvik – KUN LESING.
//
//   npm run -s regnskap -- --client "Klient" --periode ÅÅÅÅ-MM|ÅÅÅÅ-T<n>|ÅÅÅÅ [--hittil] [--sammenlign forrige,ifjor,budsjett]
//                          [--vesentlighet <beløp>] [--terskel-pst <tall>] [--bagatell <beløp>] [--json] [--ut <mappe>]
//
// Periode: ÅÅÅÅ-MM (måned), ÅÅÅÅ-T<n> (mva-termin, to måneder: T1 = jan–feb … T6 = nov–des), ÅÅÅÅ (kalenderår).
//   --hittil: fra 1. januar til og med periodens slutt. For ÅÅÅÅ betyr det til og med siste avsluttede måned (inneværende år).
// Sammenligninger (standard forrige,ifjor):
//   forrige  = like lang periode rett før (måned → forrige måned, termin → forrige termin, år → fjoråret, hittil → like mange måneder før).
//   ifjor    = samme periode i fjor.
//   budsjett = resultatbudsjett for selskapet (GET /resultbudget/company?year=, bare resultatkontoer). Finnes ingen budsjettlinjer,
//              eller kallet feiler, står kolonnen som «ikke funnet» med grunn – kommandoen feiler aldri på budsjett.
//              Fortegn antas som hovedboken (kredit negativ); er både 3xxx og 4xxx–7xxx positive, snus inntektene (står i kolonnen).
//
// Data: én GET /balanceSheet per kolonne (dateFrom/dateTo, dateTo eksklusiv, kontoer 1000–8999, fields account(number,name),
// balanceIn,balanceChange,balanceOut). Resultat = balanceChange for 3000–8999. Balanse = balanceOut for 1000–2999 ved periodeslutt.
// Resultatkontoene nullstilles 1.1. i Tripletex, så balanceOut på 3000–8999 er resultatet hittil i året.
//
// Oppstilling (artsinndelt, rskl. § 6-1 / NS 4102):
//   driftsinntekter 3000–3999 · varekostnad 4000–4999 · lonnskostnad 5000–5999 · avskrivning 6000–6099 · annenDriftskostnad 6100–7999
//   = sumDriftskostnader, driftsresultat · finansinntekter 8000–8099 · finanskostnader 8100–8199
//   · andreResultatposter 8200–8299 og 8400–8799 (normalt tomme, vises bare når ≠ 0) = resultatForSkatt · skattekostnad 8300–8399
//   = aarsresultat · disponeringer 8800–8999 (overføringer og disponeringer, vises bare når ≠ 0) = resultatEtterDisponeringer
//   (vises bare når den er ulik aarsresultat).
//   Balanse: anleggsmidler 1000–1399 · omlopsmidler 1400–1999 = sumEiendeler · egenkapital 2000–2099 · langsiktigGjeld 2100–2299
//   (avsetninger og langsiktig gjeld) · kortsiktigGjeld 2300–2999 = sumGjeld, sumEgenkapitalOgGjeld.
//   Egenkapitalen får to beregnede linjer uten konto (id resultatHittil og udisponertTidligere, uten flagg): «Årets resultat (ikke
//   disponert)» = resultat hittil i år som ikke er ført mot egenkapital, og «Udisponert resultat tidligere år» (fjorårets resultat
//   som ikke er disponert, normalt 0), slik at sumEiendeler = sumEgenkapitalOgGjeld.
//
// Fortegn i oppstillingen: inntekter og kostnader vises som positive tall (inntekt = −hovedbok, kostnad = hovedbok);
// resultatlinjer = inntekter − kostnader. Eiendeler vises positive (= hovedbok), egenkapital og gjeld positive (= −hovedbok).
// Avvik = denne − sammenligning; avvik % = avvik / |sammenligning| × 100 (null når sammenligningen er 0).
// gunstig: true/false for resultatlinjer (inntekt opp eller kostnad ned = gunstig), null for balansen.
//
// Flagg per linje og sammenligning:
//   "V"   |avvik| ≥ vesentlighetsgrensen V (--vesentlighet; standard høyeste av 5 000 og 0,5 % av driftsinntektene siste 12 mnd,
//         jf. CLAUDE.md – V fra kundeinstruksen skal sendes inn med --vesentlighet).
//   "pst" |avvik %| ≥ terskel (--terskel-pst; standard 20 for forrige, 15 for ifjor og 10 for budsjett) og |avvik| ≥ bagatellgrensen.
//   "ny"  sammenligningen er 0 og |denne| ≥ bagatellgrensen.
//   Bagatellgrensen (--bagatell, standard V/2) hindrer prosentflagg på småbeløp.
// Nøkkeltall (null ved deling på 0): bruttomargin, driftsmargin, lønn i % av driftsinntekter, likviditetsgrad 1
// (omløpsmidler / kortsiktig gjeld), egenkapitalandel (egenkapital inkl. udisponert resultat / sum eiendeler). Endring i prosentpoeng.
// Kontroller: resultatEtterDisponeringer = −(sum balanceChange 3000–8999); eiendeler − (bokført EK + gjeld) = resultat hittil i år
// + udisponert fra tidligere år (sum balanceIn 1000–8999 ved periodestart = IB 1.1. som ikke er disponert). ≠ 0 gir merknad.
//
// Utdata: full JSON i <ut>/regnskap.json (standard %TEMP%\rr\regnskap-<periode>[-hittil]) og kompakt tabell på konsollen
// (grupper, summer, flaggede kontoer, nøkkeltall, kontroller). --json uten --ut: JSON-en på stdout i stedet for fil og tabell.
// --json med --ut: fil og tabell som uten --json, så store uttrekk ikke havner i chatten.
//
// regnskap.json (versjon 1) – laget for å kunne gjøres om til en silfer-rapport-spec:
// { versjon: 1, kommando: "regnskap", klient, orgnr, klientId, laget: ISO-tid,
//   periode: "2026-09" | "2026-T5" | "2026", periodeType: "maaned" | "termin" | "aar", hittil: bool, periodeTekst,
//   kolonner: [ { id: "denne" | "forrige" | "ifjor" | "budsjett", tekst, fra: "ÅÅÅÅ-MM-DD", til: "ÅÅÅÅ-MM-DD" (inklusiv),
//                 tilEksklusiv, balansedato (= til; null for budsjett), status: "ok" | "ikke funnet", grunn?, fortegn? } ],
//   fortegn: "<forklaring>",
//   terskler: { vesentlighet, vesentlighetKilde, terskelPst: { forrige, ifjor, budsjett }, bagatell },
//   resultat: { rader: [Rad] }, balanse: { rader: [Rad] },
//   Rad = { nivaa: "gruppe" | "konto" | "sum", id, gruppe, konto: <nr> | null, tekst, art: "inntekt" | "kostnad" | "resultat" |
//           "eiendel" | "egenkapital" | "gjeld" | "sum",
//           denne: <beløp>, forrige?: <beløp>, ifjor?: <beløp>, budsjett?: <beløp> | null,       // bare kolonnene som er bedt om
//           avvik: { forrige?: Avvik, ifjor?: Avvik, budsjett?: Avvik } }
//   Avvik = { kr, pst: <tall> | null, gunstig: bool | null, flagg: ["V", "pst", "ny"] }
//   Rekkefølge: gruppelinje først, så kontoene i gruppen, så sumlinjer der de hører hjemme i oppstillingen.
//   nokkeltall: [ { id, tekst, enhet: "pst" | "forhold", formel, denne, forrige?, ifjor?, budsjett?, endring: { forrige?, ifjor?, budsjett? } } ],
//   flagg: [ { del: "resultat" | "balanse", nivaa, id, konto, tekst, sammenligning, denne, verdi, avvik, avvikPst, gunstig, flagg } ]
//          (sortert på |avvik| synkende),
//   kontroll: { resultat: { resultatEtterDisponeringer, minusSumEndring3000_8999, differanse, ok },
//               balanse: { balansedato, eiendeler, egenkapitalOgGjeldBokfort, differanse, resultatHittil, udisponertTidligereAar,
//                          rest, ok, tidligereAarDisponert } },
//   merknader: [] }
// Kontonavn er maskert med redactText(). Ingen posteringer, ingen fritekst fra bilag.

import { writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { connect } from './tripletex.js';
import { redactText } from './privacy.js';
import { argumenter, utmappe, kortFeil, rund } from './valg.js';

const RESULTAT = [
  { id: 'driftsinntekter', tekst: 'Driftsinntekter', fra: 3000, til: 3999, art: 'inntekt' },
  { id: 'varekostnad', tekst: 'Varekostnad', fra: 4000, til: 4999, art: 'kostnad' },
  { id: 'lonnskostnad', tekst: 'Lønnskostnad', fra: 5000, til: 5999, art: 'kostnad' },
  { id: 'avskrivning', tekst: 'Avskrivning og nedskrivning', fra: 6000, til: 6099, art: 'kostnad' },
  { id: 'annenDriftskostnad', tekst: 'Annen driftskostnad', fra: 6100, til: 7999, art: 'kostnad' },
  { id: 'sumDriftskostnader', tekst: 'Sum driftskostnader', sum: { pluss: ['varekostnad', 'lonnskostnad', 'avskrivning', 'annenDriftskostnad'] }, art: 'kostnad' },
  { id: 'driftsresultat', tekst: 'Driftsresultat', sum: { pluss: ['driftsinntekter'], minus: ['sumDriftskostnader'] }, art: 'resultat' },
  { id: 'finansinntekter', tekst: 'Finansinntekter', fra: 8000, til: 8099, art: 'inntekt' },
  { id: 'finanskostnader', tekst: 'Finanskostnader', fra: 8100, til: 8199, art: 'kostnad' },
  { id: 'andreResultatposter', tekst: 'Andre poster (82xx, 84xx–87xx)', kontoer: [[8200, 8299], [8400, 8799]], art: 'kostnad', skjulNull: true },
  { id: 'resultatForSkatt', tekst: 'Resultat før skatt', sum: { pluss: ['driftsresultat', 'finansinntekter'], minus: ['finanskostnader', 'andreResultatposter'] }, art: 'resultat' },
  { id: 'skattekostnad', tekst: 'Skattekostnad', fra: 8300, til: 8399, art: 'kostnad' },
  { id: 'aarsresultat', tekst: 'Årsresultat', sum: { pluss: ['resultatForSkatt'], minus: ['skattekostnad'] }, art: 'resultat' },
  { id: 'disponeringer', tekst: 'Overføringer og disponeringer', fra: 8800, til: 8999, art: 'kostnad', skjulNull: true },
  { id: 'resultatEtterDisponeringer', tekst: 'Resultat etter disponeringer', sum: { pluss: ['aarsresultat'], minus: ['disponeringer'] }, art: 'resultat', skjulLik: 'aarsresultat' },
];
const BALANSE = [
  { id: 'anleggsmidler', tekst: 'Anleggsmidler', fra: 1000, til: 1399, art: 'eiendel' },
  { id: 'omlopsmidler', tekst: 'Omløpsmidler', fra: 1400, til: 1999, art: 'eiendel' },
  { id: 'sumEiendeler', tekst: 'Sum eiendeler', sum: { pluss: ['anleggsmidler', 'omlopsmidler'] }, art: 'sum' },
  { id: 'egenkapital', tekst: 'Egenkapital', fra: 2000, til: 2099, art: 'egenkapital' },
  { id: 'langsiktigGjeld', tekst: 'Avsetninger og langsiktig gjeld', fra: 2100, til: 2299, art: 'gjeld' },
  { id: 'kortsiktigGjeld', tekst: 'Kortsiktig gjeld', fra: 2300, til: 2999, art: 'gjeld' },
  { id: 'sumGjeld', tekst: 'Sum gjeld', sum: { pluss: ['langsiktigGjeld', 'kortsiktigGjeld'] }, art: 'sum' },
  { id: 'sumEgenkapitalOgGjeld', tekst: 'Sum egenkapital og gjeld', sum: { pluss: ['egenkapital', 'sumGjeld'] }, art: 'sum' },
];
const SAMMENLIGNINGER = ['forrige', 'ifjor', 'budsjett'];
const STD_TERSKEL = { forrige: 20, ifjor: 15, budsjett: 10 };
const MND = ['januar', 'februar', 'mars', 'april', 'mai', 'juni', 'juli', 'august', 'september', 'oktober', 'november', 'desember'];
const KORT = ['jan', 'feb', 'mar', 'apr', 'mai', 'jun', 'jul', 'aug', 'sep', 'okt', 'nov', 'des'];

const pad = (n) => String(n).padStart(2, '0');
/** Hører kontoen til linjen? Linjen har fra/til eller kontoer: [[fra, til], …]. */
const iLinje = (l, k) => (l.kontoer ?? [[l.fra, l.til]]).some(([x, y]) => k >= x && k <= y);
const nesteMnd = (m, n = 1) => { const d = new Date(`${m}-01T00:00:00Z`); d.setUTCMonth(d.getUTCMonth() + n); return d.toISOString().slice(0, 7); };
const dagFor = (d) => { const x = new Date(`${d}T00:00:00Z`); x.setUTCDate(x.getUTCDate() - 1); return x.toISOString().slice(0, 10); };
const null0 = (x) => Math.abs(x ?? 0) < 0.005;
const kr = (n) => { if (n === null || n === undefined) return '–'; const s = Math.round(Math.abs(n)).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' '); return n < 0 && Math.round(Math.abs(n)) ? `-${s}` : s; };
const pst = (n) => (n === null || n === undefined ? '' : Math.abs(n) >= 1000 ? String(Math.round(n)) : n.toFixed(1).replace('.', ','));
const tall = (s) => { const n = Number(String(s).replace(/\s/g, '').replace(',', '.')); return Number.isFinite(n) ? n : NaN; };

function bruk(melding) {
  return Object.assign(new Error(`${melding ? `${melding}\n` : ''}Bruk: npm run -s regnskap -- --client "Klient" --periode ÅÅÅÅ-MM|ÅÅÅÅ-T<n>|ÅÅÅÅ [--hittil] ` +
    '[--sammenlign forrige,ifjor,budsjett] [--vesentlighet <beløp>] [--terskel-pst <tall>] [--bagatell <beløp>] [--json] [--ut <mappe>]\nIngenting er gjort.'), { bruk: true });
}

/** Tekst for et vindu av hele måneder [fraM, fraM + mnd). */
function vinduTekst(fraM, mnd) {
  const [y1, m1] = fraM.split('-').map(Number);
  const [y2, m2] = nesteMnd(fraM, mnd - 1).split('-').map(Number);
  if (mnd === 1) return `${MND[m1 - 1]} ${y1}`;
  if (mnd === 12 && m1 === 1) return `${y1}`;
  return `${KORT[m1 - 1]}${y1 !== y2 ? ` ${y1}` : ''}–${KORT[m2 - 1]} ${y2}`;
}

/** Vindu av hele måneder: { fraM, mnd, fra, tilEksklusiv, til, tekst }. */
function vindu(fraM, mnd) {
  const tilEksklusiv = `${nesteMnd(fraM, mnd)}-01`;
  return { fraM, mnd, fra: `${fraM}-01`, tilEksklusiv, til: dagFor(tilEksklusiv), tekst: vinduTekst(fraM, mnd) };
}

/** --periode og --hittil → periodevinduet. */
export function tolkPeriode(p, hittil, idag = new Date()) {
  let m, y, fraMnd, mnd, type;
  if ((m = /^(\d{4})-(0[1-9]|1[0-2])$/.exec(p ?? ''))) { y = Number(m[1]); fraMnd = Number(m[2]); mnd = 1; type = 'maaned'; }
  else if ((m = /^(\d{4})-T([1-6])$/i.exec(p ?? ''))) { y = Number(m[1]); fraMnd = Number(m[2]) * 2 - 1; mnd = 2; type = 'termin'; }
  else if ((m = /^(\d{4})$/.exec(p ?? ''))) { y = Number(m[1]); fraMnd = 1; mnd = 12; type = 'aar'; }
  else throw bruk('Angi --periode som ÅÅÅÅ-MM, ÅÅÅÅ-T<n> (1–6) eller ÅÅÅÅ.');
  let fraM = `${y}-${pad(fraMnd)}`;
  let sluttM = nesteMnd(fraM, mnd); // eksklusiv
  if (hittil) {
    if (type === 'aar') {
      const naa = `${idag.getUTCFullYear()}-${pad(idag.getUTCMonth() + 1)}`; // første måned som ikke er avsluttet
      if (naa < sluttM) sluttM = naa;
      if (sluttM <= `${y}-01`) throw bruk(`Ingen avsluttede måneder i ${y} ennå.`);
    }
    fraM = `${y}-01`;
  }
  const antall = (Number(sluttM.slice(0, 4)) - Number(fraM.slice(0, 4))) * 12 + Number(sluttM.slice(5, 7)) - Number(fraM.slice(5, 7));
  const v = vindu(fraM, antall);
  const termTekst = type === 'termin' && !hittil ? `termin ${Number(p.slice(-1))} ${y} (${v.tekst})` : null;
  const tekst = termTekst ?? (hittil ? `hittil i år ${v.tekst}` : v.tekst);
  return { ...v, type, tekst };
}

/** Saldobalanse for et vindu: Map konto → { navn, ib, endring, ub }. */
async function saldo(c, v) {
  const rader = await c.list('/balanceSheet', { query: { dateFrom: v.fra, dateTo: v.tilEksklusiv, accountNumberFrom: 1000, accountNumberTo: 8999,
    fields: 'account(number,name),balanceIn,balanceChange,balanceOut' } });
  const ut = new Map();
  for (const r of rader) {
    const k = r.account?.number;
    if (!k) continue;
    const x = ut.get(k) ?? { navn: r.account.name ?? '', ib: 0, endring: 0, ub: 0 };
    x.ib += r.balanceIn ?? 0; x.endring += r.balanceChange ?? 0; x.ub += r.balanceOut ?? 0;
    ut.set(k, x);
  }
  return ut;
}

/** Resultatbudsjett for vinduet: { status, grunn?, fortegn?, kontoer: Map konto → beløp (hovedbokfortegn) }. */
async function budsjett(c, v) {
  const aar = [...new Set([v.fra.slice(0, 4), v.til.slice(0, 4)])];
  const linjer = [];
  try {
    for (const y of aar) linjer.push(...await c.list('/resultbudget/company', { query: { year: y, fields: 'account(number,name),accountingPeriod(start),amount' } }));
  } catch (e) {
    return { status: 'ikke funnet', grunn: `kunne ikke leses (${kortFeil(e)})` };
  }
  if (!linjer.length) return { status: 'ikke funnet', grunn: `ingen budsjettlinjer i /resultbudget/company for ${aar.join(', ')}` };
  const kontoer = new Map();
  let utenPeriode = 0;
  for (const l of linjer) {
    const k = l.account?.number;
    if (!k) continue;
    const start = String(l.accountingPeriod?.start ?? '').slice(0, 10);
    let belop = l.amount ?? 0;
    if (!start) { utenPeriode++; belop = belop * v.mnd / 12; } // årsbeløp uten periode: fordeles jevnt
    else if (start < v.fra || start >= v.tilEksklusiv) continue;
    kontoer.set(k, (kontoer.get(k) ?? 0) + belop);
  }
  const sumI = (a, b) => [...kontoer].filter(([k]) => k >= a && k <= b).reduce((s, [, x]) => s + x, 0);
  let fortegn = 'som hovedboken (kredit negativ)';
  if (sumI(3000, 3999) > 0 && sumI(4000, 7999) > 0) {
    fortegn = 'positive tall – inntektene (3000–3999, 8000–8099) er snudd';
    for (const [k, x] of kontoer) if ((k >= 3000 && k <= 3999) || (k >= 8000 && k <= 8099)) kontoer.set(k, -x);
  }
  if (!kontoer.size) return { status: 'ikke funnet', grunn: `ingen budsjettlinjer for ${v.tekst}` };
  return { status: 'ok', fortegn, kontoer, grunn: utenPeriode ? `${utenPeriode} linjer uten periode er fordelt med ${v.mnd}/12` : undefined };
}

/** Linjeverdier (oppstillingsfortegn) for én kolonne: { linjer: {id: beløp}, kontoer: {konto: beløp} }. */
function beregn(spec, raa, felt) {
  const linjer = {}, kontoer = {};
  for (const l of spec) {
    if (l.sum) {
      linjer[l.id] = rund((l.sum.pluss ?? []).reduce((s, i) => s + (linjer[i] ?? 0), 0) - (l.sum.minus ?? []).reduce((s, i) => s + (linjer[i] ?? 0), 0));
      continue;
    }
    let s = 0;
    for (const [k, x] of raa) {
      if (!iLinje(l, k)) continue;
      const verdi = felt(x);
      const vist = ['inntekt', 'egenkapital', 'gjeld'].includes(l.art) ? -verdi : verdi;
      kontoer[k] = rund(vist); s += vist;
    }
    linjer[l.id] = rund(s);
  }
  return { linjer, kontoer };
}

/** Balanse med beregnede EK-linjer: årets resultat hittil og udisponert fra tidligere år. */
function beregnBalanse(raa) {
  const b = beregn(BALANSE, raa, (x) => x.ub);
  let ubBal = 0, ubRes = 0, ibAlle = 0;
  for (const [k, x] of raa) {
    if (k <= 2999) ubBal += x.ub; else ubRes += x.ub;
    ibAlle += x.ib;
  }
  const resultatHittil = rund(-ubRes);
  const udisponert = rund(ubBal + ubRes);
  b.kontoer.resultatHittil = resultatHittil;
  b.kontoer.udisponertTidligere = udisponert;
  const ekBokfort = b.linjer.egenkapital;
  b.linjer.egenkapital = rund(ekBokfort + resultatHittil + udisponert);
  b.linjer.sumEgenkapitalOgGjeld = rund(b.linjer.egenkapital + b.linjer.sumGjeld);
  b.kontroll = { eiendeler: b.linjer.sumEiendeler, egenkapitalOgGjeldBokfort: rund(ekBokfort + b.linjer.sumGjeld), resultatHittil, ibAlle: rund(ibAlle), udisponert };
  return b;
}

/** Avvik mellom denne og en sammenligning. */
function avvik(denne, verdi, art, cmp, t) {
  const a = rund(denne - verdi);
  const p = null0(verdi) ? null : Math.round((a / Math.abs(verdi)) * 1000) / 10;
  const gunstig = null0(a) ? null : art === 'inntekt' || art === 'resultat' ? a > 0 : art === 'kostnad' ? a < 0 : null;
  const flagg = [];
  if (Math.abs(a) >= t.vesentlighet && !null0(a)) flagg.push('V');
  if (p !== null && Math.abs(p) >= t.terskelPst[cmp] && Math.abs(a) >= t.bagatell) flagg.push('pst');
  if (null0(verdi) && Math.abs(denne) >= t.bagatell) flagg.push('ny');
  return { kr: a, pst: p, gunstig, flagg };
}

/** Rader for resultat eller balanse i oppstillingsrekkefølge. */
function rader(spec, kol, cmps, navn, t, del) {
  const ut = [];
  const lag = (nivaa, id, gruppe, konto, tekst, art, verdi) => {
    const r = { nivaa, id, gruppe, konto, tekst, art, denne: verdi('denne') };
    for (const c of cmps) r[c] = verdi(c);
    r.avvik = {};
    for (const c of cmps) if (r[c] !== null && r[c] !== undefined) r.avvik[c] = avvik(r.denne ?? 0, r[c], art, c, t);
    if (nivaa === 'konto' && konto === null) for (const x of Object.values(r.avvik)) x.flagg = []; // beregnede EK-linjer flagges ikke
    return r;
  };
  const alle = ['denne', ...cmps];
  const v = (c, f) => (kol[c] ? f(kol[c]) ?? 0 : null);
  for (const l of spec) {
    const linje = (c) => v(c, (k) => k.linjer[l.id]);
    if (l.skjulNull && alle.every((c) => null0(linje(c)))) continue;
    if (l.skjulLik && alle.every((c) => null0((linje(c) ?? 0) - (v(c, (k) => k.linjer[l.skjulLik]) ?? 0)))) continue;
    if (l.sum) { ut.push(lag('sum', l.id, null, null, l.tekst, l.art === 'sum' ? 'sum' : l.art, linje)); continue; }
    ut.push(lag('gruppe', l.id, l.id, null, l.tekst, l.art, linje));
    const kontoer = new Set();
    for (const c of alle) for (const k of Object.keys(kol[c]?.kontoer ?? {})) if (/^\d+$/.test(k) && iLinje(l, Number(k))) kontoer.add(Number(k));
    for (const k of [...kontoer].sort((x, y) => x - y)) {
      const kv = (c) => v(c, (x) => x.kontoer[k]);
      if (alle.every((c) => null0(kv(c)))) continue;
      ut.push(lag('konto', String(k), l.id, k, redactText(navn.get(k) ?? ''), l.art, kv));
    }
    if (del === 'balanse' && l.id === 'egenkapital') {
      for (const [id, tekst] of [['resultatHittil', 'Årets resultat (ikke disponert)'], ['udisponertTidligere', 'Udisponert resultat tidligere år']]) {
        const kv = (c) => v(c, (x) => x.kontoer[id]);
        if (alle.every((c) => null0(kv(c)))) continue;
        ut.push(lag('konto', id, l.id, null, tekst, l.art, kv));
      }
    }
  }
  return ut;
}

const NOKKELTALL = [
  { id: 'bruttomargin', tekst: 'Bruttomargin', enhet: 'pst', formel: '(driftsinntekter − varekostnad) / driftsinntekter',
    f: (r) => [r.driftsinntekter - r.varekostnad, r.driftsinntekter] },
  { id: 'driftsmargin', tekst: 'Driftsmargin', enhet: 'pst', formel: 'driftsresultat / driftsinntekter', f: (r) => [r.driftsresultat, r.driftsinntekter] },
  { id: 'lonnAvInntekt', tekst: 'Lønn i % av driftsinntekter', enhet: 'pst', formel: 'lønnskostnad / driftsinntekter', f: (r) => [r.lonnskostnad, r.driftsinntekter] },
  { id: 'likviditetsgrad1', tekst: 'Likviditetsgrad 1', enhet: 'forhold', formel: 'omløpsmidler / kortsiktig gjeld', f: (r, b) => (b ? [b.omlopsmidler, b.kortsiktigGjeld] : null) },
  { id: 'egenkapitalandel', tekst: 'Egenkapitalandel', enhet: 'pst', formel: 'egenkapital (inkl. udisponert resultat) / sum eiendeler',
    f: (r, b) => (b ? [b.egenkapital, b.sumEiendeler] : null) },
];

function nokkeltall(res, bal, cmps) {
  return NOKKELTALL.map((n) => {
    const verdi = (c) => {
      if (!res[c]) return null;
      const x = n.f(res[c].linjer, bal[c]?.linjer);
      if (!x || x.some((y) => y === null || y === undefined) || null0(x[1])) return null;
      const q = x[0] / x[1];
      return n.enhet === 'pst' ? Math.round(q * 1000) / 10 : Math.round(q * 100) / 100;
    };
    const ut = { id: n.id, tekst: n.tekst, enhet: n.enhet, formel: n.formel, denne: verdi('denne') };
    ut.endring = {};
    for (const c of cmps) {
      ut[c] = verdi(c);
      ut.endring[c] = ut.denne !== null && ut[c] !== null ? Math.round((ut.denne - ut[c]) * 100) / 100 : null;
    }
    return ut;
  });
}

async function main() {
  const a = argumenter(process.argv.slice(2));
  if (typeof a.client !== 'string') throw bruk('Angi --client "klient".');
  const hittil = a.hittil === true;
  const p = tolkPeriode(typeof a.periode === 'string' ? a.periode : '', hittil);
  const cmps = (typeof a.sammenlign === 'string' ? a.sammenlign : 'forrige,ifjor').split(',').map((s) => s.trim().toLowerCase()).filter(Boolean);
  for (const c of cmps) if (!SAMMENLIGNINGER.includes(c)) throw bruk(`Ukjent sammenligning «${c}» (forrige, ifjor, budsjett).`);
  const unike = [...new Set(cmps)];
  let vesentlighet = null;
  if (a.vesentlighet !== undefined) { vesentlighet = tall(a.vesentlighet); if (!(vesentlighet > 0)) throw bruk('--vesentlighet må være et beløp > 0.'); }
  let terskel = null;
  if (a['terskel-pst'] !== undefined) { terskel = tall(a['terskel-pst']); if (!(terskel > 0)) throw bruk('--terskel-pst må være et tall > 0.'); }
  let bagatell = null;
  if (a.bagatell !== undefined) { bagatell = tall(a.bagatell); if (!(bagatell >= 0)) throw bruk('--bagatell må være et beløp ≥ 0.'); }

  const c = await connect(a.client);
  const merknader = [];
  const idag = new Date().toISOString().slice(0, 10);
  if (p.til >= idag) merknader.push(`Perioden er ikke avsluttet (slutter ${p.til}) – tallene gjelder det som er bokført nå.`);

  // ── Kolonner ──────────────────────────────────────────────────────────────
  const vinduer = { denne: p };
  if (unike.includes('forrige')) vinduer.forrige = vindu(nesteMnd(p.fraM, -p.mnd), p.mnd);
  if (unike.includes('ifjor')) vinduer.ifjor = vindu(nesteMnd(p.fraM, -12), p.mnd);
  const raa = {}, navn = new Map();
  for (const [id, v] of Object.entries(vinduer)) {
    raa[id] = await saldo(c, v);
    for (const [k, x] of raa[id]) if (!navn.has(k) || id === 'denne') navn.set(k, x.navn);
  }
  const kolonner = [{ id: 'denne', tekst: p.tekst[0].toUpperCase() + p.tekst.slice(1), fra: p.fra, til: p.til, tilEksklusiv: p.tilEksklusiv, balansedato: p.til, status: 'ok' }];
  for (const id of unike) {
    if (id === 'budsjett') continue;
    const v = vinduer[id];
    kolonner.push({ id, tekst: `${id === 'forrige' ? 'Forrige periode' : 'I fjor'} (${v.tekst})`, fra: v.fra, til: v.til, tilEksklusiv: v.tilEksklusiv, balansedato: v.til, status: 'ok' });
  }
  let bud = null;
  if (unike.includes('budsjett')) {
    bud = await budsjett(c, p);
    const k = { id: 'budsjett', tekst: `Budsjett (${p.tekst})`, fra: p.fra, til: p.til, tilEksklusiv: p.tilEksklusiv, balansedato: null, status: bud.status };
    if (bud.grunn) k.grunn = bud.grunn;
    if (bud.fortegn) k.fortegn = bud.fortegn;
    kolonner.push(k);
    if (bud.status !== 'ok') merknader.push(`Budsjett ikke funnet: ${bud.grunn}.`);
  }
  const ordnet = unike.filter((x) => x !== 'budsjett' || bud?.status === 'ok');
  // Kolonner som ikke finnes (budsjett ikke funnet) står som null i radene.
  const radCmps = unike;

  // ── Vesentlighet ──────────────────────────────────────────────────────────
  let vesentlighetKilde = 'angitt';
  if (vesentlighet === null) {
    const v12 = vindu(nesteMnd(p.fraM, p.mnd - 12), 12);
    const r12 = p.mnd === 12 && p.fraM.endsWith('-01') ? raa.denne : await saldo(c, v12);
    const inntekt = rund(-[...r12].filter(([k]) => k >= 3000 && k <= 3999).reduce((s, [, x]) => s + x.endring, 0));
    vesentlighet = Math.max(5000, Math.round(inntekt * 0.005));
    vesentlighetKilde = `standard: høyeste av 5 000 og 0,5 % av driftsinntektene ${v12.tekst} (${kr(inntekt)})`;
  }
  const terskelPst = terskel !== null ? { forrige: terskel, ifjor: terskel, budsjett: terskel } : { ...STD_TERSKEL };
  const t = { vesentlighet, vesentlighetKilde, terskelPst, bagatell: bagatell ?? Math.round(vesentlighet / 2) };

  // ── Beregning ─────────────────────────────────────────────────────────────
  const res = {}, bal = {};
  for (const id of Object.keys(raa)) {
    res[id] = beregn(RESULTAT, raa[id], (x) => x.endring);
    bal[id] = beregnBalanse(raa[id]);
  }
  if (bud?.status === 'ok') {
    const bRaa = new Map([...bud.kontoer].map(([k, x]) => [k, { endring: x }]));
    res.budsjett = beregn(RESULTAT, bRaa, (x) => x.endring);
  }
  const resultatRader = rader(RESULTAT, res, radCmps, navn, t, 'resultat');
  const balanseRader = rader(BALANSE, bal, radCmps.filter((x) => x !== 'budsjett'), navn, t, 'balanse');

  const flagg = [];
  for (const [del, rr] of [['resultat', resultatRader], ['balanse', balanseRader]]) {
    for (const r of rr) {
      for (const [cmp, x] of Object.entries(r.avvik)) {
        if (!x.flagg.length) continue;
        flagg.push({ del, nivaa: r.nivaa, id: r.id, konto: r.konto, tekst: r.tekst, sammenligning: cmp, denne: r.denne, verdi: r[cmp], avvik: x.kr, avvikPst: x.pst, gunstig: x.gunstig, flagg: x.flagg });
      }
    }
  }
  flagg.sort((x, y) => Math.abs(y.avvik) - Math.abs(x.avvik));

  // ── Kontroller ────────────────────────────────────────────────────────────
  const sumEndring = rund([...raa.denne].filter(([k]) => k >= 3000).reduce((s, [, x]) => s + x.endring, 0));
  const red = res.denne.linjer.resultatEtterDisponeringer;
  const kRes = { resultatEtterDisponeringer: red, minusSumEndring3000_8999: rund(-sumEndring), differanse: rund(red + sumEndring), ok: Math.abs(red + sumEndring) < 0.01 };
  const kb = bal.denne.kontroll;
  const differanse = rund(kb.eiendeler - kb.egenkapitalOgGjeldBokfort);
  const rest = rund(differanse - kb.resultatHittil - kb.ibAlle);
  const kBal = {
    balansedato: p.til, eiendeler: kb.eiendeler, egenkapitalOgGjeldBokfort: kb.egenkapitalOgGjeldBokfort, differanse,
    resultatHittil: kb.resultatHittil, udisponertTidligereAar: kb.ibAlle, rest, ok: Math.abs(rest) < 1, tidligereAarDisponert: Math.abs(kb.ibAlle) < 1,
  };
  if (!kRes.ok) merknader.push(`Resultatkontroll: oppstillingen avviker ${kr(kRes.differanse)} fra −(sum endring 3000–8999).`);
  if (!kBal.ok) merknader.push(`Balansekontroll: ${kr(rest)} er ikke forklart av resultat hittil og udisponert fra tidligere år.`);
  if (!kBal.tidligereAarDisponert) merknader.push(`Resultat fra tidligere år er ikke disponert fullt ut: ${kr(kb.ibAlle)} (balansekontoene går ikke i null per 1.1. – sjekk årsoppgjørsdisposisjonen, 88xx–89xx mot 20xx).`);

  const ut = {
    versjon: 1, kommando: 'regnskap', klient: c.company.name, orgnr: c.company.organizationNumber ?? '', klientId: c.company.id,
    laget: new Date().toISOString(),
    periode: a.periode, periodeType: p.type, hittil, periodeTekst: p.tekst,
    kolonner,
    fortegn: 'Inntekter og kostnader vises som positive tall; resultat = inntekter − kostnader. Eiendeler, egenkapital og gjeld vises positive. ' +
      'Avvik = denne − sammenligning; avvik % = avvik / |sammenligning| × 100.',
    terskler: t,
    resultat: { rader: resultatRader },
    balanse: { rader: balanseRader },
    nokkeltall: nokkeltall(res, bal, radCmps),
    flagg,
    kontroll: { resultat: kRes, balanse: kBal },
    merknader,
  };

  if (a.json && typeof a.ut !== 'string') { console.log(JSON.stringify(ut, null, 1)); return; }
  const fil = join(utmappe(a.ut, 'regnskap', `${a.periode}${hittil ? '-hittil' : ''}`), 'regnskap.json');
  writeFileSync(fil, JSON.stringify(ut, null, 1));
  skrivKonsoll(ut, ordnet, fil);
}

function skrivKonsoll(ut, ordnet, fil) {
  const cmps = ordnet;
  const kolTekst = (id) => ut.kolonner.find((k) => k.id === id)?.tekst ?? id;
  console.log(`${ut.klient} – resultat og balanse ${ut.periodeTekst}, ${ut.kolonner[0].fra}–${ut.kolonner[0].til}` +
    `${cmps.length ? `, mot ${cmps.map((x) => kolTekst(x).replace(/^./, (s) => s.toLowerCase())).join(' og ')}` : ''}.`);
  console.log(`Fortegn: inntekter og kostnader positive, resultat = inntekter − kostnader. Avvik = denne − sammenligning. ` +
    `* = |avvik| ≥ V ${kr(ut.terskler.vesentlighet)} eller |avvik %| ≥ ${cmps.map((x) => `${ut.terskler.terskelPst[x]} (${x})`).join('/') || '–'} og ≥ ${kr(ut.terskler.bagatell)}.`);
  const B = 34, N = 12;
  const hode = (tittel, liste) => `${tittel.padEnd(B)}${'Denne'.padStart(N)}${liste.map((x) => `${x.padStart(N)}${'avvik'.padStart(N)}${'%'.padStart(8)}  `).join('')}`;
  const linje = (r, liste) => {
    const deler = liste.map((x) => {
      const a = r.avvik[x];
      return `${kr(r[x]).padStart(N)}${(a ? kr(a.kr) : '').padStart(N)}${(a ? pst(a.pst) : '').padStart(8)}${a?.flagg.length ? ' *' : '  '}`;
    }).join('');
    return `${(r.nivaa === 'sum' ? r.tekst.toUpperCase() : r.tekst).slice(0, B - 1).padEnd(B)}${kr(r.denne).padStart(N)}${deler}`;
  };
  console.log(`\n${hode('Resultat', cmps)}`);
  for (const r of ut.resultat.rader) if (r.nivaa !== 'konto') console.log(linje(r, cmps));
  const bcmps = cmps.filter((x) => x !== 'budsjett');
  console.log(`\n${hode(`Balanse per ${ut.kontroll.balanse.balansedato}`, bcmps)}`);
  for (const r of ut.balanse.rader) if (r.nivaa !== 'konto' || r.konto === null) console.log(linje(r, bcmps));

  const kf = ut.flagg.filter((f) => f.nivaa === 'konto');
  if (kf.length) {
    console.log(`\nFlaggede kontoer (${Math.min(15, kf.length)} av ${kf.length}, størst avvik først):`);
    for (const f of kf.slice(0, 15)) {
      console.log(`  ${String(f.konto ?? '').padEnd(5)} ${f.tekst.slice(0, 30).padEnd(30)} ${f.sammenligning.padEnd(9)}` +
        `${kr(f.denne).padStart(N)}${kr(f.verdi).padStart(N)}${kr(f.avvik).padStart(N)}${pst(f.avvikPst).padStart(8)}  ${f.flagg.join(',')}` +
        `${f.gunstig === true ? ' (gunstig)' : f.gunstig === false ? ' (ugunstig)' : ''}`);
    }
  } else console.log('\nIngen kontoer flagget.');

  const nt = ut.nokkeltall.map((n) => {
    const v = (x) => (x === null || x === undefined ? '–' : n.enhet === 'pst' ? `${pst(x)} %` : String(x).replace('.', ','));
    return `${n.tekst} ${v(n.denne)}${cmps.length ? ` (${cmps.map((x) => `${x} ${v(n[x])}`).join(', ')})` : ''}`;
  });
  console.log(`\nNøkkeltall: ${nt.join(' · ')}`);
  const kr2 = ut.kontroll.resultat, kb = ut.kontroll.balanse;
  console.log(`Kontroll: resultat = −(sum endring 3000–8999) ${kr2.ok ? 'OK' : `AVVIK ${kr(kr2.differanse)}`}; ` +
    `eiendeler − (EK + gjeld) ${kr(kb.differanse)} = resultat hittil ${kr(kb.resultatHittil)} + udisponert tidligere år ${kr(kb.udisponertTidligereAar)}` +
    ` ${kb.ok ? 'OK' : `AVVIK ${kr(kb.rest)}`}.`);
  console.log(`V: ${kr(ut.terskler.vesentlighet)} (${ut.terskler.vesentlighetKilde}).`);
  if (ut.merknader.length) console.log(`Merknader:\n- ${ut.merknader.join('\n- ')}`);
  console.log(`Skrevet: ${fil}`);
}

main().catch((e) => { console.error(e.bruk ? e.message : `Feil: ${redactText(kortFeil(e))}`); process.exitCode = 1; });
