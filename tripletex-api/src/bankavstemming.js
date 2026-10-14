// Bankavstemming: status og åpne poster per bankkonto og måned – KUN LESING.
//
//   npm run -s bankavstemming -- --til 2026-08 --alle
//   npm run -s bankavstemming -- --til 2026-08 --client "Klient A" [--client "Klient B"]
//   Valg: --fra 2026-01 (standard: januar samme år)  --ut <mappe> (standard %TEMP%\rr\bankavstemming-<til>)
//         --excel (Silfer-Excel per klient med noe fra kunden, via .claude/skills/bankavstemming/scripts/lag_spec.py)
//
// Klassifisering per konto og måned (fra–til):
//   lukket   = avstemming finnes og er lukket.
//   åpen     = ikke lukket OG (avstemming finnes ELLER bevegelse ≠ 0 ELLER UB ≠ 0).
// For åpne måneder:
//   bankside      = umatchede banktransaksjoner (CSV-eksporten til avstemmingen; fallback kontoutskrift-
//                   transaksjoner når avstemming mangler). Dette er «mangler bilag» – går til kunden.
//   tripletexside = umatchede posteringer i hovedboka (antall/sum) – internt arbeid.
//   forslag       = matcheforslag som ikke er godkjent (antall/sum av banktransaksjonene) – internt arbeid.
// Per måned med avstemming: bankens sluttsaldo (bankSaldo) og differanse mot UB i hovedboka.
// Kontoer uten bankfeed (ingen AUTOMATIC-avstemming og ingen kontoutskrifter) med bevegelse i åpne
// måneder → kunden må sende kontoutskrift. Skattetrekkskonto holdes utenfor kundelisten.
//
// Utdata i --ut: status.json (alle klienter; per konto kontoId, per måned avstemmingId, bankposter med id der
// kontoutskriften har den – nok til å matche med `api -- POST /bank/reconciliation/match … --bekreft`),
// <Klient>.data.json (formatet lag_spec.py leser), oversikt .md.
// GDPR: banktekster skrives bare til data.json/status.json (kundens egne transaksjoner). Konsollutskriften
// viser kun antall og summer.

import { mkdirSync, writeFileSync } from 'node:fs';
import { join, dirname, resolve } from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { list } from './tripletex.js';
import { BASE_URL, authorization } from './auth.js';
import { argumenter, klientutvalg, utmappe, nesteMnd, maanederMellom, erMaaned, rund, kortFeil } from './valg.js';

const HER = dirname(fileURLToPath(import.meta.url));
const LAG_SPEC = resolve(HER, '..', '..', '.claude', 'skills', 'bankavstemming', 'scripts', 'lag_spec.py');
const MND = ['Januar', 'Februar', 'Mars', 'April', 'Mai', 'Juni', 'Juli', 'August', 'September', 'Oktober', 'November', 'Desember'];

const mndNavn = (m) => MND[Number(m.slice(5, 7)) - 1];
const kr = (n) => (n ?? 0).toLocaleString('nb-NO', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const erSkattetrekk = (k) => /skattetrekk/i.test(k.navn);
// «03.08.2026» eller «2026-08-03» → «2026-08-03»
const isoDato = (d) => { const s = String(d ?? '').trim(); const m = s.match(/^(\d{2})\.(\d{2})\.(\d{4})$/); return m ? `${m[3]}-${m[2]}-${m[1]}` : s.slice(0, 10); };

function mndListe(ms) {
  // ["2026-01","2026-02","2026-04"] -> "jan–feb, apr"
  const kort = (m) => mndNavn(m).slice(0, 3).toLowerCase();
  const grupper = [];
  for (const m of ms) {
    const g = grupper.at(-1);
    if (g && nesteMnd(g.at(-1)).startsWith(m)) g.push(m); else grupper.push([m]);
  }
  return grupper.map((g) => (g.length > 1 ? `${kort(g[0])}–${kort(g.at(-1))}` : kort(g[0]))).join(', ');
}

// ── CSV (Dato,Beløp,Beskrivelse,Detaljer) ───────────────────────────────────
function parseCsv(text) {
  const rows = [];
  let row = [], cell = '', q = false;
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (q) {
      if (ch === '"' && text[i + 1] === '"') { cell += '"'; i++; }
      else if (ch === '"') q = false;
      else cell += ch;
    } else if (ch === '"') q = true;
    else if (ch === ',') { row.push(cell); cell = ''; }
    else if (ch === '\n' || ch === '\r') {
      if (ch === '\r' && text[i + 1] === '\n') i++;
      row.push(cell); cell = '';
      if (row.some((c) => c !== '')) rows.push(row);
      row = [];
    } else cell += ch;
  }
  row.push(cell);
  if (row.some((c) => c !== '')) rows.push(row);
  return rows;
}

