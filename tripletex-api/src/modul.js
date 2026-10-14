// Avstemmingsmodulen (byråkontekst): perioder, vedlegg og opplasting av dokumentasjon, pluss Tripletex' egen
// bankavstemmings-PDF (klientkontekst).
//
// tripletex.js blokkerer companyId 0 med vilje. Byråkall gjøres derfor her, med to sperrer:
//   - bare stiene i BYRAA_STIER, og bare for en klient som er navngitt med --client
//   - avstemminger (id) kontrolleres mot klientens kunde-id før noe leses eller skrives
// Opplasting skriver bare med --bekreft, leser vedleggene før og etter, og hopper over filer som alt ligger på linjen.
//
//   npm run -s modul -- perioder --client "klient" --aar 2026 --type BALANCE|VAT_GENERAL_INDUSTRY [--json]
//   npm run -s modul -- vedlegg  --client "klient" --id <avstemmings-id> [--json]
//   npm run -s modul -- linjer   --client "klient" --id <BALANCE-id> [--konto 19]
//   npm run -s modul -- sett-status --client "klient" --id <BALANCE-id> --konto <accountId> --status RECONCILED|IGNORED [--dokumentert <beløp>] [--bekreft]
//   npm run -s modul -- utlign   --client "klient" --konto 1500|2400 [--bekreft]      (lukker grupper som går i null per motpart)
//   npm run -s modul -- lukk     --client "klient" --ids <id1,id2,...> [--bekreft]    (lukker én gitt gruppe)
//   npm run -s modul -- mva-oversikt --client "klient" --id <VAT-id>                   (hovedbok/rapportert/Skatteetaten per linje)
//   npm run -s modul -- fullfor  --client "klient" --id <VAT-/BALANCE-id> [--bekreft]  (:complete bare uten avvik / åpne linjer)
//   npm run -s modul -- laas-opp --client "klient" --id <id> [--bekreft]              (:unlock – fullfør igjen etterpå)
//   npm run -s modul -- kontroll-utkast --client "klient" --aar ÅÅÅÅ --termin N [--json]  (melding/utkast mot hovedbok, fortegn, oppgjør)
//   npm run -s modul -- notat-2740 --client "klient" --aar ÅÅÅÅ --termin N [--forklaring-MM "beløp|tekst"] [--ut <mappe>]
//   npm run -s modul -- reskontro-vurdering --client "klient" --dato ÅÅÅÅ-MM-DD [--vurderinger <fil.json>] [--json] [--ut <mappe>]
//   npm run -s modul -- bankpdf  --client "klient" --konto 1920 --maaned 2026-07 [--ut <mappe>]
//   npm run -s modul -- last-opp --client "klient" --id <avstemmings-id> --ref <referenceId> --fil <sti> [--bekreft] [--erstatt]
//
// Standard --ut for PDF-er (notat-2740, reskontro-vurdering, bankpdf): %TEMP%\rr\modul-<kommando>-<periode> – aldri inne i repoet.
// reskontro-vurdering --json skriver også <ut>/reskontro-vurdering.json (poster per konto og motpart, kategorisert)
// og et kort sammendrag til konsollen. Privatpersoner vises der som «Privatperson <id>».

import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { basename, join, resolve } from 'node:path';
import { BASE_URL, authorization, resetAuth, viaKonto } from './auth.js';
import { client, connect } from './tripletex.js';
import { redact, redactText } from './privacy.js';
import { kontrollUtkast, notat2740, reskontroVurdering, lagPdf, nullgrupper } from './mva/notater.js';
import { standardUt } from './valg.js';

const BYRAA_STIER = [
  /^\/accountingOffice\/reconciliations$/,
  /^\/accountingOffice\/reconciliations\/periodsOverview$/,
  /^\/accountingOffice\/reconciliations\/\d+$/,
  /^\/accountingOffice\/reconciliations\/\d+\/(attachments|comments)$/,
  /^\/accountingOffice\/reconciliations\/\d+\/attachments\/\d+$/,
  /^\/balance\/reconciliation\/\d+\/table(\/\d+)?$/,
  /^\/vat\/reconciliation\/\d+\/overview$/,
  /^\/accountingOffice\/reconciliations\/\d+\/validations$/,
  /^\/accountingOffice\/reconciliations\/\d+\/:complete$/,
  /^\/accountingOffice\/reconciliations\/\d+\/:unlock$/,
];
// De skrivende byråkallene: opplasting av vedlegg (POST) og status på én balanselinje (PUT).
const BYRAA_SKRIV = [
  ['POST', /^\/accountingOffice\/reconciliations\/\d+\/attachments$/],
  ['PUT', /^\/balance\/reconciliation\/\d+\/table\/\d+$/],
  ['DELETE', /^\/accountingOffice\/reconciliations\/\d+\/attachments\/\d+$/], // bare via last-opp --erstatt
  ['PUT', /^\/accountingOffice\/reconciliations\/\d+\/:complete$/], // bare via fullfor --bekreft
  ['PUT', /^\/accountingOffice\/reconciliations\/\d+\/:unlock$/], // bare via laas-opp --bekreft
];
// Personfelt som modulen legger på vedlegg og kommentarer. Hentes ikke, og fjernes hvis de kommer likevel.
const PERSONFELT = new Set(['createdBy', 'uploadedBy', 'reconciledBy', 'controlledBy', 'employee']);

