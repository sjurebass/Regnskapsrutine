// Bilagsføring: dokumenter i bilagsmottaket mot åpne bankposter, og manuelle bilag (avansert føring) fra plan.
//
//   npm run -s bilag -- hent    --client "Klient" --til 2026-09 [--fra 2026-08] [--ut <mappe>]     (kun lesing)
//   npm run -s bilag -- før     --client "Klient" --plan <mappe>/plan.json [--bare <id>,<id>] [--bekreft]
//   npm run -s bilag -- manuell --client "Klient" --plan <mappe>/manuell.json [--bare <ref>,<ref>] [--vesentlighet <beløp>] [--bekreft]
//
// hent  – laster ned alle dokumenter i bilagsmottaket (ikke EHF) til <ut>/docs/<id>.pdf + .txt, henter umatchede
//         banktransaksjoner (med id) for perioden og lager forslag.json med beløpstreff dokument ↔ bankpost.
//         historikk.tsv: hvordan leverandører/tekster er ført de siste 12 månedene (konto, mva). leverandorer.tsv: id + navn.
//         Standard --ut: %TEMP%\rr\bilag-<til> (aldri inne i repoet).
// før   – per linje i plan.json: nytt avansert bilag (POST /ledger/voucher) → last opp dokumentet som vedlegg →
//         bekreft vedlegget → lukk 2400 (når leverandør) → match bankposten → slett kopien i bilagsmottaket.
//         Uten --bekreft: bare tørrkjøring (validering, ingen skriving). Logg i <plan>.resultat.json; ferdige steg hoppes over.
//
// plan.json (id-ene under er plassholdere – bruk id-ene fra forslag.json og bank.json):
// [{
//   "inbox": <inbox-id>,             // id i bilagsmottaket (fra forslag.json)
//   "dato": "2026-09-03",            // bilagsdato (fakturadato/kjøpsdato)
//   "beskrivelse": "Leverandør – faktura 1234",
//   "bankkonto": 1920, "belop": -347.08,   // bankbeløpet med fortegn (ut = negativt)
//   "bankTx": <banktransaksjon-id>,  // id på banktransaksjonen (utelates ved kontoutskrift uten bankfeed)
//   "leverandor": <leverandør-id>,   // valgfri leverandør-id → kostnad/2400 + 2400/bank i samme bilag, 2400 lukkes
//   "fakturanr": "1234",             // valgfri
//   "valuta": "USD",                 // valgfri: linjene oppgis i valuta, kurs fra Tripletex på dato, differanse → 8060/8160
//   "flere": [<inbox-id>],           // valgfri: flere dokumenter fra mottaket på samme bilag (kvittering + faktura)
//   "linjer": [{ "konto": 6552, "belop": 347.08, "mva": 86, "prosjekt": 11, "avdeling": 2 }]
// }]
// Summen av linjene (brutto, NOK) skal være lik −belop. Mva-koden er Tripletex-nummeret (1, 11, 13, 14, 86, 0 …).
//
// manuell – manuelt bilag (periodisering, avsetning, omføring) fra manuell.json. Uten --bekreft: tørrkjøring med
//         føringskontrollene J1–J12 per bilag (PASS/FEIL/ADVARSEL/INFO); exit 1 når noe har FEIL. Med --bekreft: bilag med FEIL
//         stoppes, de andre føres: POST /ledger/voucher → tilbakelesing av linjene → vedlegg (lastes opp og bekreftes) →
//         reversering (PUT :reverse på `tilbakefor`). Logg i <plan>.resultat.json (ref → bilagsnummer, reversering, vedlegg, feil);
//         ferdige refs hoppes over. Et skrivekall uten svar (nettverk) merkes «avbrutt» og stopper neste kjøring for den ref-en.
// [{
//   "ref": "forsikring-2026-09",           // unik nøkkel: logg, dublettsjekk, idempotens
//   "dato": "2026-09-30", "beskrivelse": "Periodisering forsikring sep 2026",
//   "linjer": [{ "konto": 6400, "belop": 1250.00, "mva": 0, "avdeling": <avdeling-id>, "prosjekt": <prosjekt-id>,
//                "leverandor": null, "kunde": null, "tekst": "1/12 av premie" },
//              { "konto": 1700, "belop": -1250.00 }],      // belop: + = debet, − = kredit; alle linjer får bilagsdatoen
//   "tilbakefor": "2026-10-01",              // valgfri: reversering på dato (påløpte kostnader)
//   "vedlegg": ["grunnlag.pdf"]              // valgfri: PDF/PNG/JPEG/TIFF, sti relativt til planen
// }]
// Mva mangler = 0 (eller kontoens låste kode). Avdeling/prosjekt/kunde/leverandør er Tripletex-id-er.
// Leverandør: Tripletex krever samme leverandør på alle linjene (ellers 422) – én leverandør settes derfor på alle linjene;
// to leverandører, eller kunde og leverandør i samme bilag, stoppes (FEIL J6: del bilaget). Kunde settes på linjen den står på.
// Kontrollene: J1 sum = 0 · J2 åpen periode (regnskapsperiode, bankavstemming for bankkonto, levert mva-termin for linjer med mva) ·
// J3 kontoer finnes/aktive · J4 mva-kode · J5 avdeling/prosjekt · J6 reskontropart på 1500/2400 · J7 dublett (ref i logg/plan,
// samme dato+konto+beløp i hovedboken) · J8 tilbakeføring · J9 over V · J10 runde beløp · J11 vedlegg finnes · J12 beskrivelse.
//
// GDPR: konsollen viser bare antall, beløp, konto og bilagsnummer. Tekst i filene er maskert med redactText().

import { mkdirSync, writeFileSync, readFileSync, existsSync, readdirSync } from 'node:fs';
import { join, resolve, dirname, basename } from 'node:path';
import { spawnSync } from 'node:child_process';
import { connect } from './tripletex.js';
import { BASE_URL, authorization } from './auth.js';
import { redactText } from './privacy.js';
import { standardUt, kortFeil } from './valg.js';

const args = process.argv.slice(2);
const kommando = args[0];
const opt = (n) => { const i = args.indexOf(n); return i >= 0 ? args[i + 1] : undefined; };
const flag = (n) => args.includes(n);
const r2 = (x) => Math.round(x * 100) / 100;
const nesteMnd = (m) => { const d = new Date(`${m}-01T00:00:00Z`); d.setUTCMonth(d.getUTCMonth() + 1); return d.toISOString().slice(0, 10); };
const dager = (a, b) => Math.round((new Date(a) - new Date(b)) / 86_400_000);

if (!['hent', 'før', 'for', 'manuell'].includes(kommando) || !opt('--client')) {
  console.error('Bruk: npm run -s bilag -- hent    --client "Klient" --til ÅÅÅÅ-MM [--fra ÅÅÅÅ-MM] [--ut <mappe>]\n' +
    '      npm run -s bilag -- før     --client "Klient" --plan <plan.json> [--bare id,id] [--bekreft]\n' +
    '      npm run -s bilag -- manuell --client "Klient" --plan <manuell.json> [--bare ref,ref] [--vesentlighet <beløp>] [--bekreft]\nIngenting er gjort.');
  process.exit(1);
}
const c = await connect(opt('--client'));

