// Søk i Tripletex API v2-indeksen: finn riktig kall for en oppgave.
//
//   node tripletex-api/finn.js a-melding status          oppgaver, områder og kall som matcher
//   node tripletex-api/finn.js --sti /ledger/voucher     alle parametere og body-felt for en sti (fra openapi.json)
//   node tripletex-api/finn.js --sti /invoice/{id}/:send PUT
//
// Leser bare lokale filer (docs/api-v2-indeks.json, docs/openapi.json) – ingen kall mot Tripletex.

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const DOCS = path.resolve(path.dirname(fileURLToPath(import.meta.url)), 'docs');
const args = process.argv.slice(2);

// «a-melding» -> «amelding», «Lønn» -> «lonn»: samme form i søk og nøkkelord. Enkeltbokstaver ignoreres.
const norm = (s) => String(s ?? '').toLowerCase().replace(/æ/g, 'ae').replace(/ø/g, 'o').replace(/å/g, 'a')
  .replace(/([a-z0-9])-(?=[a-z0-9])/g, '$1').replace(/[^a-z0-9/{}:>]+/g, ' ').trim();
const words = (s) => norm(s).split(/[\s/{}:>]+/).filter((w) => w.length > 1);

function showPath(p, method) {
  p = String(p ?? '').replace(/^[A-Z]:\/.*?\/Git(?=\/)/i, ''); // Git Bash gjør «/sti» om til «C:/…/Git/sti»
  const spec = JSON.parse(fs.readFileSync(path.join(DOCS, 'openapi.json'), 'utf8'));
  const item = spec.paths[p];
  if (!item) {
    const near = Object.keys(spec.paths).filter((k) => k.includes(p.split('/')[1] || '@@')).slice(0, 15);
    console.log(`Stien finnes ikke: ${p}${near.length ? `\nMente du:\n  ${near.join('\n  ')}` : ''}`);
    process.exitCode = 1;
    return;
  }
  for (const [m, d] of Object.entries(item)) {
    if (method && m !== method.toLowerCase()) continue;
    console.log(`\n${m.toUpperCase()} ${p} — ${d.summary ?? ''}`);
    if (d.description) console.log(d.description.replace(/\s+/g, ' ').slice(0, 1000));
    for (const x of d.parameters || []) {
      const en = x.schema?.enum ? ` [${x.schema.enum.join('|')}]` : '';
      console.log(`  ${x.in}:${x.name}${x.required ? '*' : ''} (${x.schema?.type ?? ''}${en}) ${(x.description || '').replace(/\s+/g, ' ').slice(0, 160)}`);
    }
    const b = d.requestBody?.content && Object.values(d.requestBody.content)[0]?.schema;
    if (b) {
      const ref = (b.$ref || b.items?.$ref || '').split('/').pop();
      console.log(`  body: ${ref ? (b.items ? `[${ref}]` : ref) : JSON.stringify(b).slice(0, 200)}`);
      const props = spec.components?.schemas?.[ref]?.properties;
      if (props) console.log(`   skrivbare felt: ${Object.entries(props).filter(([, v]) => !v.readOnly).map(([k]) => k).join(', ')}`);
    }
  }
}

