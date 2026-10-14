// Autentisering mot Tripletex API v2.
//
// Tripletex bruker Basic auth: brukernavn = companyId (0 = egen bedrift, dvs. byrået,
// ellers klientens id), passord = sessionToken. Tokenet du har fått kan være én av flere typer,
// så vi finner ut hvilken ved å prøve i denne rekkefølgen og husker det som virket:
//
//   1. session  – tokenet ER et sessionToken (base64-JSON som starter med "eyJ", ofte kalt "JWT")
//   2. employee – tokenet er et employeeToken; byttes mot sessionToken sammen med consumerToken
//   3. bearer   – ekte JWT (header.payload.signatur) sendt som "Authorization: Bearer"
//
// Hver bruker har sin egen nøkkel i tripletex-api/.env (git-ignorert):
//   TRIPLETEX_TOKEN          -> kontoen "standard" (din egen nøkkel – det vanlige)
//   TRIPLETEX_TOKEN_<NAVN>   -> kontoen "<navn>", bare hvis du har tilgang via flere byråer (én nøkkel per byrå)
//   TRIPLETEX_EMPLOYEE_TOKEN + TRIPLETEX_CONSUMER_TOKEN -> alternativ til TRIPLETEX_TOKEN for standardkontoen

export const BASE_URL = (process.env.TRIPLETEX_BASE_URL || 'https://tripletex.no/v2').replace(/\/$/, '');

export const DEFAULT_ACCOUNT = 'standard';

const states = new Map(); // konto -> { mode, token, expires?, expiresAt? }

/** Kontoene som har et token i .env: [{ account, envVar }], standardnøkkelen (TRIPLETEX_TOKEN) først. */
export function accounts() {
  const liste = Object.keys(process.env)
    .filter((k) => /^TRIPLETEX_TOKEN(_[A-Z0-9_]+)?$/.test(k) && process.env[k]?.trim())
    .map((envVar) => ({
      account: envVar === 'TRIPLETEX_TOKEN' ? DEFAULT_ACCOUNT : envVar.slice('TRIPLETEX_TOKEN_'.length).toLowerCase(),
      envVar,
    }));
  // Bare employeeToken (med consumerToken) og ingen TRIPLETEX_TOKEN: det er da standardkontoen.
  if (!liste.some((a) => a.account === DEFAULT_ACCOUNT) && process.env.TRIPLETEX_EMPLOYEE_TOKEN?.trim()) {
    liste.push({ account: DEFAULT_ACCOUNT, envVar: 'TRIPLETEX_EMPLOYEE_TOKEN' });
  }
  return liste.sort((a, b) => (a.account === DEFAULT_ACCOUNT ? -1 : b.account === DEFAULT_ACCOUNT ? 1 : a.account.localeCompare(b.account)));
}

/** Merkelapp for kontoen i utskrift: tom med én nøkkel, ellers « via <konto>». */
export function viaKonto(account) {
  return account && accounts().length > 1 ? ` via ${account}` : '';
}

/** Tokenet (uten å vise det) for en konto. */
export function tokenOf(account = DEFAULT_ACCOUNT) {
  const entry = accounts().find((a) => a.account === account);
  return entry ? process.env[entry.envVar].trim() : undefined;
}

function isoDate(d) {
  return d.toISOString().slice(0, 10);
}

function decodeBase64Json(s) {
  try {
    return JSON.parse(Buffer.from(s.replace(/-/g, '+').replace(/_/g, '/'), 'base64').toString('utf8'));
  } catch {
    return null;
  }
}

/** Ser på tokenet uten å sende det noe sted. Brukes til diagnose og valg av strategi. */
export function inspectToken(token) {
  if (!token) return { kind: 'none' };
  const refresh = token.startsWith('tlxr_');
  const parts = token.replace(/^tlxr_/, '').split('.');
  if (parts.length === 3) {
    const payload = decodeBase64Json(parts[1]);
    if (payload) {
      return {
        kind: refresh ? 'jwt-refresh' : 'jwt',
        payload,
        expires: payload.exp ? new Date(payload.exp * 1000) : undefined,
      };
    }
  }
  const json = decodeBase64Json(token);
  if (json && 'tokenId' in json) return { kind: 'tripletex', tokenId: json.tokenId };
  return { kind: 'unknown' };
}

function basic(companyId, token) {
  return `Basic ${Buffer.from(`${companyId}:${token}`).toString('base64')}`;
}

async function probe(authorization) {
  const res = await fetch(`${BASE_URL}/token/session/>whoAmI?fields=employeeId`, {
    headers: { Authorization: authorization, Accept: 'application/json' },
  });
  return res.ok;
}