async function kall(path, { companyId, account, method = 'GET', query, body, form, binaer = false }) {
  const url = new URL(`${BASE_URL}${path}`);
  for (const [k, v] of Object.entries(query ?? {})) if (v !== undefined) url.searchParams.set(k, v);
  const send = async () => fetch(url, {
    method,
    headers: {
      Authorization: await authorization(companyId, account),
      Accept: binaer ? 'application/pdf, application/json' : 'application/json',
      ...(body ? { 'Content-Type': 'application/json' } : {}),
    },
    body: form ?? (body ? JSON.stringify(body) : undefined),
  });
  let res = await send();
  if (res.status === 401) { resetAuth(account); res = await send(); }
  if (!res.ok) throw new Error(`${method} ${path} feilet (${res.status}): ${await res.text()}`);
  if (res.status === 204) return null;
  return binaer ? Buffer.from(await res.arrayBuffer()) : res.json();
}

/** Kall i byråkontekst for én navngitt klient. */
function byraa(k, path, opts = {}) {
  if (!BYRAA_STIER.some((r) => r.test(path))) throw new Error(`${path}: ikke tillatt i byråkontekst – ingenting er gjort.`);
  const metode = opts.method ?? 'GET';
  if (metode !== 'GET' && !BYRAA_SKRIV.some(([m, r]) => m === metode && r.test(path))) {
    throw new Error(`${metode} ${path}: bare lesing, vedlegg og linjestatus er tillatt – ingenting er gjort.`);
  }
  return kall(path, { ...opts, companyId: 0, account: k.account });
}

/** Kall i klientens kontekst (samme som tripletex.js, men tåler binært svar). */
function klientkall(k, path, opts = {}) {
  return kall(path, { ...opts, companyId: k.id, account: k.account });
}

const utenPerson = (x) => {
  if (Array.isArray(x)) return x.map(utenPerson);
  if (!x || typeof x !== 'object') return x;
  return Object.fromEntries(Object.entries(x).filter(([k]) => !PERSONFELT.has(k)).map(([k, v]) => [k, utenPerson(v)]));
};
const vis = (x) => utenPerson(redact(x));

/** Avstemmingen, kontrollert mot klienten. Kaster hvis den tilhører en annen kunde. */
async function avstemming(k, id) {
  const r = (await byraa(k, `/accountingOffice/reconciliations/${id}`, {
    query: { fields: 'id,type,year,term,status,modifiable,customer(id)' },
  })).value;
  if (r?.customer?.id !== k.id) throw new Error(`Avstemming ${id} tilhører ikke ${k.name} – ingenting er gjort.`);
  return r;
}

async function vedleggPaa(k, id) {
  return (await byraa(k, `/accountingOffice/reconciliations/${id}/attachments`, {
    query: { fields: 'id,reconciliationId,referenceId,uploadedAt,document(id,fileName)' },
  })).values ?? [];
}

async function kommentarerPaa(k, id) {
  return (await byraa(k, `/accountingOffice/reconciliations/${id}/comments`, {
    query: { fields: 'id,reconciliationId,referenceId,createdAt,comment' },
  })).values ?? [];
}

