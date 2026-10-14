// Kommandolinje mot Tripletex (kjøres fra repo-rota).
//
//   npm run -s connect                       vis nøklene og test tilgangen til hver klient (whoAmI per klient)
//   npm run token                            vis hva slags nøkler som ligger i tripletex-api/.env (sendes ingen steder)
//   npm run -s api -- GET /ledger/account number=1920 fields=id,name --client "Klient AS"
//   npm run -s api -- GET /voucherInbox/inboxCount --client "Klient A" --client "Klient B"   (eller --alle)
//   npm run -s api -- GET /ledger/posting dateFrom=2026-01-01 dateTo=2026-02-01 fields=id,amount --client 912345678 --sider
//   npm run -s api -- GET /ledger/voucher/<id>/pdf --client "Klient AS" --ut <fil.pdf>
//   npm run -s api -- POST /sti body='{"..."}' --client "Klient AS"            (tørrkjøring – ingenting sendes)
//   npm run -s api -- POST /sti body='{"..."}' --client "Klient AS" --bekreft  (bare etter ja fra brukeren)
//
// Personopplysninger (fødselsnr., kontonr., e-post, telefon, navn/adresse på personer) og mønstre i fritekst maskeres i
// all utskrift. --umaskert virker bare når miljøvariabelen TRIPLETEX_UMASKERT=1 er satt av brukeren selv.

import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { inspectToken, authMode, accounts, tokenOf, BASE_URL, viaKonto } from './auth.js';
import { clients, whoAmI, list, request } from './tripletex.js';
import { maskert, redactText, isPersonalPath } from './privacy.js';
import { argumenter, klientutvalg, kortFeil } from './valg.js';

const [command = 'connect', ...rest] = process.argv.slice(2);

async function cmdConnect() {
  console.log(`Koblet til ${BASE_URL}\n`);
  const all = accounts();
  if (all.length === 0) throw new Error('Ingen nøkkel i tripletex-api/.env – kjør npm run set-token.');

  for (const { account, envVar } of all) {
    try {
      const me = await whoAmI(0, account);
      console.log(`Konto "${account}" (${envVar}, ${authMode(account)}): ${me.company?.name ?? '(ukjent firma)'}`);
    } catch (err) {
      console.log(`Konto "${account}" (${envVar}): ✗ ${kortFeil(err)}`);
      process.exitCode = 1;
    }
  }
  console.log('');

  const liste = await clients();
  if (liste.length === 0) {
    console.log('Nøkkelen har ikke tilgang til noen klienter.');
    process.exitCode = 1;
    return;
  }
  console.log(`Klienter nøkkelen har tilgang til (${liste.length}):`);
  for (const c of liste) {
    const label = `${c.name}  (org.nr. ${c.organizationNumber ?? '-'}, id ${c.id}${viaKonto(c.account)})`;
    try {
      await whoAmI(c.id, c.account);
      console.log(`  ✓ ${label}`);
    } catch (err) {
      console.log(`  ✗ ${label} – ${kortFeil(err)}`);
    }
  }
}

// Git Bash gjør «/sti» om til «C:/Program Files/Git/sti» før npm ser argumentet.
const rettSti = (p) => String(p ?? '').replace(/^[A-Z]:\/.*?\/Git(?=\/)/i, '');

