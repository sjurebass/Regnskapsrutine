// Notater og kontroller til avstemmingsmodulen (Silfer-PDF): kontroll av mva-utkast mot hovedbok, avstemming av 2740
// og vurdering av åpne poster i kunde- og leverandørreskontro. Alt hentes lesende med hentAlle/hentEn (fields= påkrevd,
// ingen personfelt). Faglige vurderinger (forklaring av saldo, tiltak per motpart) gis inn av regnskapsføreren eller
// Claude etter avklaring – aldri gjettet. Logo og farger følger silfer-rapport (.claude/skills/silfer-rapport/assets).

import { existsSync, readFileSync, writeFileSync, mkdtempSync, rmSync, copyFileSync, statSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { execFileSync } from 'node:child_process';
import { hentAlle, hentEn, forsok, lagTermin, leggTilDager, leggTilMnd } from './felles.js';

// ── format og PDF ─────────────────────────────────────────────────────────────

export const kr = (x) => (x == null ? '–' : new Intl.NumberFormat('nb-NO', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(x).replace(/\u2212/g, '-'));
export const hel = (x) => (x == null ? '–' : new Intl.NumberFormat('nb-NO', { maximumFractionDigits: 0 }).format(Math.round(x) + 0).replace(/\u2212/g, '-'));
export const datoNo = (d) => (d ? d.slice(0, 10).split('-').reverse().join('.') : '–');
export const esc = (s) => String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const oere = (x) => Math.round((x ?? 0) * 100);
const MND = ['januar', 'februar', 'mars', 'april', 'mai', 'juni', 'juli', 'august', 'september', 'oktober', 'november', 'desember'];
export const mndNavn = (ym) => MND[Number(ym.slice(5, 7)) - 1];

// tripletex-api/src/mva → repo-rota → .claude/skills/silfer-rapport/assets/silfer_logo.png
const LOGO = join(dirname(fileURLToPath(import.meta.url)), '..', '..', '..', '.claude', 'skills', 'silfer-rapport', 'assets', 'silfer_logo.png');
const NETTLESERE = [
  'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
  'C:/Program Files/Microsoft/Edge/Application/msedge.exe',
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
];

const CSS = `@page { size: A4; margin: 14mm 13mm; } body { font-family: 'Segoe UI', Arial, sans-serif; color: #1a1a1a; font-size: 9pt; }
.topp { display: flex; align-items: center; gap: 14px; border-bottom: 2px solid #1B2E28; padding-bottom: 8px; } .topp img { height: 44px; }
h1 { font-size: 16pt; margin: 0; color: #1B2E28; } .under { color: #6B7280; font-size: 8.8pt; } h2 { font-size: 11pt; color: #1B2E28; margin: 14px 0 5px; } h3 { font-size: 9.8pt; color: #2D5A4A; margin: 10px 0 4px; }
table { width: 100%; border-collapse: collapse; margin-bottom: 5px; } th { background: #1B2E28; color: #fff; text-align: left; font-weight: 600; padding: 3px 5px; font-size: 8.4pt; }
td { padding: 2.5px 5px; border-bottom: 1px solid #D1D5DB; vertical-align: top; } .n { text-align: right; white-space: nowrap; }
.ok { color: #1B6E3D; background: #F0FAF4; font-weight: 600; text-align: center; } .avvik { color: #C0392B; background: #FFF0F0; font-weight: 600; text-align: center; }
.merk { color: #6B7280; font-size: 8pt; } .konkl { border: 1px solid #2D5A4A; background: #F0FAF4; padding: 8px 10px; margin-top: 8px; }
.varsel { border: 1px solid #D4760A; background: #FFF8EC; padding: 8px 10px; margin-top: 8px; } .liten td, .liten th { font-size: 7.6pt; padding: 1.5px 4px; }
.sideskift { page-break-before: always; } .nw { white-space: nowrap; } .bunn { margin-top: 14px; text-align: center; color: #6B7280; font-size: 8pt; }`;

/** Silfer-side: logo, tittel, undertittel og innhold (HTML). */
export function side(tittel, under, innhold, bunntekst) {
  const logo = existsSync(LOGO) ? `<img src="data:image/png;base64,${readFileSync(LOGO).toString('base64')}">` : '';
  return `<!doctype html><html lang="nb"><head><meta charset="utf-8"><title>${esc(tittel)}</title><style>${CSS}</style></head><body>
<div class="topp">${logo}<div><h1>${esc(tittel)}</h1><div class="under">${esc(under)}</div></div></div>
${innhold}
<div class="bunn">${esc(bunntekst)}</div></body></html>`;
}

/** Skriver HTML til PDF med Edge/Chrome headless. Returnerer antall byte. */
export function lagPdf(html, fil) {
  const exe = NETTLESERE.find((p) => existsSync(p));
  if (!exe) throw new Error('Fant verken Edge eller Chrome for PDF-utskrift.');
  const mappe = mkdtempSync(join(tmpdir(), 'silfer-notat-'));
  // Skrives først til en midlertidig fil: finnes målfila fra før, skal en feilet utskrift aldri gi den gamle fila tilbake.
  const tmpPdf = join(mappe, 'notat.pdf');
  try {
    const htmlFil = join(mappe, 'notat.html');
    writeFileSync(htmlFil, html);
    // Egen profil (--user-data-dir): ellers overtar en Edge som allerede kjører kallet og avslutter uten å skrive PDF-en.
    // Edge kan avslutte med feilkode selv når PDF-en er skrevet – derfor sjekkes filen i stedet.
    try { execFileSync(exe, ['--headless=new', '--disable-gpu', '--no-pdf-header-footer', `--user-data-dir=${join(mappe, 'profil')}`, `--print-to-pdf=${tmpPdf}`, pathToFileURL(htmlFil).href], { stdio: 'ignore', timeout: 120_000 }); } catch { /* sjekkes under */ }
    // Edge-starteren kan avslutte før utskriften er ferdig (kalibrering 06.10.2026): vent til PDF-en finnes og har stabil størrelse.
    const vent = (ms) => Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, ms);
    let forrige = -1;
    for (let i = 0; i < 240; i++) {
      const n = existsSync(tmpPdf) ? statSync(tmpPdf).size : -1;
      if (n > 0 && n === forrige) break;
      forrige = n; vent(500);
    }
    if (!existsSync(tmpPdf) || statSync(tmpPdf).size === 0) throw new Error(`PDF ble ikke laget: ${fil}`);
    copyFileSync(tmpPdf, fil);
  } finally {
    // Edge kan holde profilmappa en stund etter utskriften – en mappe som ikke lar seg slette, stopper ikke notatet.
    try { rmSync(mappe, { recursive: true, force: true, maxRetries: 10, retryDelay: 500 }); } catch { /* ligger igjen i %TEMP% */ }
  }
  return readFileSync(fil).length;
}

const saldo = async (b, konto, tilEks, fra) => (await hentAlle(b, '/balanceSheet', { dateFrom: fra, dateTo: tilEks, accountNumberFrom: konto, accountNumberTo: konto, fields: 'balanceIn,balanceChange,balanceOut' }))[0] ?? { balanceIn: 0, balanceChange: 0, balanceOut: 0 };

// ── kontroll av mva-utkast mot hovedbok ──────────────────────────────────────

/**
 * Utkastet/meldingen for terminen (`/vatReturns/>vatTerm`) mot en egen summering av posteringene per mva-kode,
 * Tripletex' terminbeløp, forhåndssjekk, fortegn mot expectedSign (merknad?), oppgjørsbilag og 27xx per terminslutt.
 */
export async function kontrollUtkast(b, aar, termin) {
  const t = lagTermin(aar, termin);
  const vt = new Map((await hentAlle(b, '/ledger/vatType', { fields: 'id,number' })).map((v) => [v.id, v.number]));
  // >vatTerm og vatTermAmount må kalles uten fields (eksplisitte fields tømmer linjene) – dokumentert unntak.
  // >vatTerm og validateCreate teller terminer fra første rad i /vatTermSizeSettings, ikke fra 1. januar (registrert fra
  // 01.05 gir vatTerm 1 = mai–juni). status og vatTermAmount bruker kalendernummer. Finn vatTerm-nummeret på startdato.
  const hentVatTerm = async (n) => (await forsok(() => b.request('/vatReturns/>vatTerm', { query: { year: aar, vatTerm: n } }))).data?.value ?? null;
  let nr = termin;
  let u = (await hentVatTerm(nr)) ?? {};
  for (let n = 1; u.start !== t.start && n <= 12; n++) {
    const x = await hentVatTerm(n);
    if (!x) break;
    if (x.start === t.start) { nr = n; u = x; }
  }
  if (u.start !== t.start) throw new Error(`Fant ingen mva-termin som starter ${t.start} i /vatReturns/>vatTerm – sjekk /vatTermSizeSettings.`);
  const termBelop = (await b.request('/vatReturnsOverview/vatTermAmount', { query: { year: aar, term: termin } }))?.value ?? null;
  const validering = u.id ? null : (await forsok(() => hentEn(b, '/vatReturns/validateCreate', { year: aar, vatTerm: nr, fields: 'incompleteVouchers,accountingPeriodClosed,beforeStartBalance,invalidDate,alreadyExists,success' }))).data ?? null;

  const linjer = (u.vatGroups ?? []).flatMap((g) => g.lines ?? []).map((l) => ({
    kode: String(vt.get(l.vatType?.id) ?? l.standardCode), grunnlag: l.basis ?? 0, mva: l.vatAmount ?? 0,
    forventet: l.expectedSign ?? null, merknad: l.structuredComment || l.userComment || null,
  }));
  const post = await hentAlle(b, '/ledger/posting', { dateFrom: t.start, dateTo: t.D, fields: 'amount,amountGross,vatType(number)' });
  const hb = new Map();
  for (const p of post) {
    const n = p.vatType?.number; if (!n || n === '0') continue;
    const x = hb.get(n) ?? { g: 0, v: 0 }; x.g += p.amount; x.v += (p.amountGross ?? 0) - (p.amount ?? 0); hb.set(n, x);
  }
  const koder = [...new Set([...hb.keys(), ...linjer.map((l) => l.kode)])].sort((a, c) => Number(a) - Number(c));
  const perKode = koder.map((kode) => {
    const h = hb.get(kode) ?? { g: 0, v: 0 };
    const l = linjer.filter((x) => x.kode === kode);
    const snudd = l.some((x) => x.grunnlag > 0) && l.some((x) => x.grunnlag < 0); // f.eks. 86: utgående og inngående linje
    const hbMva = Math.trunc(-h.v) || 0;
    const mMva = l.reduce((s, x) => s + x.mva, 0);
    return {
      kode, snudd, hbGrunnlag: snudd ? Math.abs(Math.trunc(h.g)) : Math.trunc(-h.g), hbMva,
      mGrunnlag: snudd ? Math.max(...l.map((x) => Math.abs(x.grunnlag))) : l.reduce((s, x) => s + x.grunnlag, 0), mMva, avvik: hbMva - mMva,
    };
  });
  const fortegn = linjer.filter((l) => l.forventet && l.mva !== 0 && (l.mva > 0) !== (l.forventet === 'POSITIVE'))
    .map((l) => ({ kode: l.kode, mva: l.mva, forventet: l.forventet, merknad: l.merknad }));

  let oppgjor = null;
  if (u.voucher?.id) {
    const v = await hentEn(b, `/ledger/voucher/${u.voucher.id}`, { fields: 'number,date,postings(account(number),amount)' });
    const s27 = await hentAlle(b, '/balanceSheet', { dateFrom: `${aar}-01-01`, dateTo: t.D, accountNumberFrom: 2700, accountNumberTo: 2749, fields: 'account(number),balanceOut' });
    oppgjor = { bilag: v.number, dato: v.date, poster: v.postings.map((p) => ({ konto: p.account?.number, belop: p.amount })),
      rest27xx: s27.filter((x) => x.account?.number < 2740 && Math.abs(x.balanceOut) >= 0.005).map((x) => ({ konto: x.account.number, ub: x.balanceOut })),
      ub2740: s27.find((x) => x.account?.number === 2740)?.balanceOut ?? 0 };
  }
  const status = (await forsok(() => hentEn(b, '/vatReturns/status', { year: aar, term: termin, reportType: 'GENERAL_INDUSTRY', fields: 'vatReturns2022Id,altinnPaymentAmount,deliveryStatus(status,time),paymentStatus(status,remainingAmount)' }))).data ?? null;
  const betaling = u.id ? (await forsok(() => hentEn(b, `/vatReturns/${u.id}/paymentInfo`, { fields: 'kid,amount,dueDate' }))).data ?? null : null;
  const sumHb = perKode.reduce((s, k) => s + k.hbMva, 0);
  return {
    termin: t, vatTermNr: nr, utkast: { id: u.id ?? 0, status: u.status ?? null, aaBetale: u.totalAmountVatToPay ?? null, lukket: u.closedDate ?? null },
    termBelop, sumHovedbok: sumHb, validering, perKode, fortegn, oppgjor, status, betaling,
    ok: perKode.every((k) => k.avvik === 0) && sumHb === termBelop && (u.totalAmountVatToPay == null || u.totalAmountVatToPay === termBelop) && fortegn.every((f) => f.merknad),
  };
}

function kontrollTabell(k) {
  const rader = k.perKode.map((x) => `<tr><td>${x.kode}${x.snudd ? ' (ut og inn)' : ''}</td><td class="n">${hel(x.hbGrunnlag)}</td><td class="n">${hel(x.hbMva)}</td><td class="n">${hel(x.mGrunnlag)}</td><td class="n">${hel(x.mMva)}</td><td class="${x.avvik === 0 ? 'ok' : 'avvik'}">${x.avvik === 0 ? 'OK' : hel(x.avvik)}</td></tr>`).join('');
  const f = k.fortegn.length ? `Linjer med fortegn motsatt av det Skatteetaten forventer: ${k.fortegn.map((x) => `kode ${x.kode} (${x.merknad ? `merknad «${esc(x.merknad)}»` : 'MANGLER MERKNAD'})`).join(', ')}.` : 'Ingen linjer med uventet fortegn.';
  const o = k.oppgjor ? ` Oppgjørsbilag ${k.oppgjor.bilag} (${datoNo(k.oppgjor.dato)}) nullstiller 27xx mot 2740${k.oppgjor.rest27xx.length ? ` – NB: rest på ${k.oppgjor.rest27xx.map((r) => r.konto).join(', ')}` : ''}.` : '';
  return `<table><tr><th>Kode</th><th class="n">Grunnlag hovedbok</th><th class="n">Mva hovedbok</th><th class="n">Grunnlag melding</th><th class="n">Mva melding</th><th>Avvik</th></tr>${rader}
<tr><td><b>Sum</b></td><td></td><td class="n"><b>${hel(k.sumHovedbok)}</b></td><td></td><td class="n"><b>${hel(k.utkast.aaBetale ?? k.termBelop)}</b></td><td class="${k.ok ? 'ok' : 'avvik'}">${k.ok ? 'OK' : 'SJEKK'}</td></tr></table>
<div class="merk">Egen summering av posteringene per mva-kode mot ${k.utkast.id ? 'meldingen' : 'utkastet'} og Tripletex' terminbeløp (${hel(k.termBelop)}). ${f}${o}</div>`;
}

// ── avstemming av 2740 ───────────────────────────────────────────────────────

/**
 * Notat for 2740 per månedsslutt i terminen. `forklaringer` = { 'ÅÅÅÅ-MM': { dokumentert, tekst } } – den faglige
 * forklaringen av saldoen gis inn; uten den vises måneden som ikke dokumentert.
 */
export async function notat2740(b, { aar, termin, forklaringer = {}, kundenavn, orgnr }) {
  const t = lagTermin(aar, termin);
  const idag = new Date().toISOString().slice(0, 10);
  const ib = (await saldo(b, 2740, `${aar}-01-02`, `${aar}-01-01`)).balanceIn;
  const maaneder = [];
  for (const m of t.maaneder) {
    const D = leggTilMnd(`${m}-01`, 1);
    const ub = (await saldo(b, 2740, D, `${aar}-01-01`)).balanceOut;
    const f = forklaringer[m];
    maaneder.push({ m, sisteDag: leggTilDager(D, -1), ub, dokumentert: f?.dokumentert ?? null, tekst: f?.tekst ?? null, diff: f ? Math.round((ub - f.dokumentert) * 100) / 100 : null });
  }
  const post = (await hentAlle(b, '/ledger/posting', { dateFrom: `${aar}-01-01`, dateTo: leggTilDager(idag, 1), accountNumberFrom: 2740, accountNumberTo: 2740, fields: 'date,amount,voucher(number,voucherType(name))' }))
    .sort((a, c) => a.date.localeCompare(c.date) || (a.voucher?.number ?? 0) - (c.voucher?.number ?? 0));
  const status = await hentAlle(b, '/vatReturns/status/list', { startDate: `${aar}-01-01`, endDate: `${aar + 1}-01-01`, reportType: 'GENERAL_INDUSTRY', fields: 'term,vatReturns2022Id,voucherNumber,altinnPaymentAmount,deliveryStatus(status,time),paymentStatus(status,remainingAmount)' });
  const krav = (await forsok(() => hentAlle(b, '/claimsAndPayments', { year: aar, fields: 'claimIdentifier,claimType,outstandingAmount,dueDate,periodDescription' }))).data ?? null;
  const kontroll = await kontrollUtkast(b, aar, termin);

  const typeTekst = (n) => ({ 'OCR giro': 'Innbetaling/utbetaling Skatteetaten', 'Mva-melding': 'Oppgjør mva-melding', 'Leverandørfaktura': 'Leverandørfaktura' }[n] ?? (n || 'Manuelt bilag'));
  let lop = ib;
  const bevRader = post.map((p) => { lop += p.amount; return `<tr><td>${datoNo(p.date)}</td><td>${p.voucher?.number ?? ''}</td><td>${typeTekst(p.voucher?.voucherType?.name)}</td><td class="n">${kr(p.amount)}</td><td class="n">${kr(Math.round(lop * 100) / 100)}</td></tr>`; }).join('');
  const lev = { RECEIPT_RECEIVED: 'Levert (kvittering mottatt)', WAITING_FOR_REPLY: 'Sendt – venter på kvittering', NOT_SENT: 'Opprettet, ikke sendt', NOT_STARTED: 'Ikke opprettet' };
  const bet = { AMOUNT_CREDITED: 'Utbetalt', PAID: 'Betalt', NOT_PAID: 'Ikke betalt', NOT_STARTED: '–' };
  // status/list teller som >vatTerm (fra første terminlengde-rad), ikke kalendernummer – se kontrollUtkast.
  const forskyvning = termin - kontroll.vatTermNr;
  const termRader = status.map((s) => ({ ...s, term: s.term + forskyvning })).filter((s) => s.term <= termin).map((s) => {
    const denne = s.term === termin;
    const belop = s.altinnPaymentAmount ?? (denne ? kontroll.termBelop : null);
    const levTekst = `${lev[s.deliveryStatus?.status] ?? s.deliveryStatus?.status ?? '–'} ${s.deliveryStatus?.time ? datoNo(s.deliveryStatus.time) : ''}${denne && s.voucherNumber ? `, oppgjørsbilag ${s.voucherNumber}` : ''}`;
    const betTekst = `${bet[s.paymentStatus?.status] ?? s.paymentStatus?.status ?? '–'}${denne && kontroll.betaling?.dueDate ? `, forfall ${datoNo(kontroll.betaling.dueDate)}${kontroll.betaling.kid ? `, KID ${kontroll.betaling.kid}` : ''}` : ''}`;
    return `<tr><td class="nw">Termin ${s.term}</td><td class="n">${hel(belop)}</td><td>${levTekst}</td><td>${betTekst}</td></tr>`;
  }).join('');
  const mvaKrav = krav?.filter((x) => /mva|merverdi/i.test(`${x.claimType} ${x.periodDescription}`) && Math.abs(x.outstandingAmount ?? 0) >= 1) ?? null;
  const kravRader = krav == null ? '<tr><td>Skattekontoen kunne ikke leses</td><td></td></tr>'
    : (mvaKrav.length ? mvaKrav.map((x) => `<tr><td>${esc(x.claimType)} ${esc(x.periodDescription)}</td><td class="n">${kr(x.outstandingAmount)}</td></tr>`).join('') : '<tr><td>Åpne mva-krav</td><td class="n">Ingen</td></tr>');
  const avstemt = maaneder.every((x) => x.diff === 0);
  const mRader = maaneder.map((x) => `<tr><td>${datoNo(x.sisteDag)}</td><td class="n">${kr(x.ub)}</td><td class="n">${kr(x.dokumentert)}</td><td class="n">${kr(x.diff)}</td><td>${esc(x.tekst ?? 'Ikke dokumentert')}</td><td class="${x.diff === 0 ? 'ok' : 'avvik'}">${x.diff === 0 ? 'AVSTEMT' : 'IKKE AVSTEMT'}</td></tr>`).join('');

  const innhold = `<h2>Konklusjon</h2>
<table><tr><th>Dato</th><th class="n">Saldo hovedbok</th><th class="n">Dokumentert</th><th class="n">Differanse</th><th>Dokumentasjon</th><th>Status</th></tr>${mRader}</table>
<h2>Bevegelser på 2740 i ${aar}</h2>
<table><tr><th>Dato</th><th>Bilag</th><th>Type</th><th class="n">Beløp</th><th class="n">Saldo</th></tr><tr><td>01.01.${aar}</td><td></td><td>Inngående balanse</td><td></td><td class="n">${kr(ib)}</td></tr>${bevRader}</table>
<div class="merk">Debet (+) er tilgode hos Skatteetaten, kredit (−) er skyld eller innbetaling fra Skatteetaten.</div>
<h2>Mva-meldinger ${aar}</h2>
<table><tr><th>Termin</th><th class="n">Beløp (+ betale / − tilgode)</th><th>Levering</th><th>Betaling</th></tr>${termRader}</table>
<div class="merk">Kvitteringene er registrert i Tripletex. PDF-kvitteringen kan ikke hentes gjennom API-et (manglende tilgang) og legges ved separat.</div>
<h2>Skattekonto per ${datoNo(idag)}</h2><table><tr><th>Krav</th><th class="n">Utestående</th></tr>${kravRader}</table>
<h2>Kontroll av mva-melding termin ${termin} mot hovedbok</h2>${kontrollTabell(kontroll)}
<div class="konkl"><b>Konto 2740 er ${avstemt ? '' : 'ikke '}avstemt per ${maaneder.map((x) => datoNo(x.sisteDag)).join(' og ')}.</b> ${maaneder.map((x) => `${datoNo(x.sisteDag)}: ${esc(x.tekst ?? 'mangler forklaring')}`).join(' ')}</div>`;
  const html = side('Avstemming 2740 Oppgjørskonto merverdiavgift', `${kundenavn} | Org.nr. ${orgnr ?? ''} | Termin ${termin} (${t.maaneder.map(mndNavn).join('–')} ${aar}) | ${datoNo(idag)}`, innhold, `Silfer AS · Avstemming 2740 · ${datoNo(idag)}`);
  return { html, maaneder, avstemt, kontroll, filnavn: `Avstemming 2740 ${t.maaneder.map(mndNavn).join('-')} ${aar} ${kundenavn}.pdf` };
}

// ── vurdering av åpne poster i reskontro ──────────────────────────────────────

/** Minste delmengder som går i null: hele motparten, eksakte par, deretter grupper på 3+ (inntil 16 poster per motpart). */
export function nullgrupper(poster) {
  if (poster.length > 1 && poster.reduce((s, p) => s + oere(p.amount), 0) === 0) return [poster];
  const ut = []; const brukt = new Set();
  for (const a of poster) {
    if (brukt.has(a.id)) continue;
    const c = poster.find((x) => !brukt.has(x.id) && x.id !== a.id && oere(x.amount) === -oere(a.amount));
    if (c) { brukt.add(a.id); brukt.add(c.id); ut.push([a, c]); }
  }
  let rest = poster.filter((p) => !brukt.has(p.id));
  for (let funnet = true; funnet && rest.length >= 3 && rest.length <= 16;) {
    funnet = false; let best = null;
    for (let m = 1; m < (1 << rest.length); m++) {
      const n = m.toString(2).replace(/0/g, '').length;
      if (n < 3 || (best && n >= best.n)) continue;
      let s = 0; for (let i = 0; i < rest.length; i++) if (m & (1 << i)) s += oere(rest[i].amount);
      if (s === 0) best = { m, n };
    }
    if (best) { ut.push(rest.filter((_, i) => best.m & (1 << i))); rest = rest.filter((_, i) => !(best.m & (1 << i))); funnet = true; }
  }
  return ut;
}

async function brreg(orgnr) {
  try {
    const r = await fetch(`https://data.brreg.no/enhetsregisteret/api/enheter/${orgnr}`);
    if (r.status === 404 || r.status === 410) return 'Slettet/finnes ikke';
    const j = await r.json();
    return j.konkurs ? 'Konkurs' : j.underTvangsavviklingEllerTvangsopplosning ? 'Tvangsavvikling' : j.underAvvikling ? 'Under avvikling' : 'Aktiv';
  } catch { return 'Ukjent'; }
}

/**
 * Vurdering av åpne poster per `dato` (siste dag i perioden) for 1500 og 2400. Bare poster datert i samme år vises
 * enkeltvis; eldre poster er én samlelinje («vurderes i årsoppgjøret»). Kundenavn vises i PDF-en (reskontrodokumentasjon);
 * i `data` (for --json) vises privatpersoner bare som «Privatperson <id>».
 * `vurderinger` (valgfri JSON): { konklusjon, kunder:[{motpart,vurdering,tiltak}], ufordelt:[{motpart,hva,tiltak}], leverandorer:[{motpart,hva,tiltak}], tiltak:[...] }
 */
export async function reskontroVurdering(b, { dato, vurderinger = null, kundenavn, orgnr }) {
  const aar = dato.slice(0, 4);
  const dEks = leggTilDager(dato, 1);
  const imorgen = leggTilDager(new Date().toISOString().slice(0, 10), 1);
  const F = 'id,date,amount,invoiceNumber,termOfPayment,voucher(number,voucherType(name)),customer(id,name,isPrivateIndividual,organizationNumber),supplier(id,name,isPrivateIndividual,organizationNumber)';
  const hent = (konto, d, fields = F) => hentAlle(b, '/ledger/posting/openPost', { date: d, accountNumberFrom: konto, accountNumberTo: konto, sorted: false, fields });
  const dager = (fra, til) => Math.round((new Date(til) - new Date(fra)) / 864e5);
  const res = {};
  for (const [konto, art] of [[1500, 'customer'], [2400, 'supplier']]) {
    const per = await hent(konto, dEks);
    const naa = new Set((await hent(konto, imorgen, 'id')).map((p) => p.id));
    const perMotpart = new Map();
    for (const p of per) { const id = p[art]?.id ?? 0; (perMotpart.get(id) ?? perMotpart.set(id, []).get(id)).push(p); }
    const iNull = new Set([...perMotpart.entries()].filter(([id, l]) => id && l.length > 1).flatMap(([, l]) => nullgrupper(l.filter((p) => naa.has(p.id))).flat().map((p) => p.id)));
    const poster = per.map((p) => {
      const m = p[art];
      const forfall = p.termOfPayment ?? p.date;
      const fd = dager(forfall, dato);
      const erKrav = konto === 1500 ? p.amount > 0 : p.amount < 0;
      let kat;
      if (!naa.has(p.id)) kat = erKrav ? `Betalt etter ${datoNo(dato)}` : `Utlignet etter ${datoNo(dato)}`;
      else if (iNull.has(p.id)) kat = 'Kan utlignes (går i null mot andre poster)';
      else if (Math.abs(p.amount) < 100) kat = 'Småbeløp under 100 kr';
      else if (!erKrav) kat = konto === 1500 ? 'Ufordelt innbetaling/kreditnota' : 'Betaling uten faktura';
      else if (fd <= 0) kat = `Ikke forfalt per ${datoNo(dato)}`;
      else if (fd <= 30) kat = 'Forfalt 1–30 dager';
      else if (fd <= 90) kat = konto === 1500 ? 'Forfalt 31–90 dager – purring' : 'Forfalt 31–90 dager uten betaling';
      else kat = konto === 1500 ? 'Forfalt over 90 dager – tapsvurdering' : 'Forfalt over 90 dager uten betaling';
      return { id: p.id, dato: p.date, forfall, fd, belop: p.amount, fakturanr: p.invoiceNumber ?? '', bilag: p.voucher?.number ?? '', motpartId: m?.id ?? null, motpart: m?.name ?? 'Uten motpart', privat: !!m?.isPrivateIndividual, orgnr: m?.isPrivateIndividual ? '' : (m?.organizationNumber ?? ''), aapen: naa.has(p.id), kat };
    });
    res[konto] = poster;
  }
  // Brreg-status for motparter med poster som krever oppfølging (bare inneværende år)
  const oppf = (p) => p.aapen && p.dato >= `${aar}-01-01` && !/^Betalt|^Utlignet|^Ikke forfalt|^Kan utlignes/.test(p.kat);
  const orgnrSet = new Set([...res[1500], ...res[2400]].filter((p) => oppf(p) && p.orgnr).map((p) => p.orgnr));
  const status = new Map();
  for (const o of orgnrSet) status.set(o, await brreg(o));
  const s1580 = (await saldo(b, 1580, dEks, `${aar}-01-01`)).balanceOut;

  const sum = (l) => l.reduce((s, p) => s + p.belop, 0);
  const iAar = (l) => l.filter((p) => p.dato >= `${aar}-01-01`);
  const eldre = (l) => l.filter((p) => p.dato < `${aar}-01-01`);
  const katTab = (l) => {
    const m = new Map(); for (const p of iAar(l)) { const x = m.get(p.kat) ?? { n: 0, s: 0 }; x.n++; x.s += p.belop; m.set(p.kat, x); }
    const e = eldre(l);
    return [...m].map(([k, x]) => `<tr><td>${k}</td><td class="n">${x.n}</td><td class="n">${kr(x.s)}</td></tr>`).join('')
      + (e.length ? `<tr><td><i>Poster datert før ${aar} – vurderes i årsoppgjøret</i></td><td class="n">${e.length}</td><td class="n">${kr(sum(e))}</td></tr>` : '');
  };
  // Motparter med poster som krever oppfølging, med skjønnsvurdering hvis den er gitt
  const vurdTab = (konto, liste) => {
    const per = new Map(); for (const p of res[konto].filter(oppf)) (per.get(p.motpart) ?? per.set(p.motpart, []).get(p.motpart)).push(p);
    const vmap = new Map((liste ?? []).map((v) => [v.motpart, v]));
    if (!per.size) return '<div class="merk">Ingen poster som krever oppfølging.</div>';
    return `<table><tr><th>Motpart</th><th>Brreg</th><th class="n">Åpent</th><th>Poster</th><th>Vurdering</th><th>Tiltak</th></tr>${[...per].sort((a, c) => Math.abs(sum(c[1])) - Math.abs(sum(a[1]))).map(([navn, l]) => {
      const v = vmap.get(navn);
      return `<tr><td>${esc(navn)}</td><td>${esc(status.get(l[0].orgnr) ?? '–')}</td><td class="n">${kr(sum(l))}</td><td>${[...new Set(l.map((p) => p.kat))].join('; ')}</td><td>${esc(v?.vurdering ?? v?.hva ?? 'Vurdering mangler')}</td><td>${esc(v?.tiltak ?? '')}</td></tr>`;
    }).join('')}</table>`;
  };
  const postRad = (p) => `<tr><td>${datoNo(p.dato)}</td><td>${p.bilag}</td><td>${esc(p.fakturanr)}</td><td>${esc(p.motpart)}</td><td>${datoNo(p.forfall)}</td><td class="n">${p.fd > 0 ? p.fd : ''}</td><td class="n">${kr(p.belop)}</td><td>${p.kat}</td></tr>`;
  const vedlegg = (konto, tittel) => {
    const l = [...iAar(res[konto])].sort((a, c) => a.motpart.localeCompare(c.motpart) || a.dato.localeCompare(c.dato)); const e = eldre(res[konto]);
    return `<h3>${tittel}</h3><table class="liten"><tr><th>Dato</th><th>Bilag</th><th>Fakt.nr.</th><th>Motpart</th><th>Forfall</th><th class="n">Dager</th><th class="n">Beløp</th><th>Vurdering</th></tr>${l.map(postRad).join('')}${e.length ? `<tr><td colspan="6"><i>Poster datert før ${aar} (${e.length}) – vurderes i årsoppgjøret</i></td><td class="n">${kr(sum(e))}</td><td></td></tr>` : ''}</table>`;
  };
  const v = vurderinger ?? {};
  const innhold = `<h2>Konklusjon</h2><div class="konkl">${esc(v.konklusjon ?? `Reskontroene per ${datoNo(dato)} er gjennomgått for poster datert i ${aar}. Vurdering per motpart ${vurderinger ? 'står under' : 'mangler og må fylles inn'}.`)}</div>
<h2>1500 Kundefordringer – ${res[1500].length} åpne poster per ${datoNo(dato)}, ${kr(sum(res[1500]))} kr</h2>
<table><tr><th>Kategori (poster datert ${aar})</th><th class="n">Poster</th><th class="n">Beløp</th></tr>${katTab(res[1500])}</table>
<div class="merk">«Betalt etter» = åpen per ${datoNo(dato)} og lukket i dag. Avsetning tap på kundefordringer (1580): ${kr(s1580)} kr.</div>
<h3>Kunder som krever oppfølging</h3>${vurdTab(1500, [...(v.kunder ?? []), ...(v.ufordelt ?? [])])}
<h2>2400 Leverandørgjeld – ${res[2400].length} åpne poster per ${datoNo(dato)}, ${kr(sum(res[2400]))} kr</h2>
<table><tr><th>Kategori (poster datert ${aar})</th><th class="n">Poster</th><th class="n">Beløp</th></tr>${katTab(res[2400])}</table>
<h3>Leverandører som krever oppfølging</h3>${vurdTab(2400, v.leverandorer)}
${v.tiltak?.length ? `<div class="varsel"><b>Tiltaksliste</b><br>${v.tiltak.map((x, i) => `${i + 1}. ${esc(x)}`).join('<br>')}</div>` : ''}
<div class="sideskift"></div><h2>Vedlegg: åpne poster per ${datoNo(dato)} datert i ${aar}</h2>${vedlegg(1500, '1500 Kundefordringer')}${vedlegg(2400, '2400 Leverandørgjeld')}
<div class="merk">Dager = dager forfalt per ${datoNo(dato)}.</div>`;
  const html = side('Vurdering av kunde- og leverandørreskontro', `${kundenavn} | Org.nr. ${orgnr ?? ''} | Åpne poster per ${datoNo(dato)} datert i ${aar} | Gjennomgått ${datoNo(new Date().toISOString())}`, innhold, `Silfer AS · Vurdering av reskontro · ${datoNo(new Date().toISOString())}`);
  const oppfolging = { 1500: res[1500].filter(oppf).length, 2400: res[2400].filter(oppf).length };

  // Kategorisert per konto og motpart (for --json). Poster datert i året enkeltvis, eldre poster som én sum.
  const r2 = (x) => Math.round(x * 100) / 100;
  const perKonto = (konto) => {
    const l = res[konto];
    const kategorier = {};
    for (const p of iAar(l)) { const x = (kategorier[p.kat] ??= { antall: 0, sum: 0 }); x.antall++; x.sum = r2(x.sum + p.belop); }
    const motparter = new Map();
    for (const p of l) {
      const nokkel = p.motpartId ?? 0;
      const m = motparter.get(nokkel) ?? {
        motpartId: p.motpartId, motpart: p.privat ? `Privatperson ${p.motpartId}` : p.motpart, orgnr: p.orgnr || null,
        brreg: p.orgnr ? status.get(p.orgnr) ?? null : null, antall: 0, sum: 0, tilOppfolging: 0, kategorier: [], eldre: { antall: 0, sum: 0 }, poster: [],
      };
      m.antall++; m.sum = r2(m.sum + p.belop);
      if (oppf(p)) m.tilOppfolging++;
      if (p.dato < `${aar}-01-01`) { m.eldre.antall++; m.eldre.sum = r2(m.eldre.sum + p.belop); } else {
        if (!m.kategorier.includes(p.kat)) m.kategorier.push(p.kat);
        m.poster.push({ id: p.id, dato: p.dato, forfall: p.forfall, dagerForfalt: p.fd > 0 ? p.fd : 0, belop: p.belop, fakturanr: p.fakturanr || null, bilag: p.bilag || null, kategori: p.kat });
      }
      motparter.set(nokkel, m);
    }
    const e = eldre(l);
    return {
      konto, aapnePoster: l.length, sum: r2(sum(l)), tilOppfolging: oppfolging[konto], kategorier,
      eldre: { antall: e.length, sum: r2(sum(e)) },
      motparter: [...motparter.values()].sort((a, c) => Math.abs(c.sum) - Math.abs(a.sum)),
    };
  };
  const data = { dato, aar: Number(aar), avsetning1580: r2(s1580 ?? 0), 1500: perKonto(1500), 2400: perKonto(2400) };
  return { html, oppfolging, data, antall: { 1500: res[1500].length, 2400: res[2400].length }, filnavn: `Vurdering reskontro ${datoNo(dato)} ${kundenavn}.pdf` };
}
