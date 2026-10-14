// EHF (ediDocument) for bilagene i terminen: hentes og tolkes maskinelt, så ingen agent trenger å lese dem.
// Lagrer bare mva-relevante felt (org.nr., MVA-merking, datoer, beløp per sats, referanse). Navn, merknader,
// varelinjer, kontaktinfo og kontonummer leses ikke ut, og rå XML lagres ikke.

import { BASE_URL, authorization } from '../auth.js';

const en = (x, re) => x.match(re)?.[1]?.trim() ?? null;
const alle = (x, re) => [...x.matchAll(re)].map((m) => m[1]);
const blokk = (x, tag) => en(x, new RegExp(`<cac:${tag}>([\\s\\S]*?)<\\/cac:${tag}>`)) ?? '';
const siffer9 = (s) => { const d = String(s ?? '').replace(/\D/g, ''); return d.length >= 9 ? d.slice(0, 9) : null; };

/** Tolker en EHF/PEPPOL BIS-faktura eller -kreditnota. */
export function tolkEhf(xml) {
  xml = xml.replace(/<cbc:EmbeddedDocumentBinaryObject[\s\S]*?<\/cbc:EmbeddedDocumentBinaryObject>/g, '');
  const selger = blokk(xml, 'AccountingSupplierParty');
  const kjoper = blokk(xml, 'AccountingCustomerParty');
  const skatt = blokk(xml, 'TaxTotal');
  // PartyTaxScheme kan forekomme to ganger (VAT og foretaksregisteret) i vilkårlig rekkefølge – velg den med TaxScheme VAT.
  const mvaId = (part) => alle(part, /<cac:PartyTaxScheme>([\s\S]*?)<\/cac:PartyTaxScheme>/g)
    .filter((s) => /<cac:TaxScheme>[\s\S]*?<cbc:ID[^>]*>\s*VAT\s*</.test(s))
    .map((s) => en(s, /<cbc:CompanyID[^>]*>([^<]+)</)).find(Boolean) ?? null;
  const selgerMvaId = mvaId(selger);
  return {
    type: /<CreditNote[\s>]/.test(xml) ? 'kreditnota' : 'faktura',
    fakturanr: en(xml, /<cbc:ID>([^<]+)<\/cbc:ID>/),
    dato: en(xml, /<cbc:IssueDate>([^<]+)</),
    valuta: en(xml, /<cbc:DocumentCurrencyCode[^>]*>([^<]+)</),
    selgerOrgnr: siffer9(en(selger, /<cac:PartyLegalEntity>[\s\S]*?<cbc:CompanyID[^>]*>([^<]+)</) ?? selgerMvaId),
    selgerMvaMerket: !!selgerMvaId && /MVA\s*$/i.test(selgerMvaId), // ikke bevis for registrering – Brreg er fasit
    kjoperOrgnr: siffer9(en(kjoper, /<cac:PartyLegalEntity>[\s\S]*?<cbc:CompanyID[^>]*>([^<]+)</) ?? mvaId(kjoper) ?? en(kjoper, /<cbc:EndpointID[^>]*>([^<]+)</)),
    mva: Number(en(skatt, /<cbc:TaxAmount[^>]*>([^<]+)</) ?? 0),
    satser: alle(skatt, /<cac:TaxSubtotal>([\s\S]*?)<\/cac:TaxSubtotal>/g).map((s) => ({
      kategori: en(s, /<cac:TaxCategory>[\s\S]*?<cbc:ID[^>]*>([^<]+)</), prosent: Number(en(s, /<cbc:Percent>([^<]+)</) ?? 0),
      grunnlag: Number(en(s, /<cbc:TaxableAmount[^>]*>([^<]+)</) ?? 0), mva: Number(en(s, /<cbc:TaxAmount[^>]*>([^<]+)</) ?? 0),
    })),
    aBetale: Number(en(xml, /<cbc:PayableAmount[^>]*>([^<]+)</) ?? NaN),
    referanse: en(xml, /<cac:BillingReference>[\s\S]*?<cbc:ID>([^<]+)</),
  };
}

/** Henter og tolker EHF for bilagene som har ediDocument. Returnerer { voucherId: tolket | { feil } }. */
export async function hentEhf(b, bilag, logg = () => {}) {
  const ut = {};
  const medEhf = bilag.filter((v) => v.ediDocument?.id);
  logg(`EHF for ${medEhf.length} bilag`);
  for (const v of medEhf) {
    try {
      const r = await fetch(`${BASE_URL}/document/${v.ediDocument.id}/content`, { headers: { Authorization: await authorization(b.company.id, b.company.account) } });
      if (!r.ok) { ut[v.id] = { feil: `HTTP ${r.status}` }; continue; }
      const tekst = Buffer.from(await r.arrayBuffer()).toString('utf8');
      ut[v.id] = tekst.trimStart().startsWith('<') ? tolkEhf(tekst) : { feil: 'ikke XML' };
    } catch (e) {
      ut[v.id] = { feil: e.message.slice(0, 120) };
    }
  }
  return ut;
}