function search(q) {
  const idx = JSON.parse(fs.readFileSync(path.join(DOCS, 'api-v2-indeks.json'), 'utf8'));
  const qw = words(q);
  if (!qw.length) return console.log('Bruk: node tripletex-api/finn.js <ord> [ord ...]');
  // Treff på hele ord teller mest, prefiks (≥4 tegn) litt mindre, delstreng minst.
  const hit = (w, list) => {
    let best = 0;
    for (const t of list) {
      for (const tw of words(t)) {
        if (tw === w) return 1;
        if (w.length >= 4 && (tw.startsWith(w) || w.startsWith(tw) && tw.length >= 4)) best = Math.max(best, 0.7);
        else if (w.length >= 5 && tw.includes(w)) best = Math.max(best, 0.4);
      }
    }
    return best;
  };
  const score = (fields) => qw.reduce((sum, w) => sum + Math.max(...fields.map(([list, wt]) => hit(w, list) * wt)), 0);

  const tasks = idx.oppgaver.map((o) => ({ o, s: score([[o.nokkelord, 3], [[o.oppgave], 2.5], [o.kall, 1.5], [[o.fremgangsmate], 0.5]]) })).filter((x) => x.s > 0).sort((a, b) => b.s - a.s).slice(0, 6);
  const tags = idx.tags.map((t) => ({ t, s: score([[t.nokkelord, 3], [[t.tag], 2], [[t.beskrivelse], 1]]) })).filter((x) => x.s > 0).sort((a, b) => b.s - a.s).slice(0, 3);
  const ops = idx.ops.map((o) => ({ o, s: score([[[o.path], 2], [[o.summary], 1.5]]) })).filter((x) => x.s > 0).sort((a, b) => b.s - a.s).slice(0, 10);
  const conn = idx.connector.map((c) => ({ c, s: score([[c.nokkelord || [], 3], [[c.tool.replace(/_/g, ' ')], 2.5], [[c.beskrivelse], 1]]) })).filter((x) => x.s >= qw.length * 1.5).sort((a, b) => b.s - a.s).slice(0, 4);
  const none = idx.ikkeIApi.map((x) => ({ x, s: score([[x.nokkelord || [], 3], [[x.oppgave], 2.5], [[x.merknad], 1]]) })).filter((x) => x.s >= qw.length * 1.5).sort((a, b) => b.s - a.s).slice(0, 3);

  console.log(`Søk: «${q}»  (spec ${idx.versjon})`);
  // Finnes bare i connectoren eller ikke i API-et? Si det først, så det ikke drukner i nesten-treff.
  const top = tasks[0]?.s ?? 0;
  const notInApi = none.filter(({ s }) => s >= top * 0.9);
  if (notInApi.length) {
    console.log('\n== IKKE I API v2 – bruk connectoren / annen løsning ==');
    for (const { x } of notInApi) console.log(`  ${x.oppgave}\n    ${x.merknad}`);
    for (const { c } of conn.filter(({ c }) => c.kunConnector)) console.log(`  Connector: ${c.tool} — ${c.beskrivelse}`);
  }
  if (tasks.length) {
    console.log('\n== Oppgaver ==');
    for (const { o } of tasks) console.log(`\n${o.skrivende ? '✏️  ' : ''}${o.oppgave}  [${o.group}]\n  Kall: ${o.kall.join(' · ')}\n  ${o.fremgangsmate}`);
  }
  if (tags.length) {
    console.log('\n== Områder ==');
    for (const { t } of tags) {
      const list = idx.ops.filter((o) => o.tag === t.tag);
      console.log(`\n${t.tag} – ${t.beskrivelse}`);
      for (const o of list.slice(0, 12)) console.log(`  ${o.method.padEnd(6)} ${o.path}  — ${o.summary}`);
      if (list.length > 12) console.log(`  … ${list.length - 12} til (se docs/api-v2-oversikt.md)`);
    }
  }
  const group = tasks[0]?.o.group ?? tags[0]?.t.group;
  const fg = idx.fallgruver.filter((f) => f.group === group);
  if (fg.length) {
    console.log(`\n== Fallgruver (${group}) ==`);
    for (const f of fg) console.log(`  - ${f.tekst}`);
  }
  if (ops.length) {
    console.log('\n== Kall (sti/beskrivelse) ==');
    for (const { o } of ops) console.log(`  ${o.method.padEnd(6)} ${o.path}  — ${o.summary}${o.flags.length ? `  [${o.flags.join(' ')}]` : ''}`);
  }
  if (conn.length) {
    console.log('\n== Tripletex-connectoren ==');
    for (const { c } of conn) console.log(`  ${c.tool}${c.kunConnector ? '  (KUN CONNECTOR – ikke i API v2)' : ''} — ${c.beskrivelse}${c.kall.length ? `\n    API: ${c.kall.join(' · ')}` : ''}`);
  }
  if (none.length) {
    console.log('\n== Ikke i API v2 ==');
    for (const { x } of none) console.log(`  ${x.oppgave} – ${x.merknad}`);
  }
  if (!tasks.length && !tags.length && !ops.length && !conn.length) {
    console.log('\nIngen treff. Prøv synonymer (norsk/engelsk), eller se docs/api-v2-oversikt.md.');
    process.exitCode = 1;
  }
}

const i = args.indexOf('--sti');
if (i >= 0) showPath(args[i + 1], args[i + 2]);
else search(args.join(' '));