async function umatchetCsv(c, reconciliationId) {
  const url = `${BASE_URL}/bank/reconciliation/transactions/unmatched:csv?reconciliationId=${reconciliationId}`;
  // PUT, men endrer ingenting – ren eksport av umatchede transaksjoner.
  const res = await fetch(url, { method: 'PUT', headers: { Authorization: await authorization(c.id, c.account), Accept: 'text/csv' } });
  if (!res.ok) throw new Error(`unmatched:csv ${res.status}`);
  const rows = parseCsv(new TextDecoder('utf-8').decode(await res.arrayBuffer()));
  return rows.slice(1).map(([dato, belop, beskrivelse = '', detaljer = '']) => ({
    dato, belop: Number(belop), beskrivelse: beskrivelse.trim(), detaljer: detaljer.trim(),
  }));
}

// ── per klient ──────────────────────────────────────────────────────────────
/**
 * Status for alle bankkontoer hos klienten `c` (fra clients()) per måned fra–til (ÅÅÅÅ-MM).
 * `detaljer: false` hopper over bankposter, umatchede posteringer og forslag (bare lukket/åpen, saldo og bankens saldo).
 */
export async function hentKlient(c, { fra, til, detaljer = true }) {
  const maaneder = maanederMellom(fra, til);
  const q = (path, query) => list(path, { companyId: c.id, query });
  const res = { klient: c.name, orgnr: c.organizationNumber ?? '', kontoer: [], feil: [] };

  const accs = await q('/ledger/account', { isBankAccount: true, isInactive: false, fields: 'id,number,name,requireReconciliation' });
  if (!accs.length) return res;
  const periods = await q('/ledger/accountingPeriod', { startFrom: `${fra}-01`, startTo: nesteMnd(til), fields: 'id,start' });
  const recs = await q('/bank/reconciliation', {
    accountId: accs.map((a) => a.id).join(','), accountingPeriodId: periods.map((p) => p.id).join(','),
    fields: 'id,type,isClosed,bankAccountClosingBalanceCurrency,account(id),accountingPeriod(id)',
  });
  const nrs = accs.map((a) => a.number);
  const saldo = {}; // saldo[mnd][accountId] = {ib, bev, ub}
  for (const m of maaneder) {
    saldo[m] = {};
    const rows = await q('/balanceSheet', {
      dateFrom: `${m}-01`, dateTo: nesteMnd(m), accountNumberFrom: Math.min(...nrs), accountNumberTo: Math.max(...nrs),
      fields: 'account(id),balanceIn,balanceChange,balanceOut',
    });
    for (const r of rows) saldo[m][r.account.id] = { ib: r.balanceIn, bev: r.balanceChange, ub: r.balanceOut };
  }

  for (const a of accs) {
    const k = { nummer: a.number, navn: a.name, kontoId: a.id, bankfeed: false, maaneder: [] };
    let stmts = null;
    try { stmts = await q('/bank/statement', { accountId: a.id, fields: 'id,fromDate,toDate' }); } catch { stmts = null; }
    const kontoRecs = recs.filter((r) => r.account.id === a.id);
    k.bankfeed = kontoRecs.some((r) => r.type === 'AUTOMATIC') || (stmts?.length ?? 0) > 0;

    for (const m of maaneder) {
      const p = periods.find((x) => x.start.startsWith(m));
      const r = p && kontoRecs.find((x) => x.accountingPeriod.id === p.id);
      const s = saldo[m][a.id] ?? { ib: 0, bev: 0, ub: 0 };
      const bankSaldo = r && r.bankAccountClosingBalanceCurrency != null ? rund(r.bankAccountClosingBalanceCurrency) : null;
      const mnd = {
        maaned: m, avstemming: r?.type ?? null, avstemmingId: r?.id ?? null, lukket: !!r?.isClosed, bev: rund(s.bev), ub: rund(s.ub),
        bankSaldo, differanse: bankSaldo == null ? null : rund(s.ub - bankSaldo), bank: [], tx: null, forslag: null,
      };
      mnd.aapen = !mnd.lukket && (!!r || Math.abs(s.bev) >= 0.005 || Math.abs(s.ub) >= 0.005);
      if (detaljer && mnd.aapen && k.bankfeed) {
        try {
          // Umatchede transaksjoner fra kontoutskriftene i måneden (med id, som trengs for å matche).
          const kontoutskriftTx = async () => {
            const ut = [];
            const slutt = nesteMnd(m);
            for (const st of (stmts ?? []).filter((x) => x.fromDate < slutt && (x.toDate ?? x.fromDate) >= `${m}-01`)) {
              const tx = await q('/bank/statement/transaction', { bankStatementId: st.id, fields: 'id,postedDate,description,amountCurrency,matched' });
              for (const t of tx) {
                if (!t.matched && t.postedDate >= `${m}-01` && t.postedDate < slutt && !ut.some((b) => b.id === t.id)) {
                  ut.push({ id: t.id, dato: t.postedDate, belop: t.amountCurrency, beskrivelse: t.description ?? '', detaljer: '' });
                }
              }
            }
            return ut;
          };
          if (r) {
            mnd.bank = await umatchetCsv(c, r.id);
            // CSV-eksporten har ikke id: legg på id fra kontoutskriften der dato og beløp passer entydig.
            if (stmts?.length && mnd.bank.length) {
              const tx = await kontoutskriftTx();
              const brukt = new Set();
              for (const b of mnd.bank) {
                const t = tx.find((x) => !brukt.has(x.id) && x.dato === isoDato(b.dato) && Math.abs(x.belop - b.belop) < 0.005);
                if (t) { b.id = t.id; brukt.add(t.id); }
              }
            }
          } else if (stmts) {
            mnd.bank = await kontoutskriftTx();
          }
          const posts = await q('/ledger/posting', { accountId: a.id, dateFrom: `${m}-01`, dateTo: nesteMnd(m), fields: 'id,amount,matched' });
          const um = posts.filter((x) => x.matched === false);
          mnd.tx = { antall: um.length, sum: rund(um.reduce((t, x) => t + x.amount, 0)) };
          if (r) {
            // Matcheforslag som ikke er godkjent (Tripletex' automatiske forslag) – internt arbeid.
            try {
              const fs = await q('/bank/reconciliation/match', { bankReconciliationId: r.id, approved: false, fields: 'id,type,transactions(amountCurrency)' });
              mnd.forslag = { antall: fs.length, sum: rund(fs.reduce((t, f) => t + (f.transactions ?? []).reduce((u, x) => u + (x.amountCurrency ?? 0), 0), 0)) };
            } catch (e) {
              mnd.forslag = { antall: null, sum: null, feil: kortFeil(e).slice(0, 120) };
            }
          }
        } catch (e) {
          res.feil.push(`${a.number} ${m}: ${kortFeil(e).slice(0, 160)}`);
        }
      }
      k.maaneder.push(mnd);
    }
    res.kontoer.push(k);
  }
  return res;
}