// Oppslag med hurtigbuffer (konto, mva-kode, periode …). Rå svar lagres; slå = første treff, slåAlle = liste, verdi = enkeltobjekt.
const cache = new Map();
const hentet = async (sti, query) => {
  const k = sti + JSON.stringify(query);
  if (!cache.has(k)) cache.set(k, await c.request(sti, { query }));
  return cache.get(k);
};
const slå = async (sti, query) => (await hentet(sti, query))?.values?.[0] ?? null;
const slåAlle = async (sti, query) => (await hentet(sti, query))?.values ?? [];
const verdi = async (sti, query) => (await hentet(sti, query))?.value ?? null;

// Vedlegg: multipart til /ledger/voucher/{id}/attachment (legges til som nye sider), deretter bekreftet på bilaget.
async function lastOppVedlegg(voucherId, fil) {
  const ext = fil.split('.').pop().toLowerCase();
  const type = ext === 'pdf' ? 'application/pdf' : /^(png|jpe?g)$/.test(ext) ? `image/${ext.replace('jpg', 'jpeg')}`
    : /^tiff?$/.test(ext) ? 'image/tiff' : 'application/octet-stream';
  const fd = new FormData();
  fd.append('file', new Blob([readFileSync(fil)], { type }), basename(fil));
  const res = await fetch(`${BASE_URL}/ledger/voucher/${voucherId}/attachment`, { method: 'POST',
    headers: { Authorization: await authorization(c.company.id, c.company.account), Accept: 'application/json' }, body: fd });
  if (!res.ok) throw new Error(`vedlegg: ${res.status} ${(await res.text()).slice(0, 200)}`);
  const { value: v } = await c.request(`/ledger/voucher/${voucherId}`, { query: { fields: 'attachment(id)' } });
  if (!v.attachment?.id) throw new Error('vedlegget ligger ikke på bilaget etter opplasting');
}

// ── hent ────────────────────────────────────────────────────────────────────
function belopITekst(tekst) {
  // «1 234,56», «1.234,56», «1,234.56», «347.08», «kr 99,-» → tall
  const ut = new Set();
  const re = /(?<![\d])(\d{1,3}(?:[ .,  ]\d{3})+|\d+)(?:([.,])(\d{2})|,-)(?![\d])/g;
  for (const m of tekst.matchAll(re)) {
    const heltall = m[1].replace(/[ .,  ]/g, '');
    const n = Number(`${heltall}.${m[3] ?? '00'}`);
    if (n > 0 && n < 1e8) ut.add(n);
  }
  return [...ut];
}

async function lastNed(docId, fil) {
  const res = await fetch(`${BASE_URL}/document/${docId}/content`, { headers: { Authorization: await authorization(c.company.id, c.company.account) } });
  if (!res.ok) throw new Error(`nedlasting ${docId}: ${res.status}`);
  writeFileSync(fil, Buffer.from(await res.arrayBuffer()));
}

async function umatchetBank(fra, til) {
  const kontoer = await c.list('/ledger/account', { query: { isBankAccount: true, isInactive: false, fields: 'id,number,name' } });
  const ut = [], utenFeed = [];
  for (const a of kontoer) {
    let st = [];
    try { st = await c.list('/bank/statement', { query: { accountId: a.id, fields: 'id,fromDate,toDate' } }); } catch { st = []; }
    st = st.filter((s) => s.fromDate < nesteMnd(til) && (s.toDate ?? s.fromDate) >= `${fra}-01`);
    if (!st.length) { utenFeed.push(a.number); continue; }
    for (const s of st) {
      const tx = await c.list('/bank/statement/transaction', { query: { bankStatementId: s.id, fields: 'id,postedDate,description,amountCurrency,matched' } });
      for (const t of tx) {
        if (t.matched || t.postedDate < `${fra}-01` || t.postedDate >= nesteMnd(til) || ut.some((x) => x.id === t.id)) continue;
        ut.push({ id: t.id, konto: a.number, dato: t.postedDate, belop: t.amountCurrency, tekst: redactText(t.description ?? '') });
      }
    }
  }
  return { bank: ut.sort((a, b) => a.dato.localeCompare(b.dato)), utenFeed };
}

async function historikk(til) {
  const fra = new Date(`${til}-01T00:00:00Z`); fra.setUTCFullYear(fra.getUTCFullYear() - 1);
  const p = await c.list('/ledger/posting', { query: {
    dateFrom: fra.toISOString().slice(0, 10), dateTo: nesteMnd(til), accountNumberFrom: 1200, accountNumberTo: 8999,
    fields: 'date,description,account(number),vatType(number),supplier(id,name),voucher(number,year,description)',
  } });
  const map = new Map();
  for (const x of p) {
    const n = x.account?.number;
    if (!n || (n >= 1300 && n < 4000) || (n >= 5000 && n < 5500)) continue; // balanse utenom 12xx, og lønn
    const hvem = x.supplier?.name ?? (x.description || x.voucher?.description || '').replace(/\d[\d\s.,/-]*/g, '').trim().slice(0, 40);
    if (!hvem) continue;
    const k = `${hvem.toLowerCase()}|${n}|${x.vatType?.number ?? ''}`;
    const e = map.get(k) ?? { hvem, lev: x.supplier?.id ?? '', konto: n, mva: x.vatType?.number ?? '', antall: 0, sist: '', bilag: '' };
    e.antall++;
    if (x.date > e.sist) { e.sist = x.date; e.bilag = `${x.voucher?.number}-${x.voucher?.year}`; }
    map.set(k, e);
  }
  const rader = [...map.values()].sort((a, b) => a.hvem.localeCompare(b.hvem, 'nb') || b.antall - a.antall);
  return ['leverandør/tekst\tlev-id\tkonto\tmva\tantall\tsist\tbilag',
    ...rader.map((e) => [redactText(e.hvem), e.lev, e.konto, e.mva, e.antall, e.sist, e.bilag].join('\t'))].join('\n');
}