async function createSession(consumerToken, employeeToken) {
  const expires = new Date();
  expires.setDate(expires.getDate() + 1);
  const params = new URLSearchParams({ consumerToken, employeeToken, expirationDate: isoDate(expires) });
  const res = await fetch(`${BASE_URL}/token/session/:create?${params}`, { method: 'PUT' });
  if (!res.ok) return null;
  const { value } = await res.json();
  return { token: value.token, expires: value.expirationDate };
}

// JWT refresh token (tlxr_...) -> kortlevd JWT sessionToken via /token/session/:createFromRefreshToken.
const REFRESH_TTL_SECONDS = 8 * 60 * 60; // maks tillatt: 8 timer

async function sessionFromRefreshToken(refreshToken) {
  const res = await fetch(`${BASE_URL}/token/session/:createFromRefreshToken`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify({ refreshToken, ttlSeconds: REFRESH_TTL_SECONDS }),
  });
  if (!res.ok) {
    throw new Error(`Tripletex avviste JWT refresh-tokenet (${res.status}): ${await res.text()}`);
  }
  const { value } = await res.json();
  // Forny et minutt før utløp.
  return { token: value.token, expiresAt: Date.now() + (REFRESH_TTL_SECONDS - 60) * 1000 };
}

async function resolve(account) {
  const token = tokenOf(account);
  const envVar = accounts().find((a) => a.account === account)?.envVar ?? 'TRIPLETEX_TOKEN';

  if (token?.startsWith('tlxr_')) {
    const s = await sessionFromRefreshToken(token).catch((err) => {
      throw new Error(`[${envVar}] ${err.message}`);
    });
    if (await probe(basic(0, s.token))) return { mode: 'jwt-refresh', ...s };
    if (await probe(`Bearer ${s.token}`)) return { mode: 'jwt-refresh-bearer', ...s };
    throw new Error('Fikk JWT sessionToken fra refresh-tokenet, men Tripletex godtok det ikke i kall (401).');
  }
  const consumerToken = process.env.TRIPLETEX_CONSUMER_TOKEN?.trim();
  const employeeToken = (account === DEFAULT_ACCOUNT && process.env.TRIPLETEX_EMPLOYEE_TOKEN?.trim()) || token;

  if (!token && !employeeToken) {
    throw new Error(`Mangler ${envVar} i .env (kjør npm run set-token).`);
  }

  if (token && (await probe(basic(0, token)))) {
    return { mode: 'session', token };
  }

  if (consumerToken && employeeToken) {
    const s = await createSession(consumerToken, employeeToken);
    if (s) return { mode: 'employee', ...s };
  }

  if (token && inspectToken(token).kind === 'jwt' && (await probe(`Bearer ${token}`))) {
    return { mode: 'bearer', token };
  }

  const info = inspectToken(token);
  if (info.kind === 'jwt' && info.expires && info.expires < new Date()) {
    throw new Error(`Tokenet utløp ${info.expires.toLocaleString('nb-NO')}. Be om et nytt.`);
  }
  throw new Error(
    `[${envVar}] Tripletex avviste tokenet (401). Det er verken et gyldig sessionToken eller en ekte JWT` +
      (consumerToken
        ? ', og det kunne ikke brukes som employeeToken sammen med TRIPLETEX_CONSUMER_TOKEN.'
        : '. Er det et employeeToken, må TRIPLETEX_CONSUMER_TOKEN også fylles inn.') +
      ` (API: ${BASE_URL})`,
  );
}

/** Autorisasjons-header for et kall i konteksten til `companyId`, med tokenet til `account`. */
export async function authorization(companyId = 0, account = DEFAULT_ACCOUNT) {
  let state = states.get(account);
  if (state?.mode === 'employee' && state.expires <= isoDate(new Date())) state = null;
  if (state?.expiresAt && state.expiresAt <= Date.now()) state = null;
  if (!state) {
    state = await resolve(account);
    states.set(account, state);
  }

  if (state.mode === 'bearer' || state.mode === 'jwt-refresh-bearer') {
    if (companyId !== 0) {
      throw new Error('Bearer-JWT støtter ikke å velge klient via companyId. Bruk et sessionToken/employeeToken.');
    }
    return `Bearer ${state.token}`;
  }
  return basic(companyId, state.token);
}

/** Glemmer gjeldende sesjon (f.eks. etter 401), slik at neste kall autentiserer på nytt. */
export function resetAuth(account = DEFAULT_ACCOUNT) {
  states.delete(account);
}

export function authMode(account = DEFAULT_ACCOUNT) {
  return states.get(account)?.mode;
}
