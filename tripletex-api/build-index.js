// Bygger søkeindeksen og oversiktene over Tripletex API v2 fra docs/openapi.json + docs/indeks/*.json.
//
//   node tripletex-api/build-index.js                 -> docs/api-v2-indeks.json, docs/api-v2-oversikt.md, docs/api-v2-oppgaver.md
//   node tripletex-api/build-index.js -- --hent-spec  -> henter openapi.json på nytt først og viser nye/fjernede kall
//
// docs/indeks/<gruppe>.json inneholder nøkkelord, oppgaver og fallgruver per fagområde (håndskrevet/kuratert).
// Kall i en ny spec som ikke står i noen oppgave, havner likevel i oversikten via taggens gruppe.

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.dirname(fileURLToPath(import.meta.url));
const DOCS = path.join(ROOT, 'docs');
const SPEC = path.join(DOCS, 'openapi.json');
const SPEC_URL = 'https://tripletex.no/v2/openapi.json';

export const GROUPS = [
  ['mva', 'MVA / merverdiavgift', /^(ledger\/vat|vatReturns|vatTermSize)/],
  ['bank', 'Bank, avstemming og utbetalinger', /^(bank|ledger\/paymentTypeOut)/],
  ['lonn', 'Lønn, lønnsavstemminger, pensjon', /^(salary|pension|financeTax|company\/settings\/altinn)/],
  ['ansatte', 'Ansatte, arbeidsforhold, avdelinger, kontakter', /^(employee|department|division|contact)/],
  ['hovedbok', 'Hovedbok, bilag, posteringer, kontoplan, perioder, budsjett, avstemming', /^(ledger|voucher|balanceSheet|balance\/|accountingOffice|resultbudget|currency)/],
  ['salg', 'Kunder, ordre, faktura, purring, abonnement/CRM', /^(invoice|order|reminder|customer|crm|deliveryAddress|discountPolicy|supplierCustomer)/],
  ['innkjop', 'Leverandører, leverandørfaktura, innkjøp, dokumentarkiv', /^(supplier|purchaseOrder|document)/],
  ['prosjekt', 'Prosjekt, aktiviteter, oppgaver', /^(project|activity|task)/],
  ['timer', 'Timeføring og timelister', /^timesheet/],
  ['reise', 'Reiseregninger og utlegg', /^travelExpense/],
  ['produkt', 'Produkter, lager, logistikk', /^(product|inventory|pickupPoint|transportType)/],
  ['arsoppgjor', 'Anleggsmidler, årsoppgjør, SAF-T, signering (Penneo)', /^(asset|yearEnd|saft|penneo)/],
  ['system', 'Selskap, innstillinger, autentisering, webhooks, lisenser, oppslag', /.*/],
];
const PERSONAL = [/^\/employee/, /^\/salary/, /^\/contact/, /^\/timesheet/, /^\/travelExpense/];
const STD = new Set(['from', 'count', 'sorting', 'fields']);

export function extractOps(spec) {
  const ops = [];
  for (const [p, item] of Object.entries(spec.paths)) {
    for (const [m, d] of Object.entries(item)) {
      if (!['get', 'post', 'put', 'delete', 'patch'].includes(m)) continue;
      const tag = (d.tags || ['?'])[0];
      const summary = (d.summary || '').replace(/\s+/g, ' ').trim();
      const flags = ['BETA', 'INTERNAL', 'DEPRECATED'].filter((f) => summary.toUpperCase().includes(`[${f}]`) || (f === 'DEPRECATED' && d.deprecated));
      if (PERSONAL.some((re) => re.test(p))) flags.push('PERSONDATA');
      const params = (d.parameters || []).filter((x) => x.in !== 'header' && !STD.has(x.name));
      ops.push({
        method: m.toUpperCase(), path: p, tag, group: GROUPS.find(([, , re]) => re.test(tag))[0], summary, flags,
        params: params.map((x) => x.name + (x.required ? '*' : '')),
      });
    }
  }
  return ops;
}

const key = (o) => `${o.method} ${o.path}`;
const readJson = (f) => JSON.parse(fs.readFileSync(f, 'utf8'));
const esc = (s) => String(s ?? '').replace(/\|/g, '\\|');

async function fetchSpec() {
  const old = fs.existsSync(SPEC) ? extractOps(readJson(SPEC)) : [];
  const res = await fetch(SPEC_URL);
  if (!res.ok) throw new Error(`Klarte ikke hente ${SPEC_URL}: ${res.status}`);
  const text = await res.text();
  const fresh = extractOps(JSON.parse(text));
  const a = new Set(old.map(key)), b = new Set(fresh.map(key));
  const added = [...b].filter((k) => !a.has(k)), removed = [...a].filter((k) => !b.has(k));
  fs.writeFileSync(SPEC, text);
  console.log(`Spec oppdatert: ${fresh.length} kall (${added.length} nye, ${removed.length} fjernet).`);
  for (const k of added) console.log(`  + ${k}`);
  for (const k of removed) console.log(`  - ${k}`);
}