async function hent() {
  const forrige = new Date(); forrige.setDate(1); forrige.setMonth(forrige.getMonth() - 1);
  const TIL = opt('--til') ?? `${forrige.getFullYear()}-${String(forrige.getMonth() + 1).padStart(2, '0')}`;
  const FRA = opt('--fra') ?? TIL;
  if (!/^\d{4}-\d{2}$/.test(TIL ?? '') || !/^\d{4}-\d{2}$/.test(FRA) || FRA > TIL) throw new Error('--til (og --fra) må være ÅÅÅÅ-MM.');
  const UT = resolve(opt('--ut') ?? standardUt('bilag', TIL));
  mkdirSync(join(UT, 'docs'), { recursive: true });

  const mottak = await c.list('/ledger/voucher/>voucherReception', { query: {
    fields: 'id,date,description,vendorInvoiceNumber,attachment(id,fileName,mimeType),ediDocument(id),postings(amountGross)',
  } });
  const ehf = mottak.filter((v) => v.ediDocument);
  const docs = mottak.filter((v) => !v.ediDocument);
  // Sekvensielt: tokenfornyingen tåler ikke parallelle kall.
  const { bank, utenFeed } = await umatchetBank(FRA, TIL);
  const hist = await historikk(TIL);
  const lev = await c.list('/supplier', { query: { fields: 'id,name,organizationNumber' } });
  writeFileSync(join(UT, 'historikk.tsv'), hist);
  writeFileSync(join(UT, 'leverandorer.tsv'), ['id\tnavn\torgnr', ...lev.map((s) => `${s.id}\t${redactText(s.name)}\t${s.organizationNumber ?? ''}`)].join('\n'));
  writeFileSync(join(UT, 'bank.json'), JSON.stringify(bank, null, 1));

  const forslag = [];
  const pdftotext = spawnSync('pdftotext', ['-v']).error ? null : 'pdftotext';
  for (const v of docs) {
    const d = { inbox: v.id, dato: v.date, fakturanr: v.vendorInvoiceNumber ?? null, filnavn: redactText(v.attachment?.fileName ?? ''), fil: null, txt: null, skann: false, belop: [], kandidater: [] };
    if (v.attachment?.id) {
      const ext = (v.attachment.fileName?.split('.').pop() || 'pdf').toLowerCase();
      d.fil = join(UT, 'docs', `${v.id}.${ext}`);
      if (!existsSync(d.fil)) await lastNed(v.attachment.id, d.fil);
      let tekst = '';
      if (ext === 'pdf' && pdftotext) {
        const p = spawnSync(pdftotext, ['-layout', '-enc', 'UTF-8', d.fil, '-'], { encoding: 'utf8' });
        tekst = p.stdout ?? '';
      }
      d.skann = tekst.replace(/\s/g, '').length < 40;
      if (!d.skann) { d.txt = d.fil.replace(/\.[^.]+$/, '.txt'); writeFileSync(d.txt, redactText(tekst)); }
      d.belop = belopITekst(tekst);
    }
    for (const p of v.postings ?? []) if (p.amountGross) d.belop.push(Math.abs(p.amountGross));
    const sett = [...new Set(d.belop.map(r2))];
    d.kandidater = bank
      .filter((t) => sett.some((n) => Math.abs(Math.abs(t.belop) - n) < 0.015))
      .map((t) => ({ ...t, dagerEtter: v.date ? dager(t.dato, v.date) : null }))
      .sort((a, b) => Math.abs(a.dagerEtter ?? 999) - Math.abs(b.dagerEtter ?? 999))
      .slice(0, 4);
    d.belop = sett.sort((a, b) => b - a).slice(0, 8);
    forslag.push(d);
  }
  writeFileSync(join(UT, 'forslag.json'), JSON.stringify(forslag, null, 1));

  const medTreff = forslag.filter((f) => f.kandidater.length);
  console.log(`${c.company.name} ${FRA}${FRA !== TIL ? `–${TIL}` : ''}: bilagsmottak ${mottak.length} (EHF ${ehf.length} hoppet over), ` +
    `umatchede bankposter ${bank.length}, dokumenter med beløpstreff i bank ${medTreff.length}, skannede (les PDF) ${forslag.filter((f) => f.skann).length}`);
  if (utenFeed.length) console.log(`Bankkontoer uten bankfeed i perioden: ${utenFeed.join(', ')} – motpost bare fra vedlagt kontoutskrift.`);
  console.log(`Filer i ${UT}: forslag.json, bank.json, historikk.tsv, leverandorer.tsv, docs/`);
}