async function cmdPerioder(k, a) {
  if (!a.aar || !a.type) throw new Error('Bruk: perioder --client "klient" --aar ÅÅÅÅ --type BALANCE|VAT_GENERAL_INDUSTRY');
  const svar = (await byraa(k, '/accountingOffice/reconciliations/periodsOverview', {
    query: { customerId: k.id, year: a.aar, type: a.type, fields: '*,periods(*,reconciliation(id,status,type))' },
  })).value;
  const perioder = (svar?.periods ?? [])
    .filter((p) => !p.reconciliation || p.reconciliation.type === a.type) // ANNUAL_BALANCE ut
    .map((p) => ({ termin: p.termNumber, start: p.startDate ?? p.start, slutt: p.endDate ?? p.end, id: p.reconciliation?.id ?? null, status: p.reconciliation?.status ?? null }));
  if (a.json) return console.log(JSON.stringify(perioder, null, 1));
  for (const p of perioder) console.log(`${String(p.termin).padStart(2)}  ${p.start} – ${p.slutt}  ${p.id ?? '(ingen)'}  ${p.status ?? ''}`);
}

async function cmdVedlegg(k, a) {
  const r = await avstemming(k, a.id);
  const vedlegg = await vedleggPaa(k, a.id); // sekvensielt: tokenfornyingen tåler ikke parallelle kall
  const kommentarer = await kommentarerPaa(k, a.id);
  const ut = { avstemming: r, vedlegg: vis(vedlegg), kommentarer: vis(kommentarer) };
  console.log(JSON.stringify(ut, null, a.json ? 1 : 2));
}

async function cmdLinjer(k, a) {
  const r = await avstemming(k, a.id);
  if (r.type !== 'BALANCE') throw new Error(`Avstemming ${a.id} er ${r.type}, ikke BALANCE.`);
  const t = (await byraa(k, `/balance/reconciliation/${a.id}/table`, {
    query: { fields: '*,groups(*,lines(accountId,displayName,balanceIn,balanceChange,balanceOut,documentedBalance,difference,status,autoReconciled))' },
  })).value;
  const linjer = (t?.groups ?? []).flatMap((g) => g.lines ?? [])
    .filter((l) => !a.konto || String(l.displayName ?? '').startsWith(String(a.konto)));
  console.log(JSON.stringify(vis(linjer), null, 1));
}

async function balanselinje(k, id, accountId) {
  const t = (await byraa(k, `/balance/reconciliation/${id}/table`, { query: { fields: '*,groups(*,lines(*))' } })).value;
  return (t?.groups ?? []).flatMap((g) => g.lines ?? []).find((l) => String(l.accountId) === String(accountId));
}

const kortLinje = (l) => l && ({ accountId: l.accountId, konto: l.displayName, saldo: l.balanceOut, dokumentert: l.documentedBalance, differanse: l.difference, status: l.status });

/** Setter status (og eventuelt dokumentert saldo fra kontoutskrift) på én balanselinje. RECONCILED krever differanse 0. */
async function cmdSettStatus(k, a) {
  if (!a.id || !a.konto || !a.status) throw new Error('Bruk: sett-status --client "klient" --id <BALANCE-id> --konto <accountId> --status RECONCILED|IGNORED [--dokumentert <beløp>] [--bekreft]');
  const r = await avstemming(k, a.id);
  if (r.type !== 'BALANCE') throw new Error(`Avstemming ${a.id} er ${r.type}, ikke BALANCE.`);
  if (r.modifiable === false) throw new Error(`Avstemming ${a.id} er låst (${r.status}) – ingenting er gjort.`);
  const foer = await balanselinje(k, a.id, a.konto);
  if (!foer) throw new Error(`Fant ikke linjen for konto-id ${a.konto}.`);
  if (foer.status === a.status && a.dokumentert === undefined) return console.log(JSON.stringify({ linje: kortLinje(foer), resultat: 'allerede satt' }));
  if (foer.status !== a.status && foer.availableStatuses && !foer.availableStatuses.includes(a.status)) throw new Error(`${a.status} er ikke tillatt på ${foer.displayName} (${foer.availableStatuses.join(', ')}).`);
  const dokumentert = a.dokumentert !== undefined ? Number(String(a.dokumentert).replace(',', '.')) : foer.documentedBalance;
  const diff = dokumentert == null ? null : Math.round((foer.balanceOut - dokumentert) * 100) / 100;
  if (a.status === 'RECONCILED' && diff !== 0) throw new Error(`${foer.displayName}: differanse ${diff ?? 'ukjent (ingen dokumentert saldo)'} – setter ikke RECONCILED.`);
  const plan = { avstemming: `${r.type} ${r.year}/${r.term} (${r.id})`, foer: kortLinje(foer), nyStatus: a.status, dokumentert };
  if (foer.status === a.status && foer.documentedBalance === dokumentert) return console.log(JSON.stringify({ ...plan, resultat: 'allerede satt' }));
  if (!a.bekreft) return console.log(JSON.stringify({ ...plan, resultat: 'tørrkjøring – legg til --bekreft' }));
  const body = { ...foer, documentedBalance: dokumentert, status: a.status, reconciledBy: null, controlledBy: null };
  await byraa(k, `/balance/reconciliation/${a.id}/table/${foer.accountId}`, { method: 'PUT', body, query: { fields: 'accountId,documentedBalance,difference,status' } });
  const etter = await balanselinje(k, a.id, a.konto);
  console.log(JSON.stringify({ ...plan, resultat: etter?.status === a.status ? 'satt' : 'UVENTET – sjekk', etter: kortLinje(etter) }));
}

