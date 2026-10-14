// Felles kommandolinjevalg: argumenter, klientutvalg (--client, gjentatt --client, --alle) og standard utmappe.

import { join, resolve } from 'node:path';
import { tmpdir } from 'node:os';
import { mkdirSync } from 'node:fs';
import { clients, client } from './tripletex.js';

/**
 * «--navn verdi» og «--flagg» → { navn: verdi, flagg: true }. Gjentatte valg samles i `flere[navn]` (liste).
 * Posisjonelle argumenter havner i `_`.
 */
export function argumenter(liste) {
  const a = { _: [], flere: {} };
  for (let i = 0; i < liste.length; i++) {
    const x = liste[i];
    if (!x.startsWith('--')) { a._.push(x); continue; }
    const navn = x.slice(2);
    const neste = liste[i + 1];
    const verdi = neste === undefined || neste.startsWith('--') ? true : (i++, neste);
    a[navn] = verdi;
    (a.flere[navn] ??= []).push(verdi);
  }
  return a;
}

/**
 * Klientene kommandoen gjelder: `--alle`, eller én eller flere `--client`. Velger aldri en klient på egen hånd.
 * Returnerer klientobjekter fra clients() (id, name, organizationNumber, account).
 */
export async function klientutvalg(a) {
  if (a.alle === true) return clients();
  const navn = (a.flere?.client ?? []).filter((x) => typeof x === 'string');
  if (!navn.length) throw new Error('Angi --client "klient" (kan gjentas) eller --alle. Ingenting er gjort.');
  const ut = [];
  for (const n of navn) ut.push(await client(n)); // sekvensielt
  return ut;
}

/** Standard utmappe: %TEMP%\rr\<kommando>-<periode>. Aldri inne i repoet. */
export function standardUt(kommando, periode) {
  return join(tmpdir(), 'rr', `${kommando}${periode ? `-${periode}` : ''}`);
}

/** Utmappa: --ut hvis gitt, ellers standard. Lages hvis den ikke finnes. */
export function utmappe(ut, kommando, periode) {
  const m = resolve(typeof ut === 'string' ? ut : standardUt(kommando, periode));
  mkdirSync(m, { recursive: true });
  return m;
}

/**
 * Kjører fn(klient) for hver klient, én om gangen (tokenfornyingen tåler ikke parallelle kall).
 * Nettverksbrudd prøves inntil tre ganger. Feil stopper ikke de andre klientene.
 * Returnerer [{ klient, orgnr, ok, data | feil }].
 */
export async function perKlient(utvalg, fn, { forsok = 3 } = {}) {
  const ut = [];
  for (const c of utvalg) {
    let data, feil;
    for (let i = 1; i <= forsok; i++) {
      try { data = await fn(c); feil = undefined; break; } catch (e) {
        feil = e;
        const forbigaaende = /fetch failed|ECONNRESET|ETIMEDOUT|socket/i.test(e.message);
        if (!forbigaaende || i === forsok) break;
        await new Promise((r) => setTimeout(r, 3000 * i));
      }
    }
    ut.push(feil ? { klient: c.name, orgnr: c.organizationNumber ?? '', ok: false, feil: kortFeil(feil) } : { klient: c.name, orgnr: c.organizationNumber ?? '', ok: true, data });
  }
  return ut;
}

/** Første linje av en feilmelding, kortet ned (uten responskropp fra Tripletex). */
export function kortFeil(e) {
  const m = String(e?.message ?? e).split('\n')[0];
  const status = m.match(/feilet \((\d{3})\)/)?.[1];
  const melding = m.match(/"message"\s*:\s*"([^"]{0,160})/)?.[1];
  const detalj = m.match(/"validationMessages"\s*:\s*\[\{[^\]]*?"message"\s*:\s*"([^"]{0,200})/)?.[1];
  return status ? `HTTP ${status}${melding ? `: ${melding}` : ''}${detalj ? ` (${detalj})` : ''}` : m.slice(0, 200);
}

/** Måned ÅÅÅÅ-MM → første dag i neste måned (eksklusiv til-dato i Tripletex). */
export const nesteMnd = (m) => { const d = new Date(`${m}-01T00:00:00Z`); d.setUTCMonth(d.getUTCMonth() + 1); return d.toISOString().slice(0, 10); };

/** Alle måneder fra og med `fra` til og med `til` (ÅÅÅÅ-MM). */
export function maanederMellom(fra, til) {
  const ut = [];
  for (let d = new Date(`${fra}-01T00:00:00Z`); d <= new Date(`${til}-01T00:00:00Z`); d.setUTCMonth(d.getUTCMonth() + 1)) ut.push(d.toISOString().slice(0, 7));
  return ut;
}

export const erMaaned = (s) => /^\d{4}-(0[1-9]|1[0-2])$/.test(s ?? '');
export const rund = (n) => Math.round((n ?? 0) * 100) / 100;