// ── før ─────────────────────────────────────────────────────────────────────
async function foer() {
  const PLAN = resolve(opt('--plan') ?? '');
  if (!existsSync(PLAN)) throw new Error('--plan <plan.json> mangler.');
  const BEKREFT = flag('--bekreft');
  const bare = opt('--bare')?.split(',').map(Number);
  const plan = JSON.parse(readFileSync(PLAN, 'utf8')).filter((p) => !bare || bare.includes(p.inbox));
  const logF = PLAN.replace(/\.json$/, '') + '.resultat.json';
  const log = existsSync(logF) ? JSON.parse(readFileSync(logF, 'utf8')) : {};
  const lagre = () => writeFileSync(logF, JSON.stringify(log, null, 1));
  const docsDir = join(dirname(PLAN), 'docs');

  const konto = async (n) => { const a = await slå('/ledger/account', { number: n, fields: 'id' }); if (!a) throw new Error(`konto ${n} finnes ikke`); return { id: a.id }; };
  const mva = async (n) => {
    if (!n) return { id: 0 }; // ingen mvabehandling
    const v = await slå('/ledger/vatType', { number: n, fields: 'id' });
    if (!v) throw new Error(`mva-kode ${n} ikke funnet`);
    return { id: v.id };
  };
  const kurs = async (kode, dato) => {
    const cur = await slå('/currency', { code: kode, fields: 'id' });
    const { value } = await c.request(`/currency/${cur.id}/rate`, { query: { date: dato, fields: 'rate' } });
    return value.rate;
  };
  const dokFil = (id) => readdirSync(docsDir).find((f) => f.startsWith(`${id}.`) && !f.endsWith('.txt'));

  async function postinger(p, L) {
    const lin = [];
    const dim = { ...(p.leverandor ? { supplier: { id: p.leverandor } } : {}) };
    const add = async (k, belop, ekstra = {}) => lin.push({
      row: lin.length + 1, date: p.dato, description: p.beskrivelse, account: await konto(k),
      amountGross: r2(belop), amountGrossCurrency: r2(belop), vatType: await mva(ekstra.mva ?? 0),
      ...dim, ...(ekstra.prosjekt ? { project: { id: ekstra.prosjekt } } : {}), ...(ekstra.avdeling ? { department: { id: ekstra.avdeling } } : {}),
      ...(ekstra.fakturanr ? { invoiceNumber: String(ekstra.fakturanr) } : {}),
    });
    if (p.valuta && p.valuta !== 'NOK') L.kurs ??= await kurs(p.valuta, p.dato);
    let kost = 0;
    for (const l of p.linjer) { const b = L.kurs ? r2(l.belop * L.kurs) : l.belop; kost = r2(kost + b); await add(l.konto, b, l); }
    const bank = -p.belop;
    if (L.kurs && Math.abs(bank - kost) > 0.004) { await add(bank > kost ? 8160 : 8060, r2(bank - kost)); kost = bank; }
    if (Math.abs(kost - bank) > 0.004) throw new Error(`linjene (${kost}) ≠ bankbeløpet (${bank})`);
    if (p.leverandor) { await add(2400, -kost, { fakturanr: p.fakturanr }); await add(2400, bank); }
    await add(p.bankkonto ?? 1920, p.belop);
    return lin;
  }

  async function avstemming(kontoNr, dato) {
    const a = await konto(kontoNr);
    const per = await slå('/ledger/accountingPeriod', { startFrom: `${dato.slice(0, 7)}-01`, startTo: nesteMnd(dato.slice(0, 7)), fields: 'id' });
    if (!per) return null;
    return slå('/bank/reconciliation', { accountId: a.id, accountingPeriodId: per.id, fields: 'id,isClosed' });
  }

  const mottak = new Set((await c.list('/ledger/voucher/>voucherReception', { query: { fields: 'id' } })).map((v) => v.id));
  for (const p of plan) {
    const L = (log[p.inbox] ??= {});
    try {
      const ider = [p.inbox, ...(p.flere ?? [])]; // flere: kvittering + faktura for samme kjøp på ett bilag
      const filer = ider.map((id) => [id, dokFil(id)]);
      for (const [id, f] of filer) {
        if (!f) throw new Error(`dokument ${id} mangler i docs/ – kjør hent først`);
        if (!L.voucherId && !mottak.has(id)) throw new Error(`dokument ${id} ligger ikke lenger i bilagsmottaket`);
      }
      const lin = await postinger(p, L);
      if (!BEKREFT) {
        console.log(`TØRR ${p.inbox} ${p.dato} ${p.belop}: ${lin.map((x) => `${x.amountGross}`).join(' / ')} | vedlegg ${filer.map((f) => f[1]).join(' + ')}${p.bankTx ? ` | match tx ${p.bankTx}` : ''}`);
        continue;
      }
      if (!L.voucherId) {
        const { value } = await c.request('/ledger/voucher', { method: 'POST', query: { sendToLedger: true, fields: 'id,number,year' },
          body: { date: p.dato, description: p.beskrivelse, ...(p.fakturanr ? { vendorInvoiceNumber: String(p.fakturanr) } : {}), postings: lin } });
        L.voucherId = value.id; L.nummer = `${value.number}-${value.year}`; lagre();
      }
      L.vedlegg = Array.isArray(L.vedlegg) ? L.vedlegg : [];
      for (const [id, fil] of filer) {
        if (L.vedlegg.includes(id)) continue;
        await lastOppVedlegg(L.voucherId, join(docsDir, fil));
        L.vedlegg.push(id); lagre();
      }
      if (p.leverandor && !L.lukket) {
        const { value: v } = await c.request(`/ledger/voucher/${L.voucherId}`, { query: { fields: 'postings(id,account(number),amountGross)' } });
        const lev = v.postings.filter((x) => x.account.number === 2400);
        if (Math.abs(lev.reduce((t, x) => t + x.amountGross, 0)) < 0.005) {
          await c.request('/ledger/posting/:closePostings', { method: 'PUT', body: lev.map((x) => x.id) });
          L.lukket = true; lagre();
        }
      }
      if (p.bankTx && !L.matchet) {
        L.txDato ??= (await c.request(`/bank/statement/transaction/${p.bankTx}`, { query: { fields: 'postedDate' } })).value.postedDate;
        const rec = await avstemming(p.bankkonto ?? 1920, L.txDato);
        const { value: v } = await c.request(`/ledger/voucher/${L.voucherId}`, { query: { fields: 'postings(id,account(number))' } });
        const bp = v.postings.find((x) => x.account.number === (p.bankkonto ?? 1920));
        if (!rec) L.match = 'ingen bankavstemming for måneden – match i Tripletex';
        else if (rec.isClosed) L.match = 'bankavstemmingen er lukket – ikke matchet';
        else {
          await c.request('/bank/reconciliation/match', { method: 'POST', query: { fields: 'id' },
            body: { bankReconciliation: { id: rec.id }, type: 'MANUAL', transactions: [{ id: p.bankTx }], postings: [{ id: bp.id }] } });
          L.matchet = true; delete L.match;
        }
        lagre();
      }
      // Kopien i mottaket slettes bare når akkurat det dokumentet er bekreftet lastet opp på det nye bilaget.
      L.slettet ??= [];
      for (const id of ider) {
        if (L.slettet.includes(id) || !L.vedlegg.includes(id) || !mottak.has(id)) continue;
        await c.request(`/ledger/voucher/${id}`, { method: 'DELETE' });
        L.slettet.push(id); lagre();
      }
      L.ok = true; delete L.feil; lagre();
      console.log(`OK ${p.inbox} → bilag ${L.nummer} ${p.dato} ${p.belop}${L.kurs ? ` kurs ${L.kurs}` : ''}${L.matchet ? ' matchet' : L.match ? ` (${L.match})` : ''}${L.lukket ? ' 2400 lukket' : ''}`);
    } catch (e) {
      L.feil = e.message.slice(0, 400); lagre();
      console.log(`FEIL ${p.inbox}: ${redactText(L.feil)}`);
    }
  }
  if (!BEKREFT) console.log('Tørrkjøring – ingenting er ført. Kjør med --bekreft etter ja.');
}

// ── manuell ─────────────────────────────────────────────────────────────────
const MND_PER_TERMIN = { ONE_MONTH: 1, TWO_MONTHS: 2, THREE_MONTHS: 3, FOUR_MONTHS: 4, SIX_MONTHS: 6, YEAR: 12 };
const MVA_LEVERT = new Set(['SENDING', 'WAITING_FOR_REPLY', 'RECEIPT_RECEIVED', 'MANUAL_DELIVERY']);
const kr = (x) => { const [h, d] = Math.abs(x).toFixed(2).split('.'); return `${x < 0 ? '-' : ''}${h.replace(/\B(?=(\d{3})+(?!\d))/g, ' ')},${d}`; };
const erDato = (s) => typeof s === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(s) && !Number.isNaN(Date.parse(`${s}T00:00:00Z`)) &&
  new Date(`${s}T00:00:00Z`).toISOString().slice(0, 10) === s;
const dagEtter = (s) => new Date(Date.parse(`${s}T00:00:00Z`) + 86_400_000).toISOString().slice(0, 10);
const erId = (x) => Number.isInteger(Number(x)) && Number(x) > 0;

/** Objekt på id, eller null ved 404. */
async function objekt(sti, id, fields) {
  try { return await verdi(`${sti}/${id}`, { fields }); } catch (e) { if (/feilet \(404\)/.test(e.message)) return null; throw e; }
}

