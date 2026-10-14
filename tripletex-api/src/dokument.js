// Dokumentet bak et bilag eller en leverandørfaktura som PDF + maskert tekst – KUN LESING.
//
//   npm run -s dokument -- --client "Klient" --bilag 123-2026 [--ut <mappe>]     (bilagsnummer-år)
//   npm run -s dokument -- --client "Klient" --bilag <voucher-id> [--ut <mappe>]  (Tripletex-id)
//   npm run -s dokument -- --client "Klient" --faktura <leverandørfaktura-id> [--ut <mappe>]
//
// Skriver <ut>/<id>.pdf (originalen) og <ut>/<id>.txt (teksten, maskert med redactText; krever pdftotext).
// Standard --ut: %TEMP%\rr\dokument-<klient-id>. Konsollen viser bare sti, størrelse og antall tegn – aldri innholdet.
// Kall: GET /ledger/voucher (nummer → id), GET /ledger/voucher/{id}/pdf, ellers /document/{id}/content;
//       GET /supplierInvoice/{id}/pdf for leverandørfaktura.

import { writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { spawnSync } from 'node:child_process';
import { connect } from './tripletex.js';
import { redactText } from './privacy.js';
import { argumenter, utmappe, kortFeil } from './valg.js';

const a = argumenter(process.argv.slice(2));

async function finnBilag(b, ref) {
  const m = String(ref).match(/^(\d+)-(\d{4})$/);
  const felt = 'id,number,year,date,attachment(id,fileName,mimeType),document(id,fileName,mimeType),ediDocument(id)';
  if (m) {
    const [, nr, aar] = m;
    const v = await b.list('/ledger/voucher', { query: { number: nr, dateFrom: `${aar}-01-01`, dateTo: `${Number(aar) + 1}-01-01`, fields: felt } });
    const treff = v.filter((x) => String(x.number) === nr && String(x.year) === aar);
    if (!treff.length) throw new Error(`Fant ikke bilag ${ref} – ingenting er hentet.`);
    if (treff.length > 1) throw new Error(`Flere bilag har nummer ${ref} (ulike bilagsserier?) – bruk id: ${treff.map((x) => x.id).join(', ')}.`);
    return treff[0];
  }
  if (!/^\d+$/.test(String(ref))) throw new Error('--bilag må være <nummer>-<år> (f.eks. 123-2026) eller bilagets id.');
  return (await b.request(`/ledger/voucher/${ref}`, { query: { fields: felt } })).value;
}

const endelse = (type, navn) => {
  if (/pdf/i.test(type) || /\.pdf$/i.test(navn ?? '')) return 'pdf';
  const e = String(navn ?? '').split('.').pop()?.toLowerCase();
  return e && e.length <= 4 && e !== navn ? e : /png/i.test(type) ? 'png' : /jpe?g/i.test(type) ? 'jpg' : /xml/i.test(type) ? 'xml' : 'bin';
};

try {
  if (typeof a.client !== 'string') throw new Error('Angi --client "klient". Ingenting er gjort.');
  if (!a.bilag === !a.faktura || (a.bilag && typeof a.bilag !== 'string') || (a.faktura && typeof a.faktura !== 'string')) {
    throw new Error('Angi enten --bilag <nr-år|id> eller --faktura <id>. Ingenting er gjort.');
  }
  const b = await connect(a.client);
  const mappe = utmappe(a.ut, 'dokument', String(b.company.id));
  let id, svar, kilde, bilagsnr = null;

  if (a.faktura) {
    if (!/^\d+$/.test(a.faktura)) throw new Error('--faktura må være leverandørfakturaens id.');
    id = a.faktura;
    svar = await b.raw(`/supplierInvoice/${id}/pdf`);
    kilde = 'supplierInvoice/pdf';
  } else {
    const v = await finnBilag(b, a.bilag);
    id = String(v.id);
    bilagsnr = v.number ? `${v.number}-${v.year}` : null;
    let feil = null;
    try {
      svar = await b.raw(`/ledger/voucher/${id}/pdf`);
      kilde = 'voucher/pdf';
    } catch (e) { feil = e; }
    if (!svar?.buffer?.length) {
      // Tom eller feilet PDF: prøv originalvedlegget direkte.
      const dok = v.attachment?.id ? v.attachment : v.document?.id ? v.document : null;
      if (!dok) throw new Error(`Bilag ${bilagsnr ?? id} har ikke vedlegg eller dokument${feil ? ` (${kortFeil(feil)})` : ''} – ingenting er lagret.`);
      svar = await b.raw(`/document/${dok.id}/content`);
      svar.filnavn = dok.fileName;
      kilde = 'document/content';
    }
  }

  if (!svar?.buffer?.length) throw new Error('Tomt svar fra Tripletex – ingenting er lagret.');
  const ext = svar.buffer.subarray(0, 4).toString() === '%PDF' ? 'pdf' : endelse(svar.contentType, svar.filnavn);
  const fil = join(mappe, `${id}.${ext}`);
  writeFileSync(fil, svar.buffer);

  let txt = null, tegn = 0, merknad = null;
  if (ext === 'pdf') {
    const p = spawnSync('pdftotext', ['-layout', '-enc', 'UTF-8', fil, '-'], { encoding: 'utf8' });
    if (p.error) merknad = 'pdftotext ikke funnet – bare PDF lagret (les PDF-en direkte).';
    else {
      const tekst = redactText(p.stdout ?? '');
      tegn = tekst.replace(/\s/g, '').length;
      txt = join(mappe, `${id}.txt`);
      writeFileSync(txt, tekst);
      if (tegn < 40) merknad = 'lite eller ingen tekst – trolig skannet dokument (les PDF-en som bilde).';
    }
  } else merknad = `ikke PDF (${ext}) – ingen .txt laget.`;

  console.log(JSON.stringify({ klient: b.company.name, ...(bilagsnr ? { bilag: bilagsnr } : {}), id: Number(id), kilde, fil, byte: svar.buffer.length, txt, tegn, merknad }, null, 1));
} catch (e) {
  console.error(`Feil: ${redactText(kortFeil(e))}`);
  process.exitCode = 1;
}