// ---- Mva-avstemming: oversikt og fullføring ----
async function mvaOversikt(k, id) {
  const r = await avstemming(k, id);
  if (!String(r.type).startsWith('VAT')) throw new Error(`Avstemming ${id} er ${r.type}, ikke mva.`);
  const o = (await byraa(k, `/vat/reconciliation/${id}/overview`, { query: { fields: '*,groups(*,lines(*))' } })).value ?? {};
  const linjer = (o.groups ?? []).flatMap((g) => g.lines ?? []).map((l) => ({
    vatTypeId: l.vatTypeId ?? l.vatType?.id, grunnlag: l.basis, hovedbok: l.ledgerData, rapportert: l.reportedData, skatteetaten: l.taxAdminData, differanse: l.difference,
  }));
  const sum = (f) => linjer.reduce((s, l) => s + (l[f] ?? 0), 0);
  return { r, linjer, sum: { hovedbok: sum('hovedbok'), rapportert: sum('rapportert'), skatteetaten: sum('skatteetaten'), differanse: sum('differanse') }, raa: Object.keys(o) };
}

async function cmdMvaOversikt(k, a) {
  const { r, linjer, sum, raa } = await mvaOversikt(k, a.id);
  const val = (await byraa(k, `/accountingOffice/reconciliations/${a.id}/validations`, { query: { fields: 'referenceId,message' } })).values ?? [];
  console.log(JSON.stringify({ avstemming: r, linjer, sum, validations: val, felt: raa }, null, 1));
}

/**
 * Fullfører en avstemming. Mva: krever at Skatteetatens tall finnes og at hovedbok = rapportert = Skatteetaten på alle linjer.
 * Balanse: krever at ingen linje står som NOT_RECONCILED/REJECTED og at avstemte linjer har differanse 0.
 */
async function cmdFullfor(k, a) {
  const ra = await avstemming(k, a.id);
  if (ra.type === 'BALANCE') {
    if (ra.status !== 'DRAFT') return console.log(JSON.stringify({ avstemming: ra, resultat: `ikke DRAFT (${ra.status}) – ingenting gjort` }));
    const t = (await byraa(k, `/balance/reconciliation/${a.id}/table`, { query: { fields: '*,groups(*,lines(accountId,displayName,status,difference))' } })).value;
    const linjer = (t?.groups ?? []).flatMap((g) => g.lines ?? []);
    const aapne = linjer.filter((l) => ['NOT_RECONCILED', 'REJECTED'].includes(l.status) || (l.status === 'RECONCILED' && l.difference && Math.abs(l.difference) >= 0.005));
    if (aapne.length) return console.log(JSON.stringify({ avstemming: ra.id, resultat: `fullføres ikke: ${aapne.length} linjer uten status eller med differanse`, linjer: aapne.map((l) => l.displayName) }));
    if (!a.bekreft) return console.log(JSON.stringify({ avstemming: ra.id, linjer: linjer.length, resultat: 'klar – legg til --bekreft for å fullføre' }));
    await byraa(k, `/accountingOffice/reconciliations/${a.id}/:complete`, { method: 'PUT' });
    return console.log(JSON.stringify({ avstemming: await avstemming(k, a.id), resultat: 'fullført' }));
  }
  const { r, linjer, sum } = await mvaOversikt(k, a.id);
  if (r.status !== 'DRAFT') return console.log(JSON.stringify({ avstemming: r, resultat: `ikke DRAFT (${r.status}) – ingenting gjort` }));
  const avvik = linjer.filter((l) => l.skatteetaten == null || l.hovedbok !== l.rapportert || l.rapportert !== l.skatteetaten);
  if (avvik.length) return console.log(JSON.stringify({ avstemming: r.id, resultat: 'fullføres ikke: mangler Skatteetatens tall eller har avvik', avvik }));
  if (!a.bekreft) return console.log(JSON.stringify({ avstemming: r.id, sum, resultat: 'klar – legg til --bekreft for å fullføre' }));
  await byraa(k, `/accountingOffice/reconciliations/${a.id}/:complete`, { method: 'PUT' });
  const etter = await avstemming(k, a.id);
  console.log(JSON.stringify({ avstemming: etter, sum, resultat: etter.status }));
}

