// Tripletex API v2-klient for regnskapsbyrå-tilgang (byrå -> klienter).
//
// Hvilke klienter som er tilgjengelige bestemmes av hvem som har delegert tilgang til nøkkelen,
// og hentes dynamisk fra Tripletex (/company/>withLoginAccess) for hver nøkkel i tripletex-api/.env.
// Har du flere nøkler (flere byråer), slås listene sammen, og hvert kall går automatisk via nøkkelen
// som har tilgang til klienten.
//
// Kall skal gå sekvensielt: tokenfornyingen tåler ikke parallelle kall.

import { BASE_URL, DEFAULT_ACCOUNT, accounts, authorization, resetAuth } from './auth.js';

let cache = null; // [{ id, name, organizationNumber, account }]

/**
 * Selve HTTP-kallet. Standard er JSON-svar. Med `raw: true` returneres { status, contentType, buffer }
 * uten tolkning, slik at PDF og annet binært innhold kan lagres som det er.
 */
export async function rawRequest(path, { companyId = 0, account = DEFAULT_ACCOUNT, method = 'GET', query, body, form, raw = false, accept } = {}) {
  const url = new URL(`${BASE_URL}${path}`);
  if (query) {
    for (const [k, v] of Object.entries(query)) if (v !== undefined) url.searchParams.set(k, v);
  }

  const send = async () =>
    fetch(url, {
      method,
      headers: {
        Authorization: await authorization(companyId, account),
        Accept: accept ?? (raw ? '*/*' : 'application/json'),
        ...(body !== undefined && !form ? { 'Content-Type': 'application/json' } : {}),
      },
      // form (FormData) gir multipart; fetch setter Content-Type med boundary selv.
      body: form ?? (body !== undefined ? JSON.stringify(body) : undefined),
    });

  let res = await send();
  if (res.status === 401) {
    // Sesjonen kan være utløpt eller ugyldiggjort – prøv én gang med ny.
    resetAuth(account);
    res = await send();
  }
  // Struping (429) og forbigående serverfeil: prøv lesende kall på nytt med økende pause.
  // Skrivende kall prøves aldri på nytt – de kan ha blitt utført selv om svaret feilet.
  for (let forsok = 1; method === 'GET' && (res.status === 429 || res.status >= 500) && forsok <= 3; forsok++) {
    const vent = Number(res.headers.get('retry-after')) * 1000 || 1000 * 2 ** (forsok - 1);
    await new Promise((r) => setTimeout(r, Math.min(vent, 10_000)));
    res = await send();
  }
  if (!res.ok) {
    throw new Error(`${method} ${path} feilet (${res.status}): ${await res.text()}`);
  }
  if (raw) {
    return { status: res.status, contentType: res.headers.get('content-type') ?? '', buffer: Buffer.from(await res.arrayBuffer()) };
  }
  if (res.status === 204) return null;
  const tekst = await res.text();
  return tekst ? JSON.parse(tekst) : null;
}

/**
 * Klientene nøkkelen har delegert tilgang til akkurat nå. Hentes fra Tripletex hver gang
 * prosessen starter, så listen følger det som til enhver tid er delegert – ingen fast liste i koden.
 * Hver klient får `account` = kontoen (nøkkelen) kallene skal gå via. Har flere nøkler tilgang til
 * samme klient, brukes den første (standardnøkkelen først). Feiler én nøkkel, brukes de andre (med varsel).
 */
export async function clients() {
  if (cache) return cache;
  const byId = new Map();
  const failures = [];
  for (const { account, envVar } of accounts()) {
    try {
      const { values } = await rawRequest('/company/>withLoginAccess', {
        account,
        query: { fields: 'id,name,organizationNumber', count: 1000 },
      });
      for (const c of values) if (!byId.has(c.id)) byId.set(c.id, { ...c, account });
    } catch (err) {
      failures.push(`${envVar}: ${err.message.split('\n')[0]}`);
    }
  }
  if (accounts().length === 0) throw new Error('Ingen nøkkel i tripletex-api/.env – kjør npm run set-token.');
  if (failures.length && byId.size === 0) throw new Error(failures.join('\n'));
  for (const f of failures) console.error(`Advarsel – nøkkel hoppet over: ${f}`);
  cache = [...byId.values()].sort((a, b) => a.name.localeCompare(b.name, 'nb'));
  return cache;
}