// ── vurdering: hva må kunden levere, hva er internt ─────────────────────────
const poster = (n) => `${n} ${n === 1 ? 'post' : 'poster'}`;

export function vurder(r, til) {
  // intern-punkter: { konto, mnd: [ÅÅÅÅ-MM], tekst } – slås sammen per konto+tekst ved utskrift
  const kunde = [], intern = [], excelKontoer = [];
  const inn = (konto, mnd, tekst) => intern.push({ konto, mnd, tekst });
  let antallPoster = 0;
  for (const k of r.kontoer) {
    let aapne = k.maaneder.filter((m) => m.aapen);
    const sisteUb = k.maaneder.at(-1)?.ub ?? 0;
    if (String(k.nummer).startsWith('19') && sisteUb < -0.005) inn(k.nummer, [], `negativ banksaldo ${kr(sisteUb)} per ${mndNavn(til).toLowerCase()} – sjekk`);
    if (!aapne.length) continue;

    if (erSkattetrekk(k)) {
      inn(k.nummer, aapne.map((m) => m.maaned), 'skattetrekkskonto ikke lukket');
      continue;
    }
    if (k.bankfeed) {
      const alle = aapne.flatMap((m) => m.bank.map((b) => ({ ...b, maaned: m.maaned })));
      if (alle.length) {
        antallPoster += alle.length;
        kunde.push(`${k.nummer}: ${poster(alle.length)} uten bilag`);
        excelKontoer.push({
          nummer: String(k.nummer), navn: k.navn,
          maaneder: aapne.filter((m) => m.bank.length).map((m) => ({
            maaned: mndNavn(m.maaned),
            poster: m.bank.map((b) => ({
              raw: `${b.dato} ${b.belop.toFixed(2).replace('.', ',')} ${b.beskrivelse}${b.detaljer ? ` | Detaljer: ${b.detaljer}` : ''}`,
              kilde: 'Bankside',
            })),
          })),
        });
      }
      for (const m of aapne) {
        if (m.forslag?.antall) inn(k.nummer, [m.maaned], `${m.forslag.antall} matcheforslag ikke godkjent`);
        if (m.bank.length) continue;
        if (!m.avstemming) inn(k.nummer, [m.maaned], Math.abs(m.bev) >= 0.005 ? `avstemming ikke opprettet (bevegelse ${kr(m.bev)})` : 'avstemming ikke opprettet (ingen bevegelse)');
        else if (m.tx?.antall) inn(k.nummer, [m.maaned], `${m.tx.antall} bokførte posteringer umatchet (sum ${kr(m.tx.sum)})`);
        else inn(k.nummer, [m.maaned], 'ingen åpne poster – kan lukkes');
      }
    } else {
      // Uten bankfeed: en lukket (manuell) avstemming bekrefter saldoen bakover. Måneder før siste lukkede
      // uten avstemming regnes som dekket; påbegynte, ikke lukkede avstemminger der er internt arbeid.
      const sisteLukket = k.maaneder.findLastIndex((m) => m.lukket);
      const før = aapne.filter((m) => k.maaneder.indexOf(m) < sisteLukket);
      for (const m of før.filter((x) => x.avstemming)) inn(k.nummer, [m.maaned], 'manuell avstemming påbegynt, ikke lukket');
      aapne = aapne.filter((m) => k.maaneder.indexOf(m) > sisteLukket);
      if (!aapne.length) continue;
      const ms = aapne.map((m) => m.maaned);
      const bev = rund(aapne.reduce((t, m) => t + m.bev, 0));
      if (Math.abs(bev) >= 0.005 || aapne.some((m) => Math.abs(m.bev) >= 0.005) || aapne.some((m) => m.avstemming)) {
        kunde.push(`${k.nummer}: kontoutskrift ${mndListe(ms)}`);
        excelKontoer.push({
          nummer: String(k.nummer), navn: k.navn, maaneder: [],
          merknad: `Ingen bankfeed – send kontoutskrift for ${mndListe(ms)} ${til.slice(0, 4)}. ` +
            `Bevegelse i ${aapne.filter((m) => Math.abs(m.bev) >= 0.005).length} av ${aapne.length} måneder, netto ${kr(bev)} kr; saldo ${kr(aapne.at(-1).ub)} kr.`,
        });
      } else {
        inn(k.nummer, ms, `statisk saldo ${kr(aapne.at(-1).ub)}, ingen bevegelse – ikke avstemt`);
      }
    }
  }
  return { kunde, intern, excelKontoer, antallPoster };
}