async function cmdApi() {
  const a = argumenter(rest);
  if (a.umaskert && process.env.TRIPLETEX_UMASKERT !== '1') {
    throw new Error('--umaskert er avvist: krever at brukeren selv har satt miljøvariabelen TRIPLETEX_UMASKERT=1. Ingenting er gjort.');
  }
  const pos = [...a._];
  const metode = (pos.length && !pos[0].startsWith('/') && !/^[A-Z]:\//i.test(pos[0]) ? pos.shift() : 'GET').toUpperCase();
  const sti = rettSti(pos.shift());
  if (!sti.startsWith('/') || !['GET', 'POST', 'PUT', 'DELETE'].includes(metode)) {
    throw new Error('Bruk: npm run -s api -- [GET|POST|PUT|DELETE] /sti [nøkkel=verdi ...] [body=\'{...}\'] (--client "klient" | --alle) [--sider] [--ut <fil>] [--bekreft]');
  }
  const query = {};
  let body;
  for (const p of pos) {
    const eq = p.indexOf('=');
    if (p.startsWith('body=')) {
      try { body = JSON.parse(p.slice(5)); } catch (e) { throw new Error(`body er ikke gyldig JSON (${e.message}). Ingenting er gjort.`); }
    } else if (eq > 0) query[p.slice(0, eq)] = p.slice(eq + 1);
    else throw new Error(`Ukjent argument «${p}» (bruk nøkkel=verdi). Ingenting er gjort.`);
  }

  // Klienten(e) avgjøres før noe sendes; klientutvalg() stopper hvis --client mangler eller er tvetydig.
  const utvalg = await klientutvalg(a);
  const skriv = metode !== 'GET';
  if (skriv && utvalg.length !== 1) throw new Error('Skrivende kall går bare mot én klient om gangen. Ingenting er gjort.');
  if (skriv && !a.bekreft) {
    console.log(JSON.stringify({
      torrkjoring: true, klient: utvalg[0].name, metode, sti, parametre: query, body: maskert(body ?? null),
      resultat: 'Ingenting er sendt. Kjør på nytt med --bekreft når brukeren har sagt ja.',
    }, null, 2));
    return;
  }
  if (isPersonalPath(sti)) console.error('Merk: endepunktet inneholder personopplysninger – maskert i utskriften. Hent bare det oppgaven krever (fields=).');
  const vis = (x) => (a.umaskert ? x : maskert(x));
  if (a.umaskert) console.error('ADVARSEL: umaskert utskrift – kan inneholde personopplysninger. Ikke del eller lagre.');

  // Ett kall for én klient. Svar som ikke er JSON (PDF o.l.) returneres som Buffer.
  const ettKall = async (c) => {
    if (a.sider) {
      if (skriv) throw new Error('--sider gjelder bare GET.');
      const values = await list(sti, { companyId: c.id, query });
      return { json: { antall: values.length, values } };
    }
    const r = await request(sti, { companyId: c.id, method: metode, query, body, raw: true });
    if (!r.buffer.length) return { json: null };
    if (/json/i.test(r.contentType)) return { json: JSON.parse(r.buffer.toString('utf8')) };
    return { binaer: r.buffer, type: r.contentType };
  };

  if (utvalg.length === 1) {
    const c = utvalg[0];
    console.error(`[${c.name}${viaKonto(c.account)}] ${metode} ${sti}`);
    const svar = await ettKall(c);
    if (typeof a.ut === 'string') {
      const fil = resolve(a.ut);
      mkdirSync(dirname(fil), { recursive: true });
      const innhold = svar.binaer ?? JSON.stringify(vis(svar.json), null, 1);
      writeFileSync(fil, innhold);
      console.log(JSON.stringify({ fil, byte: Buffer.byteLength(innhold), type: svar.type ?? 'application/json' }));
      return;
    }
    if (svar.binaer) throw new Error(`Svaret er binært (${svar.type || 'ukjent type'}, ${svar.binaer.length} byte) – bruk --ut <fil>. Ingenting er skrevet ut.`);
    console.log(JSON.stringify(vis(svar.json), null, 2));
    return;
  }

  // Flere klienter: én om gangen, JSON-liste [{klient, ok, data|feil}].
  console.error(`[${utvalg.length} klienter] ${metode} ${sti}`);
  const res = [];
  for (const c of utvalg) {
    try {
      const svar = await ettKall(c);
      if (svar.binaer) throw new Error(`binært svar (${svar.type}) – hent én klient om gangen med --ut`);
      res.push({ klient: c.name, ok: true, data: vis(svar.json) });
    } catch (e) {
      res.push({ klient: c.name, ok: false, feil: redactText(kortFeil(e)) });
    }
  }
  if (typeof a.ut === 'string') {
    const fil = resolve(a.ut);
    mkdirSync(dirname(fil), { recursive: true });
    const innhold = JSON.stringify(res, null, 1);
    writeFileSync(fil, innhold);
    console.log(JSON.stringify({ fil, byte: Buffer.byteLength(innhold), klienter: res.length, ok: res.filter((r) => r.ok).length, feil: res.filter((r) => !r.ok).length }));
    return;
  }
  console.log(JSON.stringify(res, null, 2));
}

// `token` kjøres uten --env-file, så den virker også før nøkkelen er lagt inn: tripletex-api/.env leses her hvis den finnes.
function lesEnvFil() {
  const fil = new URL('../.env', import.meta.url);
  if (!existsSync(fil)) return false;
  for (const linje of readFileSync(fil, 'utf8').replace(/^\uFEFF/, '').split(/\r?\n/)) {
    const m = linje.match(/^\s*([A-Z0-9_]+)\s*=\s*(.*?)\s*$/);
    if (m && process.env[m[1]] === undefined) process.env[m[1]] = m[2].replace(/^["']|["']$/g, '');
  }
  return true;
}

function cmdToken() {
  const funnet = lesEnvFil();
  const all = accounts();
  if (all.length === 0) {
    console.log(funnet ? 'Ingen nøkkel i tripletex-api/.env – kjør npm run set-token.' : 'tripletex-api/.env finnes ikke – kjør npm run set-token.');
    return;
  }
  for (const { account, envVar } of all) {
    console.log(`\n${envVar}${all.length > 1 ? ` (konto "${account}")` : ''}:`);
    describeToken(tokenOf(account));
  }
  const satt = (k) => (process.env[k]?.trim() ? 'satt' : 'ikke satt');
  console.log(`\nTRIPLETEX_CONSUMER_TOKEN: ${satt('TRIPLETEX_CONSUMER_TOKEN')}. API: ${BASE_URL}`);
}

function describeToken(token) {
  const info = inspectToken(token);
  const describe = {
    none: 'Ingen nøkkel.',
    'jwt-refresh': 'Tripletex JWT refresh token (tlxr_) – byttes automatisk mot sessionToken (8 t).',
    jwt: 'Ekte JWT (header.payload.signatur).',
    tripletex: 'Tripletex-token (base64-JSON med tokenId) – session- eller employeeToken.',
    unknown: 'Ukjent format.',
  }[info.kind];
  console.log(describe);
  if (info.kind === 'jwt' || info.kind === 'jwt-refresh') {
    const { exp, iat, ...claims } = info.payload;
    console.log('Claims (bare navnene):', Object.keys(claims).join(', ') || '-');
    if (info.expires) console.log(`Utløper: ${info.expires.toLocaleString('nb-NO')}${info.expires < new Date() ? '  (UTLØPT)' : ''}`);
  }
}

const commands = { connect: cmdConnect, api: cmdApi, token: cmdToken };
if (!commands[command]) {
  console.error(`Ukjent kommando "${command}". Tilgjengelig: ${Object.keys(commands).join(', ')}`);
  process.exit(1);
}

try {
  await commands[command]();
} catch (err) {
  console.error(`Feil: ${redactText(String(err.message).slice(0, 1500))}`);
  process.exitCode = 1;
}