/** Låser opp en fullført avstemming (f.eks. for å bytte et vedlegg). Fullfør igjen med `fullfor` etterpå. */
async function cmdLaasOpp(k, a) {
  const r = await avstemming(k, a.id);
  if (r.status === 'DRAFT') return console.log(JSON.stringify({ avstemming: r, resultat: 'allerede åpen' }));
  if (!a.bekreft) return console.log(JSON.stringify({ avstemming: r, resultat: 'tørrkjøring – legg til --bekreft for å låse opp' }));
  await byraa(k, `/accountingOffice/reconciliations/${a.id}/:unlock`, { method: 'PUT' });
  console.log(JSON.stringify({ avstemming: await avstemming(k, a.id), resultat: 'låst opp' }));
}

// ---- Utligning av åpne poster i reskontro (klientkontekst) ----
// Sperrer: bare kontoer 1500–1599 og 2400–2499, én konto og én motpart per gruppe, sum nøyaktig 0,00,
// alle poster åpne før kallet, og kontroll etterpå. Skriver bare med --bekreft.
const PF = 'id,date,amount,account(number),customer(id),supplier(id),closeGroup(id)';
const oere = (x) => Math.round(x * 100);
const reskontrokonto = (n) => (n >= 1500 && n <= 1599) || (n >= 2400 && n <= 2499);
const motpartAv = (p) => (p.account?.number < 2000 ? p.customer?.id : p.supplier?.id) ?? null;

async function lukkGruppe(k, ids) {
  const poster = await hentPoster(k, ids, PF);
  const kontoer = new Set(poster.map((p) => p.account?.number));
  const motparter = new Set(poster.map(motpartAv));
  const sum = poster.reduce((s, p) => s + oere(p.amount), 0);
  const feil = [
    kontoer.size !== 1 && 'ulike kontoer',
    ![...kontoer].every(reskontrokonto) && 'ikke reskontrokonto',
    (motparter.size !== 1 || motparter.has(null)) && 'ulik eller manglende motpart',
    sum !== 0 && `summerer til ${sum / 100}, ikke 0`,
    poster.some((p) => p.closeGroup) && 'en eller flere poster er allerede lukket',
  ].filter(Boolean);
  if (feil.length) return { ids, lukket: false, grunn: feil.join(', ') };
  await klientkall(k, '/ledger/posting/:closePostings', { method: 'PUT', body: ids });
  const etter = await hentPoster(k, ids, 'id,closeGroup(id)');
  return { ids, konto: [...kontoer][0], lukket: etter.every((p) => p.closeGroup), closeGroup: etter[0]?.closeGroup?.id ?? null };
}

async function cmdUtlign(k, a) {
  const konto = Number(a.konto);
  if (!reskontrokonto(konto)) throw new Error('Bruk: utlign --client "klient" --konto 1500|2400 [--bekreft]');
  const imorgen = new Date(Date.now() + 864e5).toISOString().slice(0, 10);
  const poster = (await klientkall(k, '/ledger/posting/openPost', { query: { date: imorgen, accountNumberFrom: konto, accountNumberTo: konto, sorted: false, count: 10000, fields: PF } })).values ?? [];
  const per = new Map();
  for (const p of poster) { const m = motpartAv(p); if (m) (per.get(m) ?? per.set(m, []).get(m)).push(p); }
  const grupper = [...per.values()].flatMap((l) => (l.length > 1 ? nullgrupper(l) : []));
  const plan = { konto, aapnePoster: poster.length, grupper: grupper.length, posterSomLukkes: grupper.reduce((s, g) => s + g.length, 0) };
  if (!a.bekreft) return console.log(JSON.stringify({ ...plan, resultat: 'tørrkjøring – legg til --bekreft for å lukke' }));
  const res = [];
  for (const g of grupper) res.push(await lukkGruppe(k, g.map((p) => p.id)));
  const igjen = (await klientkall(k, '/ledger/posting/openPost', { query: { date: imorgen, accountNumberFrom: konto, accountNumberTo: konto, sorted: false, count: 10000, fields: 'id' } })).values ?? [];
  console.log(JSON.stringify({ ...plan, lukket: res.filter((r) => r.lukket).length, ikkeLukket: res.filter((r) => !r.lukket), aapnePosterEtter: igjen.length }));
}