/**
 * Finn én klient på navn, org.nr. eller id. Klienten MÅ alltid angis eksplisitt – vi velger
 * aldri en klient på egen hånd, heller ikke når nøkkelen bare har tilgang til én.
 * Feilmeldingene viser ikke hele klientlisten (bruk `npm run -s klienter`).
 */
export async function client(nameOrOrgNr) {
  const list = await clients();
  if (!nameOrOrgNr || !String(nameOrOrgNr).trim()) {
    throw new Error(`Ingen klient angitt – ingenting er gjort. Angi hvilken klient det gjelder (${list.length} tilgjengelige, se npm run -s klienter).`);
  }
  const q = String(nameOrOrgNr).toLowerCase().replace(/\s/g, '');
  const exact = list.find((c) => String(c.id) === q || c.organizationNumber?.replace(/\s/g, '') === q);
  if (exact) return exact;

  const hits = list.filter((c) => c.name.toLowerCase().replace(/\s/g, '').includes(q));
  if (hits.length === 0) throw new Error(`Fant ingen klient "${nameOrOrgNr}" – ingenting er gjort (se npm run -s klienter -- --sok <tekst>).`);
  if (hits.length > 1) {
    throw new Error(
      `"${nameOrOrgNr}" passer på flere klienter – ingenting er gjort. Vær mer presis eller bruk org.nr.: ` +
        hits.map((c) => `${c.name} (${c.organizationNumber ?? c.id})`).join(', '),
    );
  }
  return hits[0];
}

// Kall som er lov uten at en klient er valgt: bare "hvem er jeg" (klientlisten går via rawRequest).
const WITHOUT_CLIENT = ['/token/session/>whoAmI'];

/**
 * Kall mot Tripletex i en klients regnskap. `companyId` er påkrevd og må være en klient en av
 * nøklene har tilgang til; uten det gjøres ingenting (hindrer også kall i byråets egen konto).
 * Kallet går via nøkkelen (kontoen) som har tilgang til klienten.
 */
export async function request(path, options = {}) {
  const { companyId } = options;
  if (!companyId) {
    if (!WITHOUT_CLIENT.includes(path)) {
      throw new Error(`${path}: ingen klient angitt – ingenting er gjort. Bruk connect("klient").`);
    }
    return rawRequest(path, { ...options, companyId: 0 });
  }
  const c = (await clients()).find((x) => x.id === companyId);
  if (!c) {
    throw new Error(`Klient-id ${companyId} er ikke blant klientene nøkkelen har tilgang til – ingenting er gjort.`);
  }
  return rawRequest(path, { ...options, account: c.account });
}

/**
 * Henter alle sider av et liste-endepunkt (from/count) og returnerer samlet `values`.
 * Blar til en side gir færre enn `pageSize`: `fullResultSize` er ikke et pålitelig totalantall
 * (kalibrering 24.09.2026 – på /ledger/posting og /accountingOffice/reconciliations er den bare en nedre grense).
 */
export async function list(path, { companyId, query = {}, pageSize = 1000 } = {}) {
  const out = [];
  for (let from = 0; ; from += pageSize) {
    const page = await request(path, { companyId, query: { ...query, from, count: pageSize } });
    out.push(...(page?.values ?? []));
    if ((page?.values ?? []).length < pageSize) return out;
  }
}

/** Hvem er innlogget (for `account` sin nøkkel), eventuelt sett fra en klients kontekst. */
export async function whoAmI(companyId = 0, account = DEFAULT_ACCOUNT) {
  const { value } = await request('/token/session/>whoAmI', {
    companyId,
    account,
    query: { fields: 'employee(firstName,lastName),company(id,name,organizationNumber)' },
  });
  return value;
}

/**
 * Bundet klient-kontekst: `const b = await connect('klient E'); await b.list('/customer')`.
 * Samme metoder som over, men companyId er låst til klienten. `raw` gir binært svar (PDF o.l.).
 */
export async function connect(nameOrOrgNr) {
  const c = typeof nameOrOrgNr === 'object' && nameOrOrgNr?.id ? nameOrOrgNr : await client(nameOrOrgNr);
  return bind(c);
}

/** Samme som connect(), men for et klientobjekt fra clients(). */
export function bind(c) {
  return {
    company: c,
    request: (path, opts = {}) => request(path, { ...opts, companyId: c.id }),
    list: (path, opts = {}) => list(path, { ...opts, companyId: c.id }),
    raw: (path, opts = {}) => request(path, { ...opts, companyId: c.id, raw: true }),
    whoAmI: () => whoAmI(c.id),
  };
}
