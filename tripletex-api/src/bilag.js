// Bilagsføring: dokumenter i bilagsmottaket mot åpne bankposter.
//
//   npm run -s bilag -- hent --client "Klient" --til 2026-09 [--fra 2026-08] [--ut <mappe>]     (kun lesing)
//   npm run -s bilag -- før  --client "Klient" --plan <mappe>/plan.json [--bare <id>,<id>] [--bekreft]
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
// GDPR: konsollen viser bare antall, beløp, konto og bilagsnummer. Tekst i filene er maskert med redactText().

import { mkdirSync, writeFileSync, readFileSync, existsSync, readdirSync } from 'node:fs';
import { join, resolve, dirname, basename } from 'node:path';
import { spawnSync } from 'node:child_process';
import { connect } from './tripletex.js';
import { BASE_URL, authorization } from './auth.js';
import { redactText } from './privacy.js';
import { standardUt } from './valg.js';

const args = process.argv.slice(2);
const kommando = args[0];
const opt = (n) => { const i = args.indexOf(n); return i >= 0 ? args[i + 1] : undefined; };
const flag = (n) => args.includes(n);
const r2 = (x) => Math.round(x * 100) / 100;
const nesteMnd = (m) => { const d = new Date(`${m}-01T00:00:00Z`); d.setUTCMonth(d.getUTCMonth() + 1); return d.toISOString().slice(0, 10); };
const dager = (a, b) => Math.round((new Date(a) - new Date(b)) / 86_400_000);

if (!['hent', 'før', 'for'].includes(kommando) || !opt('--client')) {
  console.error('Bruk: npm run -s bilag -- hent --client "Klient" --til ÅÅÅÅ-MM [--fra ÅÅÅÅ-MM] [--ut <mappe>]\n' +
    '      npm run -s bilag -- før  --client "Klient" --plan <plan.json> [--bare id,id] [--bekreft]\nIngenting er gjort.');
  process.exit(1);
}
const c = await connect(opt('--client'));

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

  const cache = new Map();
  const slå = async (sti, query) => {
    const k = sti + JSON.stringify(query);
    if (!cache.has(k)) cache.set(k, (await c.request(sti, { query })).values?.[0] ?? null);
    return cache.get(k);
  };
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
        const fd = new FormData();
        const type = fil.endsWith('.pdf') ? 'application/pdf' : fil.match(/\.(png|jpe?g)$/) ? `image/${fil.split('.').pop().replace('jpg', 'jpeg')}` : 'application/octet-stream';
        fd.append('file', new Blob([readFileSync(join(docsDir, fil))], { type }), basename(fil));
        const res = await fetch(`${BASE_URL}/ledger/voucher/${L.voucherId}/attachment`, { method: 'POST',
          headers: { Authorization: await authorization(c.company.id, c.company.account), Accept: 'application/json' }, body: fd });
        if (!res.ok) throw new Error(`vedlegg: ${res.status} ${(await res.text()).slice(0, 200)}`);
        const { value: v } = await c.request(`/ledger/voucher/${L.voucherId}`, { query: { fields: 'attachment(id)' } });
        if (!v.attachment?.id) throw new Error('vedlegget ligger ikke på bilaget etter opplasting');
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

try {
  await (kommando === 'hent' ? hent() : foer());
} catch (e) {
  console.error(`Feil: ${redactText(e.message.split('\n')[0].slice(0, 300))}`);
  process.exit(1);
}