async function cmdLukk(k, a) {
  const ids = String(a.ids ?? '').split(',').map((x) => Number(x.trim())).filter(Boolean);
  if (ids.length < 2) throw new Error('Bruk: lukk --client "klient" --ids <id1,id2,...> [--bekreft]');
  if (!a.bekreft) {
    const poster = await hentPoster(k, ids, PF);
    return console.log(JSON.stringify({ poster: poster.map((p) => ({ id: p.id, dato: p.date, konto: p.account?.number, belop: p.amount, motpart: motpartAv(p), lukket: !!p.closeGroup })), sum: poster.reduce((s, p) => s + oere(p.amount), 0) / 100, resultat: 'tørrkjøring – legg til --bekreft' }));
  }
  console.log(JSON.stringify(await lukkGruppe(k, ids)));
}

/** Poster på id, én om gangen (tokenfornyingen tåler ikke parallelle kall). */
async function hentPoster(k, ids, fields) {
  const ut = [];
  for (const id of ids) ut.push((await klientkall(k, `/ledger/posting/${id}`, { query: { fields } })).value);
  return ut;
}

// ---- Notater (Silfer-PDF) og kontroll av mva-utkast ----
/** Mappa PDF-en skrives til: --ut, ellers %TEMP%\rr\modul-<kommando>-<periode>. Aldri inne i repoet. */
function dokumentasjonsmappe(kommando, periode, ut) {
  const m = resolve(typeof ut === 'string' ? ut : standardUt(`modul-${kommando}`, periode));
  mkdirSync(m, { recursive: true });
  return m;
}

async function cmdKontrollUtkast(k, a) {
  const aar = Number(a.aar), termin = Number(a.termin);
  if (!aar || !termin) throw new Error('Bruk: kontroll-utkast --client "klient" --aar ÅÅÅÅ --termin N [--json]');
  const r = await kontrollUtkast(await connect(a.client), aar, termin);
  if (a.json) return console.log(JSON.stringify(r, null, 1));
  console.log(`Termin ${termin}/${aar}: ${r.ok ? 'OK' : 'SJEKK'} – melding id ${r.utkast.id} (${r.utkast.status ?? 'utkast'}), å betale ${r.utkast.aaBetale ?? '–'}, terminbeløp ${r.termBelop}, hovedbok ${r.sumHovedbok}`);
  for (const x of r.perKode) console.log(`  kode ${x.kode}${x.snudd ? ' (ut/inn)' : ''}: hovedbok ${x.hbMva} / melding ${x.mMva}${x.avvik ? `  AVVIK ${x.avvik}` : ''}`);
  for (const f of r.fortegn) console.log(`  fortegn: kode ${f.kode} ${f.mva} (forventet ${f.forventet}) – ${f.merknad ? `merknad «${f.merknad}»` : 'MANGLER MERKNAD'}`);
  if (r.validering) console.log(`  forhåndssjekk: ${JSON.stringify(r.validering)}`);
  if (r.oppgjor) console.log(`  oppgjørsbilag ${r.oppgjor.bilag} (${r.oppgjor.dato}), 2740 ${r.oppgjor.ub2740}${r.oppgjor.rest27xx.length ? `, REST 27xx: ${JSON.stringify(r.oppgjor.rest27xx)}` : ''}`);
  if (r.status) console.log(`  levering ${r.status.deliveryStatus?.status ?? '–'}, betaling ${r.status.paymentStatus?.status ?? '–'}${r.betaling ? `, KID ${r.betaling.kid}, forfall ${r.betaling.dueDate}` : ''}`);
}

async function cmdNotat2740(k, a) {
  const aar = Number(a.aar), termin = Number(a.termin);
  if (!aar || !termin) throw new Error('Bruk: notat-2740 --client "klient" --aar ÅÅÅÅ --termin N [--forklaring-MM "beløp|tekst"] [--ut <mappe>]');
  // --forklaring-07 "171809|Tilgode termin 3 ..." gir dokumentert saldo og forklaring for måneden (faglig vurdering).
  const forklaringer = {};
  for (const [nokkel, verdi] of Object.entries(a)) {
    const m = nokkel.match(/^forklaring-(\d{2})$/);
    if (!m || typeof verdi !== 'string') continue;
    const [belop, ...tekst] = verdi.split('|');
    forklaringer[`${aar}-${m[1]}`] = { dokumentert: Number(belop.replace(/\s/g, '').replace(',', '.')), tekst: tekst.join('|').trim() };
  }
  const r = await notat2740(await connect(a.client), { aar, termin, forklaringer, kundenavn: k.name, orgnr: k.organizationNumber });
  const fil = join(dokumentasjonsmappe('notat-2740', `${aar}-T${termin}`, a.ut), r.filnavn);
  const byte = lagPdf(r.html, fil);
  console.log(JSON.stringify({ fil, byte, avstemt: r.avstemt, maaneder: r.maaneder.map((x) => ({ maaned: x.m, saldo: x.ub, dokumentert: x.dokumentert, differanse: x.diff })), kontrollOk: r.kontroll.ok }));
}