export function slåSammen(punkter) {
  // Samme konto + tekst over flere måneder -> "1920 jan–feb, apr: …"
  const map = new Map();
  for (const p of punkter) {
    const nøkkel = `${p.konto}|${p.tekst}`;
    if (!map.has(nøkkel)) map.set(nøkkel, { ...p, mnd: [] });
    map.get(nøkkel).mnd.push(...p.mnd);
  }
  return [...map.values()].map((v) => `${v.konto}${v.mnd.length ? ` ${mndListe([...new Set(v.mnd)].sort())}` : ''}: ${v.tekst}`);
}

// ── kjør ────────────────────────────────────────────────────────────────────
async function main() {
  const a = argumenter(process.argv.slice(2));
  const iDag = new Date();
  const forrige = new Date(iDag.getFullYear(), iDag.getMonth() - 1, 1);
  const TIL = typeof a.til === 'string' ? a.til : `${forrige.getFullYear()}-${String(forrige.getMonth() + 1).padStart(2, '0')}`;
  const FRA = typeof a.fra === 'string' ? a.fra : `${TIL.slice(0, 4)}-01`;
  if (!erMaaned(TIL) || !erMaaned(FRA) || FRA > TIL) throw new Error('--fra/--til må være ÅÅÅÅ-MM og fra ≤ til. Ingenting er gjort.');
  if (a.kundemapper) throw new Error('--kundemapper er fjernet: leveranser går til Tally. Bruk --ut <mappe>. Ingenting er gjort.');

  const utvalg = await klientutvalg(a);
  const UT = utmappe(a.ut, 'bankavstemming', TIL);
  const periodeTekst = `${mndNavn(FRA)}–${mndNavn(TIL)} ${TIL.slice(0, 4)}`;
  const dato = iDag.toLocaleDateString('nb-NO', { day: '2-digit', month: '2-digit', year: 'numeric' });
  const alle = [];
  const oversikt = [];

  for (const c of utvalg) {
    let r, feil;
    for (let forsøk = 1; forsøk <= 3 && !r; forsøk++) {
      // Nettverksbrudd ("fetch failed") er som regel forbigående – prøv igjen (alt er lesende).
      try { r = await hentKlient(c, { fra: FRA, til: TIL }); } catch (e) {
        feil = e;
        if (forsøk < 3) await new Promise((ok) => setTimeout(ok, 3000 * forsøk));
      }
    }
    if (!r) {
      oversikt.push({ klient: c.name, kunde: '–', intern: `FEIL: ${kortFeil(feil).slice(0, 120)}` });
      console.error(`${c.name}: FEIL – ${kortFeil(feil).slice(0, 160)}`);
      continue;
    }
    const v = vurder(r, TIL);
    alle.push({ ...r, vurdering: { kunde: v.kunde, intern: slåSammen(v.intern) } });
    oversikt.push({
      klient: c.name,
      kunde: v.kunde.join('; ') || '–',
      intern: [...slåSammen(v.intern), ...r.feil.map((f) => `feil ${f}`)].join('; ') || '–',
    });

    if (v.excelKontoer.length) {
      const data = { selskap: c.name, orgnr: r.orgnr, aar: TIL.slice(0, 4), periode: periodeTekst, dato, kontoer: v.excelKontoer };
      const dataFil = join(UT, `${c.name.replace(/[<>:"/\\|?*]/g, '')}.data.json`);
      writeFileSync(dataFil, JSON.stringify(data, null, 2));
      if (a.excel) {
        const p = spawnSync('uv', ['run', '--quiet', '--with', 'openpyxl', '--with', 'pillow', '--with', 'pypdf', 'python', LAG_SPEC, dataFil, '--mappe', UT],
          // Systemets sertifikatlager (proxy/antivirus som bryter TLS); nye uv leser UV_SYSTEM_CERTS, eldre UV_NATIVE_TLS.
          { encoding: 'utf-8', env: { UV_SYSTEM_CERTS: 'true', UV_NATIVE_TLS: 'true', ...process.env, PYTHONIOENCODING: 'utf-8' } });
        if (p.status !== 0) console.error(`Excel feilet for ${c.name}: ${(p.stdout || p.stderr || p.error?.message || '').slice(0, 300)}`);
        else console.error(`Excel: ${(p.stdout.match(/Laget (.+)/)?.[1] ?? UT).trim()}`);
      }
    }
    console.error(`${c.name}: ${poster(v.antallPoster)} uten bilag, ${v.kunde.length} krav til kunden, ${slåSammen(v.intern).length} interne punkter`);
  }

  writeFileSync(join(UT, 'status.json'), JSON.stringify(alle, null, 2));
  const md = [
    `# Bankavstemming ${mndNavn(TIL).toLowerCase()} ${TIL.slice(0, 4)} – oversikt (${dato})`, '',
    `Kontoer som ikke er avstemt og lukket for alle måneder ${periodeTekst.toLowerCase()}. Kun lesing via Tripletex API.`, '',
    '| Klient | Fra kunden | Internt |', '|---|---|---|',
    ...oversikt.map((o) => `| ${o.klient} | ${o.kunde} | ${o.intern} |`), '',
  ].join('\n');
  writeFileSync(join(UT, `Bankavstemming ${mndNavn(TIL).toLowerCase()} ${TIL.slice(0, 4)} - oversikt.md`), md);
  console.log(md);
  console.error(`Filer i ${UT}`);
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  main().catch((e) => { console.error(`Feil: ${kortFeil(e)}`); process.exitCode = 1; });
}