async function manuell() {
  const PLAN = resolve(opt('--plan') ?? '');
  if (!existsSync(PLAN)) throw new Error('--plan <manuell.json> mangler.');
  const BEKREFT = flag('--bekreft');
  const V = opt('--vesentlighet') === undefined ? null : Number(String(opt('--vesentlighet')).replace(/\s/g, '').replace(',', '.'));
  if (V !== null && !(V > 0)) throw new Error('--vesentlighet må være et beløp større enn 0.');
  const alle = JSON.parse(readFileSync(PLAN, 'utf8'));
  if (!Array.isArray(alle)) throw new Error('planen må være en liste av bilag.');
  const bare = opt('--bare')?.split(',').map((s) => s.trim()).filter(Boolean);
  const plan = alle.filter((p) => !bare || bare.includes(String(p.ref)));
  const ukjente = (bare ?? []).filter((r) => !plan.some((p) => String(p.ref) === r));
  if (ukjente.length) throw new Error(`--bare: ref ikke funnet i planen: ${ukjente.join(', ')}`);
  const logF = PLAN.replace(/\.json$/, '') + '.resultat.json';
  const log = existsSync(logF) ? JSON.parse(readFileSync(logF, 'utf8')) : {};
  const lagre = () => writeFileSync(logF, JSON.stringify(log, null, 1));
  const idag = new Date().toISOString().slice(0, 10);

  // Klientoppslag (lesing, hurtigbuffer).
  const kontoInfo = (n) => slå('/ledger/account', { number: n,
    fields: 'id,number,isInactive,isBankAccount,vatLocked,vatType(number),legalVatTypes(number),requiresDepartment,requiresProject,ledgerType' });
  const mvaId = async (kode) => (kode === '0' ? { id: 0 } : slå('/ledger/vatType', { number: kode, fields: 'id,number' }));
  const periode = (mnd) => slå('/ledger/accountingPeriod', { startFrom: `${mnd}-01`, startTo: nesteMnd(mnd), fields: 'id,start,isClosed' });
  let mvaReg;
  const mvaRegistrert = async () => {
    if (mvaReg === undefined) {
      try { mvaReg = (await verdi('/ledger/vatSettings', { fields: 'vatRegistrationStatus' }))?.vatRegistrationStatus ?? null; } catch { mvaReg = null; }
    }
    return mvaReg; // VAT_REGISTERED, VAT_NOT_REGISTERED … eller null (ikke avklart)
  };
  async function mvaTermin(dato) {
    const rader = (await slåAlle('/vatTermSizeSettings', { fields: 'reportType,fromDate,termSize', sorting: 'fromDate' }))
      .filter((t) => t.reportType === 'GENERAL_INDUSTRY' && t.fromDate <= dato);
    const mnd = MND_PER_TERMIN[rader.at(-1)?.termSize] ?? 2;
    const aar = Number(dato.slice(0, 4)), termin = Math.ceil(Number(dato.slice(5, 7)) / mnd);
    const s = await verdi('/vatReturns/status', { year: aar, term: termin, fields: 'voucherNumber,deliveryStatus(status)' });
    return { navn: `${termin}/${aar}`, levert: (s?.voucherNumber ?? 0) > 0 || MVA_LEVERT.has(s?.deliveryStatus?.status) };
  }
  const hb = new Map();
  const hovedbok = async (dato) => {
    if (!hb.has(dato)) hb.set(dato, await c.list('/ledger/posting', { query: { dateFrom: dato, dateTo: dagEtter(dato),
      fields: 'account(number),amountGross,voucher(id,number,year)' } }));
    return hb.get(dato);
  };

  // Regnskapsperiode, bankavstemming (bankkontoer) og mva-termin (linjer med mva) for én dato. Brukes for dato (J2) og tilbakefor (J8).
  async function periodeSjekk(dato, linjer) {
    const ut = [];
    const mnd = dato.slice(0, 7);
    const per = await periode(mnd);
    if (!per) return [['FEIL', `ingen regnskapsperiode for ${mnd}`]];
    if (per.isClosed) ut.push(['FEIL', `periode ${mnd} er lukket`]);
    for (const n of [...new Set(linjer.filter((l) => l.info?.isBankAccount).map((l) => l.konto))]) {
      const info = linjer.find((l) => l.konto === n).info;
      const rec = await slåAlle('/bank/reconciliation', { accountId: info.id, accountingPeriodId: per.id, fields: 'id,isClosed' });
      if (rec.some((r) => r.isClosed)) ut.push(['FEIL', `bankavstemmingen for ${n} i ${mnd} er lukket`]);
    }
    if (linjer.some((l) => l.kode && l.kode !== '0') && (await mvaRegistrert()) === 'VAT_REGISTERED') {
      const t = await mvaTermin(dato);
      if (t.levert) ut.push(['FEIL', `mva-termin ${t.navn} er levert – rettes i inneværende termin`]);
    }
    return ut;
  }

  const refTeller = new Map();
  for (const p of alle) refTeller.set(String(p.ref ?? ''), (refTeller.get(String(p.ref ?? '')) ?? 0) + 1);
  const fingeravtrykk = (p) => JSON.stringify([p.dato, (p.linjer ?? []).map((l) => [Number(l.konto), r2(Number(l.belop))]), p.tilbakefor ?? null]);

  async function kontroller(p, L) {
    const J = [];
    const sett = (id, status, tekst) => J.push({ id, status, tekst });
    const rader = Array.isArray(p.linjer) ? p.linjer : [];
    const linjer = rader.map((l) => ({ ...l, konto: Number(l.konto), belop: r2(Number(l.belop)), kode: l.mva == null ? null : String(l.mva) }));
    const debet = r2(linjer.filter((l) => l.belop > 0).reduce((s, l) => s + l.belop, 0));
    const kredit = r2(-linjer.filter((l) => l.belop < 0).reduce((s, l) => s + l.belop, 0));
    const steg = async (id, fn) => { try { await fn(); } catch (e) { sett(id, 'FEIL', `kunne ikke kontrolleres: ${kortFeil(e)}`); } };

    // J1 sum = 0
    const ugyldige = linjer.filter((l) => !Number.isInteger(l.konto) || !Number.isFinite(l.belop) || l.belop === 0);
    if (linjer.length < 2) sett('J1', 'FEIL', 'bilaget må ha minst to linjer');
    else if (ugyldige.length) sett('J1', 'FEIL', `${ugyldige.length} linje(r) med ugyldig konto eller beløp som mangler/er 0`);
    else if (p.valuta && p.valuta !== 'NOK') sett('J1', 'FEIL', 'valuta støttes ikke i manuell – før i NOK');
    else if (Math.abs(debet - kredit) > 0.004) sett('J1', 'FEIL', `sum ≠ 0: debet ${kr(debet)}, kredit ${kr(kredit)}, differanse ${kr(r2(debet - kredit))}`);
    else sett('J1', 'PASS', `sum 0 (debet = kredit = ${kr(debet)})`);

    // J3 kontoer finnes og er aktive (først – de andre kontrollene trenger kontoinfo)
    await steg('J3', async () => {
      const feil = [];
      for (const l of linjer.filter((x) => Number.isInteger(x.konto))) {
        l.info = await kontoInfo(l.konto);
        if (!l.info) feil.push(`konto ${l.konto} ikke funnet`);
        else if (l.info.isInactive) feil.push(`konto ${l.konto} er inaktiv`);
      }
      if (feil.length) sett('J3', 'FEIL', [...new Set(feil)].join('; '));
      else sett('J3', 'PASS', `${new Set(linjer.map((l) => l.konto)).size} kontoer finnes og er aktive`);
    });

    // J4 mva-kode finnes og passer kontoen (før J2, som trenger kodene)
    await steg('J4', async () => {
      const feil = [], adv = [];
      for (const l of linjer.filter((x) => x.info)) {
        if (l.kode == null) l.kode = l.info.vatLocked ? String(l.info.vatType?.number ?? '0') : '0';
        if (l.info.vatLocked && l.kode !== String(l.info.vatType?.number ?? '0')) feil.push(`konto ${l.konto} er låst til mva-kode ${l.info.vatType?.number}`);
        const lovlige = (l.info.legalVatTypes ?? []).map((v) => String(v.number));
        if (lovlige.length && !lovlige.includes(l.kode)) feil.push(`mva-kode ${l.kode} er ikke lovlig på konto ${l.konto}`);
        l.vatType = await mvaId(l.kode);
        if (!l.vatType) feil.push(`mva-kode ${l.kode} ikke funnet`);
        if (l.kode !== '0') {
          const reg = await mvaRegistrert();
          if (reg === null) adv.push('mva-registrering ikke avklart');
          else if (reg !== 'VAT_REGISTERED') feil.push(`klienten er ikke mva-registrert (kode ${l.kode} på ${l.konto})`);
        }
      }
      if (feil.length) sett('J4', 'FEIL', [...new Set(feil)].join('; '));
      for (const t of new Set(adv)) sett('J4', 'ADVARSEL', t);
      if (!feil.length && !adv.length) sett('J4', 'PASS', `mva-koder ${[...new Set(linjer.map((l) => l.kode ?? '0'))].join(', ')}`);
    });

    // J2 åpen periode
    await steg('J2', async () => {
      if (!erDato(p.dato)) return sett('J2', 'FEIL', 'dato mangler eller er ugyldig (ÅÅÅÅ-MM-DD)');
      const funn = await periodeSjekk(p.dato, linjer);
      if (p.dato > idag) funn.push(['ADVARSEL', `dato ${p.dato} er frem i tid`]);
      for (const [s, t] of funn) sett('J2', s, t);
      if (!funn.length) sett('J2', 'PASS', `${p.dato.slice(0, 7)} åpen${linjer.some((l) => l.info?.isBankAccount) ? ', bankavstemmingen åpen' : ''}`);
    });

    // J5 avdeling og prosjekt finnes (og påkrevd dimensjon er satt)
    await steg('J5', async () => {
      const feil = [];
      for (const l of linjer) {
        if (l.avdeling != null) {
          const d = erId(l.avdeling) ? await objekt('/department', l.avdeling, 'id,isInactive') : null;
          if (!d) feil.push(`avdeling-id ${l.avdeling} ikke funnet (bruk id, ikke avdelingsnummer)`);
          else if (d.isInactive) feil.push(`avdeling ${l.avdeling} er inaktiv`);
        } else if (l.info?.requiresDepartment) feil.push(`konto ${l.konto} krever avdeling`);
        if (l.prosjekt != null) {
          // isClosed kommer ikke alltid med på /project/{id}; filteret på listen er pålitelig.
          const pr = erId(l.prosjekt) ? await objekt('/project', l.prosjekt, 'id') : null;
          if (!pr) feil.push(`prosjekt-id ${l.prosjekt} ikke funnet`);
          else if ((await slåAlle('/project', { id: l.prosjekt, isClosed: true, fields: 'id' })).length) feil.push(`prosjekt ${l.prosjekt} er lukket`);
        } else if (l.info?.requiresProject) feil.push(`konto ${l.konto} krever prosjekt`);
      }
      const brukt = linjer.some((l) => l.avdeling != null || l.prosjekt != null);
      if (feil.length) sett('J5', 'FEIL', [...new Set(feil)].join('; '));
      else sett('J5', 'PASS', brukt ? 'avdeling/prosjekt finnes' : 'ingen avdeling/prosjekt (ikke påkrevd)');
    });

    // J6 reskontropart: kunde på kundereskontro (1500), leverandør på leverandørreskontro (2400)
    let leverandor = null;
    await steg('J6', async () => {
      const feil = [], adv = [];
      const levIder = [...new Set(linjer.filter((l) => l.leverandor != null).map((l) => String(l.leverandor)))];
      const harKunde = linjer.some((l) => l.kunde != null);
      if (levIder.length > 1) feil.push('flere leverandører i samme bilag – Tripletex krever samme leverandør på alle linjene; del bilaget');
      if (levIder.length && harKunde) feil.push('kunde og leverandør i samme bilag – del bilaget');
      leverandor = levIder.length === 1 ? Number(levIder[0]) : null;
      for (const l of linjer) {
        const type = l.info?.ledgerType;
        if (type === 'EMPLOYEE') feil.push(`konto ${l.konto} er ansattreskontro – før i Tripletex-UI`);
        if ((type === 'CUSTOMER' || l.konto === 1500) && l.kunde == null) feil.push(`konto ${l.konto} krever kunde`);
        if ((type === 'VENDOR' || l.konto === 2400) && !levIder.length) feil.push(`konto ${l.konto} krever leverandør`);
        if (l.kunde != null) {
          const k = erId(l.kunde) ? await objekt('/customer', l.kunde, 'id,isInactive') : null;
          if (!k) feil.push(`kunde-id ${l.kunde} ikke funnet`); else if (k.isInactive) adv.push(`kunde ${l.kunde} er inaktiv`);
        }
      }
      if (levIder.length === 1) {
        const s = erId(levIder[0]) ? await objekt('/supplier', levIder[0], 'id,isInactive') : null;
        if (!s) feil.push(`leverandør-id ${levIder[0]} ikke funnet`); else if (s.isInactive) adv.push(`leverandør ${levIder[0]} er inaktiv`);
      }
      if (feil.length) sett('J6', 'FEIL', [...new Set(feil)].join('; '));
      for (const t of new Set(adv)) sett('J6', 'ADVARSEL', t);
      if (!feil.length && !adv.length) {
        sett('J6', 'PASS', leverandor ? 'leverandør finnes – settes på alle linjene' : harKunde ? 'kunde finnes' : 'ingen reskontrokontoer');
      }
    });

    // J7 mulig dublett: ref i plan/logg, samme dato+konto+beløp i hovedboken eller i planen
    await steg('J7', async () => {
      const ref = String(p.ref ?? '').trim();
      if (!ref) return sett('J7', 'FEIL', 'ref mangler');
      if (refTeller.get(String(p.ref)) > 1) sett('J7', 'FEIL', `ref ${ref} er brukt flere ganger i planen`);
      if (L?.voucherId && L.fingeravtrykk && L.fingeravtrykk !== fingeravtrykk(p)) {
        sett('J7', 'FEIL', `ref er påbegynt som bilag ${L.nummer} med annet innhold – rett bilaget i Tripletex eller bruk ny ref`);
      }
      const funn = new Set();
      if (erDato(p.dato)) {
        const egne = new Set([L?.voucherId, L?.reverseringId].filter(Boolean));
        for (const x of await hovedbok(p.dato)) {
          if (egne.has(x.voucher?.id)) continue;
          if (linjer.some((l) => l.konto === x.account?.number && Math.abs(l.belop - (x.amountGross ?? 0)) < 0.005)) {
            funn.add(`bilag ${x.voucher?.number}-${x.voucher?.year} (konto ${x.account.number}, ${kr(x.amountGross)})`);
          }
        }
      }
      for (const q of alle) {
        if (q === p || q.dato !== p.dato) continue;
        if ((q.linjer ?? []).some((m) => linjer.some((l) => l.konto === Number(m.konto) && Math.abs(l.belop - Number(m.belop)) < 0.005))) {
          funn.add(`${String(q.ref)} i planen`);
        }
      }
      if (funn.size) sett('J7', 'ADVARSEL', `mulig dublett, samme dato, konto og beløp: ${[...funn].slice(0, 3).join('; ')}${funn.size > 3 ? ` (+${funn.size - 3})` : ''}`);
      if (!J.some((x) => x.id === 'J7')) sett('J7', 'PASS', `ingen treff på ${p.dato} i hovedboken eller planen`);
    });

    // J8 tilbakeføring: etter dato og i åpen periode; påløpt kostnad (296x) uten tilbakeføring flagges
    await steg('J8', async () => {
      if (p.tilbakefor == null) {
        if (linjer.some((l) => l.konto >= 2960 && l.konto <= 2969)) sett('J8', 'ADVARSEL', 'påløpt kostnad (296x) uten tilbakefor – sjekk at den reverseres');
        else sett('J8', 'PASS', 'ingen tilbakeføring');
        return;
      }
      if (!erDato(p.tilbakefor)) return sett('J8', 'FEIL', 'tilbakefor er ugyldig (ÅÅÅÅ-MM-DD)');
      if (erDato(p.dato) && p.tilbakefor <= p.dato) return sett('J8', 'FEIL', `tilbakefor ${p.tilbakefor} må være etter dato ${p.dato}`);
      const funn = await periodeSjekk(p.tilbakefor, linjer);
      for (const [s, t] of funn) sett('J8', s, `tilbakeføring: ${t}`);
      if (!funn.length) sett('J8', 'PASS', `tilbakeføres ${p.tilbakefor}, perioden er åpen`);
    });

    // J9 over vesentlighetsgrensen V
    if (V === null) sett('J9', 'ADVARSEL', 'ikke vurdert: --vesentlighet mangler');
    else if (debet > V) sett('J9', 'ADVARSEL', `sum ${kr(debet)} over V (${kr(V)}) – begrunn beløpet`);
    else sett('J9', 'PASS', `sum ${kr(debet)} under V (${kr(V)})`);

    // J10 runde beløp (hele tusen) – INFO, krever ingenting
    const runde = [...new Set(linjer.filter((l) => Math.abs(l.belop) >= 1000 && Math.abs(l.belop) % 1000 === 0).map((l) => Math.abs(l.belop)))];
    if (runde.length) sett('J10', 'INFO', `runde beløp ${runde.map(kr).join(', ')} – sjekk at beløpet er beregnet`);
    else sett('J10', 'PASS', 'ingen runde beløp');

    // J11 vedlegg finnes (bokf.l. § 10: dokumentasjon av bokførte opplysninger)
    const vedlegg = (Array.isArray(p.vedlegg) ? p.vedlegg : p.vedlegg ? [p.vedlegg] : []).map((f) => resolve(dirname(PLAN), String(f)));
    if (!vedlegg.length) sett('J11', 'ADVARSEL', 'uten vedlegg – legg ved beregningsgrunnlag (bokf.l. § 10)');
    else {
      const feil = vedlegg.flatMap((f) => (!existsSync(f) ? [`${redactText(basename(f))} ikke funnet`]
        : !/\.(pdf|png|jpe?g|tiff?)$/i.test(f) ? [`${redactText(basename(f))}: bare PDF, PNG, JPEG eller TIFF`] : []));
      if (feil.length) sett('J11', 'FEIL', feil.join('; '));
      else sett('J11', 'PASS', `${vedlegg.length} vedlegg finnes`);
    }

    // J12 beskrivelse
    const besk = String(p.beskrivelse ?? '').trim();
    if (!besk) sett('J12', 'FEIL', 'beskrivelse mangler');
    else if (besk.length < 10) sett('J12', 'ADVARSEL', 'beskrivelsen er kort – skriv hva og hvorfor');
    else sett('J12', 'PASS', 'beskrivelse finnes');

    J.sort((a, b) => Number(a.id.slice(1)) - Number(b.id.slice(1)));
    const harFeil = J.some((x) => x.status === 'FEIL');
    const postinger = harFeil ? null : linjer.map((l, i) => ({
      row: i + 1, date: p.dato, description: String(l.tekst ?? '').trim() || besk, account: { id: l.info.id },
      amountGross: l.belop, amountGrossCurrency: l.belop, vatType: { id: l.vatType.id },
      ...(leverandor ? { supplier: { id: leverandor } } : {}), ...(l.kunde != null ? { customer: { id: Number(l.kunde) } } : {}),
      ...(l.avdeling != null ? { department: { id: Number(l.avdeling) } } : {}), ...(l.prosjekt != null ? { project: { id: Number(l.prosjekt) } } : {}),
    }));
    return { J, linjer, debet, kredit, vedlegg, harFeil, postinger };
  }

  function vis(p, k, L) {
    console.log(`\n${String(p.ref ?? '(uten ref)')}  ${p.dato ?? '?'}${p.tilbakefor ? `  tilbakefor ${p.tilbakefor}` : ''}  vedlegg ${k.vedlegg.length}` +
      `${L?.voucherId ? `  (påbegynt: bilag ${L.nummer} finnes)` : ''}`);
    console.log(`  ${'konto'.padEnd(6)}${'debet'.padStart(14)}${'kredit'.padStart(14)}${'mva'.padStart(7)}${'avd'.padStart(10)}${'prosj'.padStart(11)}  part`);
    for (const l of k.linjer) {
      console.log(`  ${String(Number.isInteger(l.konto) ? l.konto : '?').padEnd(6)}${(l.belop > 0 ? kr(l.belop) : '').padStart(14)}${(l.belop < 0 ? kr(-l.belop) : '').padStart(14)}` +
        `${String(l.kode ?? '0').padStart(7)}${String(l.avdeling ?? '').padStart(10)}${String(l.prosjekt ?? '').padStart(11)}  ${l.kunde != null ? 'kunde' : l.leverandor != null ? 'lev' : ''}`);
    }
    console.log(`  ${'sum'.padEnd(6)}${kr(k.debet).padStart(14)}${kr(k.kredit).padStart(14)}`);
    for (const x of k.J) console.log(`  ${x.status.padEnd(9)}${x.id.padEnd(5)}${redactText(x.tekst)}`);
  }

  // Skrivekall som ikke skal gjentas: blir et kall avbrutt uten svar (nettverk), stoppes neste kjøring til hovedboken er sjekket.
  async function engang(L, steg, fn, noter) {
    if (L.avbrutt === steg) throw new Error(`forrige ${steg} ble avbrutt uten svar – sjekk hovedboken, fjern «avbrutt» i resultatfila og kjør på nytt`);
    L.avbrutt = steg; lagre();
    let r;
    try { r = await fn(); } catch (e) {
      if (/feilet \(\d{3}\)/.test(e.message)) { delete L.avbrutt; lagre(); } // svar fra Tripletex = ikke utført
      throw e;
    }
    noter(r); delete L.avbrutt; lagre(); // id-en lagres før markøren fjernes
  }

  const status = { ok: [], advarsel: [], feil: [], ferdig: [], stoppet: [] };
  for (const p of plan) {
    const ref = String(p.ref ?? '');
    const L0 = log[ref];
    if (L0?.ok) {
      const endret = L0.fingeravtrykk && L0.fingeravtrykk !== fingeravtrykk(p);
      console.log(`\n${ref}  FERDIG → bilag ${L0.nummer}${L0.reversering ? `, reversering ${L0.reversering}` : ''}\n` +
        `  ${'INFO'.padEnd(9)}${'J7'.padEnd(5)}ref ferdig i loggen – hoppes over` +
        (endret ? `\n  ${'ADVARSEL'.padEnd(9)}${'J7'.padEnd(5)}planen er endret etter føring – bruk ny ref for et nytt bilag` : ''));
      status.ferdig.push(ref);
      continue;
    }
    let k;
    try { k = await kontroller(p, L0); } catch (e) {
      console.log(`\nFEIL ${ref}: ${redactText(kortFeil(e))}`); status.feil.push(ref); continue;
    }
    if (!BEKREFT) {
      vis(p, k, L0);
      (k.harFeil ? status.feil : k.J.some((x) => x.status === 'ADVARSEL') ? status.advarsel : status.ok).push(ref);
      continue;
    }
    if (k.harFeil) {
      vis(p, k, L0);
      console.log(`  STOPPET ${ref}: FEIL i ${[...new Set(k.J.filter((x) => x.status === 'FEIL').map((x) => x.id))].join(', ')} – ` +
        (L0?.voucherId ? `bilag ${L0.nummer} finnes, resten (vedlegg/reversering) er ikke gjort` : 'ikke ført'));
      status.stoppet.push(ref);
      continue;
    }
    const L = (log[ref] ??= {});
    try {
      L.kontroll = { advarsel: [...new Set(k.J.filter((x) => x.status === 'ADVARSEL').map((x) => x.id))] };
      if (!L.voucherId) {
        await engang(L, 'oppretting', async () => (await c.request('/ledger/voucher', { method: 'POST',
          query: { sendToLedger: true, fields: 'id,number,year' }, body: { date: p.dato, description: String(p.beskrivelse).trim(), postings: k.postinger } })).value,
        (v) => Object.assign(L, { voucherId: v.id, nummer: `${v.number}-${v.year}`, dato: p.dato, sum: k.debet, fingeravtrykk: fingeravtrykk(p) }));
      }
      if (!L.lestTilbake) {
        // Tilbakelesing: hver planlinje (konto, brutto) skal finnes på bilaget; ekstra linjer er bare tillatt på 27xx (mva).
        const { value: v } = await c.request(`/ledger/voucher/${L.voucherId}`, { query: { fields: 'postings(account(number),amountGross)' } });
        const igjen = [...(v.postings ?? [])];
        const mangler = k.linjer.filter((l) => {
          const i = igjen.findIndex((x) => x.account?.number === l.konto && Math.abs((x.amountGross ?? 0) - l.belop) < 0.005);
          return i < 0 ? true : (igjen.splice(i, 1), false);
        });
        const ekstra = igjen.filter((x) => !(x.account?.number >= 2700 && x.account?.number <= 2799));
        if (mangler.length || ekstra.length) throw new Error(`tilbakelesing: bilag ${L.nummer} avviker fra planen (${mangler.length} mangler, ${ekstra.length} ekstra) – sjekk bilaget i Tripletex`);
        L.lestTilbake = true; lagre();
      }
      L.vedlegg = Array.isArray(L.vedlegg) ? L.vedlegg : [];
      for (const f of k.vedlegg) {
        if (L.vedlegg.includes(basename(f))) continue;
        await lastOppVedlegg(L.voucherId, f);
        L.vedlegg.push(basename(f)); lagre();
      }
      if (p.tilbakefor && !L.reverseringId) {
        await engang(L, 'reversering', async () => (await c.request(`/ledger/voucher/${L.voucherId}/:reverse`, { method: 'PUT',
          query: { date: p.tilbakefor, fields: 'id,number,year' } })).value,
        (v) => Object.assign(L, { reverseringId: v.id, tilbakefor: p.tilbakefor, reversering: v.number ? `${v.number}-${v.year}` : String(v.id) }));
      }
      L.ok = true; delete L.feil; lagre();
      console.log(`OK ${ref} → bilag ${L.nummer} ${p.dato} sum ${kr(k.debet)} | vedlegg ${L.vedlegg.length}` +
        `${L.reversering ? ` | reversering ${L.reversering} ${p.tilbakefor}` : ''}${L.kontroll.advarsel.length ? ` | ADVARSEL ${L.kontroll.advarsel.join(', ')}` : ''}`);
      status.ok.push(ref);
    } catch (e) {
      L.feil = redactText(kortFeil(e)); lagre();
      console.log(`FEIL ${ref}: ${L.feil}${L.voucherId ? ` (bilag ${L.nummer} er opprettet – kjør på nytt for resten)` : ' – ikke ført'}`);
      status.feil.push(ref);
    }
  }

  console.log('');
  if (!BEKREFT) {
    console.log(`Tørrkjøring: ${plan.length} bilag – ${status.ok.length} uten avvik, ${status.advarsel.length} med ADVARSEL, ` +
      `${status.feil.length} med FEIL${status.feil.length ? ` (${status.feil.join(', ')})` : ''}${status.ferdig.length ? `, ${status.ferdig.length} ferdige` : ''}. ` +
      'Ingenting er ført. Bilag med FEIL føres ikke; de andre føres med --bekreft etter ja.');
  } else {
    console.log(`Ført ${status.ok.length} av ${plan.length} bilag. Stoppet av kontroll: ${status.stoppet.length}. Feil: ${status.feil.length}. ` +
      `Ferdige fra før: ${status.ferdig.length}. Logg: ${basename(logF)}`);
  }
  if (status.feil.length || status.stoppet.length) process.exitCode = 1;
}

try {
  await (kommando === 'hent' ? hent() : kommando === 'manuell' ? manuell() : foer());
} catch (e) {
  console.error(`Feil: ${redactText(e.message.split('\n')[0].slice(0, 300))}`);
  process.exit(1);
}