async function cmdReskontroVurdering(k, a) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(a.dato ?? '')) throw new Error('Bruk: reskontro-vurdering --client "klient" --dato ÅÅÅÅ-MM-DD [--vurderinger <fil.json>] [--json] [--ut <mappe>]');
  const vurderinger = typeof a.vurderinger === 'string' ? JSON.parse(readFileSync(a.vurderinger, 'utf8')) : null;
  const r = await reskontroVurdering(await connect(a.client), { dato: a.dato, vurderinger, kundenavn: k.name, orgnr: k.organizationNumber });
  const mappe = dokumentasjonsmappe('reskontro-vurdering', a.dato, a.ut);
  const fil = join(mappe, r.filnavn);
  const byte = lagPdf(r.html, fil);
  const ut = { fil, byte, aapnePoster: r.antall, tilOppfolging: r.oppfolging, vurderinger: !!vurderinger };
  if (a.json) {
    // Kategorisert per konto og motpart til fil; konsollen får bare sammendraget per konto og kategori.
    const jsonFil = join(mappe, 'reskontro-vurdering.json');
    writeFileSync(jsonFil, JSON.stringify({ klient: k.name, orgnr: k.organizationNumber ?? '', ...r.data }, null, 1));
    const kort = (x) => ({ aapnePoster: x.aapnePoster, sum: x.sum, tilOppfolging: x.tilOppfolging, motparter: x.motparter.length, kategorier: x.kategorier, eldre: x.eldre });
    return console.log(JSON.stringify({ ...ut, json: jsonFil, dato: r.data.dato, avsetning1580: r.data.avsetning1580, 1500: kort(r.data[1500]), 2400: kort(r.data[2400]) }, null, 1));
  }
  // Bare antall i utskriften – navn og beløp per motpart står i PDF-en.
  console.log(JSON.stringify(ut));
}

async function cmdBankpdf(k, a) {
  if (!a.konto || !/^\d{4}-\d{2}$/.test(a.maaned ?? '')) throw new Error('Bruk: bankpdf --client "klient" --konto 1920 --maaned ÅÅÅÅ-MM [--ut <mappe>]');
  const konto = (await klientkall(k, '/ledger/account', { query: { number: a.konto, fields: 'id,number,name' } })).values?.[0];
  if (!konto) throw new Error(`Fant ikke konto ${a.konto}.`);
  // Filtrer på regnskapsperiode: klienter med mange år har over 100 avstemminger per konto, så en usortert side bommer.
  const periode = (await klientkall(k, '/ledger/accountingPeriod', {
    query: { startFrom: `${a.maaned}-01`, startTo: `${a.maaned}-02`, fields: 'id,start' },
  })).values?.[0];
  if (!periode) throw new Error(`Fant ikke regnskapsperiode ${a.maaned}.`);
  const avst = (await klientkall(k, '/bank/reconciliation', {
    query: { accountId: konto.id, accountingPeriodId: periode.id, fields: 'id,type,isClosed,accountingPeriod(start,end)' },
  })).values ?? [];
  const r = avst.find((x) => x.accountingPeriod?.start?.startsWith(a.maaned));
  if (!r) throw new Error(`Ingen bankavstemming for ${a.konto} i ${a.maaned}.`);
  if (!r.isClosed) throw new Error(`Bankavstemmingen for ${a.konto} i ${a.maaned} er ikke lukket – ingen PDF.`);
  // Eksport, ikke endring. actionType er låst til FileDownload: aldri SendEmail eller e-postadresser.
  const pdf = await klientkall(k, '/bank/reconciliation/internal/export/pdf', {
    method: 'PUT', binaer: true,
    body: { actionType: 'FileDownload', type: 'APPROVED', transactionsType: 'CURRENT_MONTH', pdfOrientation: 'portrait', bankReconciliationId: r.id, accountId: konto.id },
  });
  if (pdf.subarray(0, 4).toString() !== '%PDF') throw new Error(`Svaret var ikke en PDF (${pdf.length} byte).`);
  const fil = join(dokumentasjonsmappe('bankpdf', a.maaned, a.ut), `Bankavstemming ${a.konto} ${a.maaned} ${k.name}.pdf`);
  writeFileSync(fil, pdf);
  console.log(JSON.stringify({ konto: a.konto, maaned: a.maaned, bankavstemming: r.id, type: r.type, fil, byte: pdf.length }));
}