function build() {
  const spec = readJson(SPEC);
  const ops = extractOps(spec);
  const valid = new Set(ops.map(key));
  const dir = path.join(DOCS, 'indeks');
  const src = Object.fromEntries(fs.readdirSync(dir).filter((f) => f.endsWith('.json')).map((f) => [f.replace(/\.json$/, ''), readJson(path.join(dir, f))]));

  const tags = [], oppgaver = [], fallgruver = [], stale = [];
  for (const [g, name] of GROUPS) {
    const d = src[g] || { tags: [], oppgaver: [], fallgruver: [] };
    for (const t of d.tags) tags.push({ ...t, group: g });
    for (const o of d.oppgaver) oppgaver.push({ ...o, group: g });
    for (const f of d.fallgruver) fallgruver.push({ group: g, tekst: f });
  }
  for (const o of src._kritiker?.oppgaver || []) oppgaver.push({ ...o, group: GROUPS.find(([, , re]) => re.test(o.kall[0]?.split(' /')[1] || ''))?.[0] || 'system' });
  for (const o of oppgaver) {
    const bad = o.kall.filter((k) => !valid.has(k));
    if (bad.length) stale.push(`${o.oppgave}: ${bad.join(', ')}`);
    o.kall = o.kall.filter((k) => valid.has(k));
  }
  const connector = src._connector?.verktoy || [];
  const ikkeIApi = src._kritiker?.ikkeIApi || [];
  const tagInfo = Object.fromEntries(tags.map((t) => [t.tag, t]));

  const index = { versjon: spec.info.version, bygget: new Date().toISOString().slice(0, 10), grupper: GROUPS.map(([k, n]) => ({ key: k, navn: n })), ops, tags, oppgaver, fallgruver, connector, ikkeIApi };
  fs.writeFileSync(path.join(DOCS, 'api-v2-indeks.json'), JSON.stringify(index, null, 1));

  // Oversikt over alle kall, gruppert etter fagområde og tag.
  let md = `# Tripletex API v2 – alle kall\n\nSpec ${spec.info.version}, ${ops.length} kall, bygget ${index.bygget} fra ${SPEC_URL}.\n` +
    `Søk: \`node tripletex-api/finn.js <ord>\`. Parametere: \`node tripletex-api/finn.js --sti /sti\`. * = påkrevd parameter. ` +
    `Flagg: BETA, INTERNAL, DEPRECATED, PERSONDATA (bruk minimal fields=, GDPR).\n\n## Innhold\n\n`;
  for (const [g, name] of GROUPS) md += `- [${name}](#${g}) (${ops.filter((o) => o.group === g).length})\n`;
  for (const [g, name] of GROUPS) {
    md += `\n<a id="${g}"></a>\n## ${name}\n`;
    for (const t of [...new Set(ops.filter((o) => o.group === g).map((o) => o.tag))]) {
      const info = tagInfo[t];
      md += `\n### ${t}\n${info ? `${info.beskrivelse}\n\n*Nøkkelord:* ${info.nokkelord.join(', ')}\n` : ''}\n| Kall | Hva | Parametere | Flagg |\n|---|---|---|---|\n`;
      for (const o of ops.filter((x) => x.tag === t)) md += `| \`${o.method} ${esc(o.path)}\` | ${esc(o.summary.replace(/\[(BETA|INTERNAL|DEPRECATED)\]\s*/gi, ''))} | ${esc(o.params.join(', '))} | ${o.flags.join(' ')} |\n`;
    }
  }
  fs.writeFileSync(path.join(DOCS, 'api-v2-oversikt.md'), md);

  // Oppgaveoppskrifter.
  let oq = `# Tripletex API v2 – oppgaver og oppskrifter\n\nSpec ${spec.info.version}, bygget ${index.bygget}. ${oppgaver.length} oppgaver. ✏️ = skrivende (krever bekreftelse).\n\n`;
  for (const [g, name] of GROUPS) {
    const list = oppgaver.filter((o) => o.group === g);
    const fg = fallgruver.filter((f) => f.group === g);
    if (!list.length && !fg.length) continue;
    oq += `## ${name}\n\n`;
    for (const o of list) oq += `### ${o.skrivende ? '✏️ ' : ''}${o.oppgave}\n- **Kall:** ${o.kall.map((k) => `\`${k}\``).join(', ')}\n- **Nøkkelord:** ${o.nokkelord.join(', ')}\n- ${o.fremgangsmate}\n\n`;
    if (fg.length) oq += `**Fallgruver:**\n${fg.map((f) => `- ${f.tekst}`).join('\n')}\n\n`;
  }
  if (connector.length) {
    oq += `## Tripletex-connectoren (MCP) mot API v2\n\nVerktøy merket «kun connector» har ikke noe offentlig v2-endepunkt – bruk connectoren til dem.\n\n| Verktøy | Hva | API v2-kall |\n|---|---|---|\n`;
    for (const c of [...connector].sort((a, b) => b.kunConnector - a.kunConnector)) oq += `| \`${c.tool}\` | ${esc(c.beskrivelse)} | ${c.kunConnector ? '**kun connector**' : c.kall.map((k) => `\`${esc(k)}\``).join(', ')} |\n`;
    oq += '\n';
  }
  if (ikkeIApi.length) {
    oq += `## Ikke i API v2\n\n`;
    for (const x of ikkeIApi) oq += `- **${x.oppgave}** – ${x.merknad}\n`;
  }
  fs.writeFileSync(path.join(DOCS, 'api-v2-oppgaver.md'), oq);

  const uncovered = ops.filter((o) => !oppgaver.some((t) => t.kall.includes(key(o))));
  console.log(`Indeks bygget: ${ops.length} kall, ${tags.length} tags, ${oppgaver.length} oppgaver, ${connector.length} connector-verktøy.`);
  console.log(`Kall uten egen oppgave (finnes via tag/sti): ${uncovered.length}. Tags uten nøkkelord: ${[...new Set(ops.map((o) => o.tag))].filter((t) => !tagInfo[t]).length}.`);
  if (stale.length) console.log(`Fjernet kall som ikke lenger finnes i spec:\n  ${stale.join('\n  ')}`);
}

if (process.argv.includes('--hent-spec')) await fetchSpec();
build();