async function cmdLastOpp(k, a) {
  if (!a.id || !a.ref || !a.fil) throw new Error('Bruk: last-opp --client "klient" --id <id> --ref <referenceId> --fil <sti> [--bekreft]');
  if (!existsSync(a.fil)) throw new Error(`Fant ikke ${a.fil}.`);
  const r = await avstemming(k, a.id);
  if (r.modifiable === false) throw new Error(`Avstemming ${a.id} er låst (${r.status}) – ingenting er gjort.`);
  const navn = basename(a.fil);
  const navnPaa = (v) => v.fileName ?? v.name ?? v.document?.fileName ?? v.document?.name;
  const foer = await vedleggPaa(k, a.id);
  const gamle = foer.filter((v) => String(v.referenceId) === String(a.ref) && navnPaa(v) === navn);
  const plan = { avstemming: `${r.type} ${r.year}/${r.term} (${r.id})`, referenceId: a.ref, fil: navn, vedleggFoer: foer.length };
  if (gamle.length && !a.erstatt) return console.log(JSON.stringify({ ...plan, resultat: 'finnes allerede – ikke lastet opp (bruk --erstatt for ny versjon)' }));
  if (!a.bekreft) return console.log(JSON.stringify({ ...plan, resultat: 'tørrkjøring – legg til --bekreft for å laste opp' }));
  const form = new FormData();
  form.append('file', new Blob([readFileSync(a.fil)], { type: navn.toLowerCase().endsWith('.pdf') ? 'application/pdf' : 'application/octet-stream' }), navn);
  await byraa(k, `/accountingOffice/reconciliations/${a.id}/attachments`, { method: 'POST', query: { referenceId: a.ref }, form });
  let etter = await vedleggPaa(k, a.id);
  const ny = etter.filter((v) => !foer.some((f) => f.id === v.id));
  // --erstatt: den gamle versjonen slettes først når den nye er bekreftet lastet opp.
  let slettet = 0;
  if (gamle.length && ny.length === 1) {
    for (const g of gamle) { await byraa(k, `/accountingOffice/reconciliations/${a.id}/attachments/${g.id}`, { method: 'DELETE' }); slettet++; }
    etter = await vedleggPaa(k, a.id);
  }
  console.log(JSON.stringify({ ...plan, resultat: gamle.length ? `erstattet (${slettet} gammel slettet)` : 'lastet opp', vedleggEtter: etter.length, nytt: vis(ny) }));
}

function argumenter(liste) {
  const a = {};
  for (let i = 0; i < liste.length; i++) {
    if (!liste[i].startsWith('--')) continue;
    const navn = liste[i].slice(2);
    const neste = liste[i + 1];
    if (neste === undefined || neste.startsWith('--')) a[navn] = true;
    else { a[navn] = neste; i++; }
  }
  return a;
}

const [kommando, ...rest] = process.argv.slice(2);
const kommandoer = { perioder: cmdPerioder, vedlegg: cmdVedlegg, linjer: cmdLinjer, 'sett-status': cmdSettStatus, utlign: cmdUtlign, lukk: cmdLukk, 'mva-oversikt': cmdMvaOversikt, fullfor: cmdFullfor, 'laas-opp': cmdLaasOpp,
  'kontroll-utkast': cmdKontrollUtkast, 'notat-2740': cmdNotat2740, 'reskontro-vurdering': cmdReskontroVurdering, bankpdf: cmdBankpdf, 'last-opp': cmdLastOpp };
try {
  if (!kommandoer[kommando]) throw new Error(`Ukjent kommando «${kommando ?? ''}». Tilgjengelig: ${Object.keys(kommandoer).join(', ')}`);
  const a = argumenter(rest);
  if (typeof a.client !== 'string') throw new Error('Klient mangler: --client "klient". Ingenting er gjort.');
  const k = await client(a.client);
  console.error(`[${k.name}${viaKonto(k.account)}] ${kommando}`);
  await kommandoer[kommando](k, a);
} catch (err) {
  console.error(`Feil: ${redactText(String(err.message).slice(0, 1500))}`);
  process.exitCode = 1;
}
