// UR0–UR7: klienter som ikke er mva-registrert (kontroller.md seksjon I, fradragsregler.md kap. 7).
// Deterministiske kontroller. Det som krever skjønn, merkes trengerSkjonn og går til beslutningslista/agenten.

import { lagFunn, kr } from '../felles.js';
import { iIntervall } from '../profil.js';

// Koder en klient uten registrering kan ha: ingen mva (0), utenfor/ingen behandling (6, 7) og
// omvendt avgiftsplikt uten fradrag (87, 89, 92).
const TILLATT = new Set(['0', '6', '7', '87', '89', '92']);
const OMVENDT = new Set(['87', '89', '92']);
const IMPORT = new Set(['14', '15', '20', '21', '22', '81', '82', '83', '84', '85']);
const FRADRAG_STANDARD = new Set(['1', '11', '12', '13', '14', '15', '81', '83', '86', '88', '91']);
const kode = (p) => String(p.vatType?.number ?? '0');
const er27 = (nr) => nr >= 2700 && nr <= 2749;

export function ureg(d, { t, profil, oppsett, aarlig = false }) {
  const funn = [];
  const bilagNr = new Map(d.bilag.map((v) => [v.id, v.number || (v.tempNumber ? `T${v.tempNumber}` : `id${v.id}`)]));
  const nr = (p) => bilagNr.get(p.voucher?.id) ?? `id${p.voucher?.id}`;

  // UR0 – modus må være entydig.
  if (oppsett.modus === 'UKLAR') {
    funn.push(lagFunn({
      kontroll: 'UR0', alvor: 'STOPP', nivaa: 'klient', regel: 'UR0',
      tittel: 'Mva-status er uklar',
      detalj: `Tripletex: ${oppsett.mvaStatusTripletex ?? 'ukjent'}. Enhetsregisteret: ${oppsett.mvaRegistrertBrreg === null ? `ukjent (${oppsett.brregFeil ?? 'ikke slått opp'})` : oppsett.mvaRegistrertBrreg ? 'registrert' : 'ikke registrert'}.`,
      handling: 'Avklar registreringsstatus før flyten kjøres videre (VAT_APPLICANT betyr tilbakegående avgiftsoppgjør, § 8-6).',
    }));
    return funn;
  }

  // UR1 / UR7 – koder som ikke hører hjemme, gruppert per konto og kode.
  const vouchersMedOmvendt = new Set(d.posteringer.filter((p) => OMVENDT.has(kode(p))).map((p) => p.voucher?.id));
  const grupper = new Map();
  for (const p of d.posteringer) {
    const k = kode(p);
    if (TILLATT.has(k)) continue;
    const g = `${p.account.number}|${k}`;
    if (!grupper.has(g)) grupper.set(g, { konto: p.account.number, kode: k, sum: 0, bilag: new Set() });
    const x = grupper.get(g);
    x.sum += p.amount;
    x.bilag.add(nr(p));
  }
  for (const x of grupper.values()) {
    const imp = IMPORT.has(x.kode);
    funn.push(lagFunn({
      kontroll: imp ? 'UR7' : 'UR1', alvor: 'BLOKK', konto: x.konto, belop: x.sum, bilag: [...x.bilag],
      regel: imp ? 'R-UREG-IMPORTKODE' : 'R-UREG-FRADRAG', hjemmel: imp ? 'mval. § 11-1' : 'mval. § 8-1',
      tittel: imp ? `Innførselskode ${x.kode} på konto ${x.konto}` : `Mva-kode ${x.kode} på konto ${x.konto}`,
      detalj: `${x.bilag.size} bilag, sum ${kr(x.sum)} kr. Klienten er ikke mva-registrert og skal ikke ha fradrag eller utgående mva – mva er en del av kostnaden.`,
      handling: 'Endre koden til 0 (brutto på kostnaden) med korreksjonsbilag, etter ja.',
    }));
  }
  // 27xx skal være tom, bortsett fra skyldig mva ved omvendt avgiftsplikt.
  const medFeilKode = new Set(d.posteringer.filter((p) => !TILLATT.has(kode(p))).map((p) => p.voucher?.id));
  const mva27 = d.posteringer.filter((p) => er27(p.account.number) && !vouchersMedOmvendt.has(p.voucher?.id)
    && !(p.systemGenerated && medFeilKode.has(p.voucher?.id))); // mva fra en feil kode rapporteres under koden
  if (mva27.length) {
    const sum = mva27.reduce((s, p) => s + p.amount, 0);
    funn.push(lagFunn({
      kontroll: 'UR1', alvor: 'BLOKK', konto: '2700–2749', belop: sum, bilag: [...new Set(mva27.map(nr))], regel: 'R-UREG-27XX',
      tittel: 'Posteringer på mva-kontoene', detalj: `${mva27.length} posteringer, sum ${kr(sum)} kr, uten omvendt avgiftsplikt i samme bilag.`,
      handling: 'Flytt beløpet til kostnaden (klienten har ikke fradragsrett).',
    }));
  }
  // Brutto på kostnadslinjene: amount skal være lik amountGross når koden er tillatt.
  const netto = d.posteringer.filter((p) => TILLATT.has(kode(p)) && !OMVENDT.has(kode(p)) && !er27(p.account.number)
    && p.amountGross !== undefined && Math.abs((p.amountGross ?? p.amount) - p.amount) >= 1);
  if (netto.length) {
    const diff = netto.reduce((s, p) => s + (p.amountGross - p.amount), 0);
    funn.push(lagFunn({
      kontroll: 'UR1', alvor: 'BLOKK', belop: diff, bilag: [...new Set(netto.map(nr))], regel: 'R-UREG-BRUTTO',
      tittel: 'Kostnad ført netto', detalj: `${netto.length} linjer der beløp og bruttobeløp er ulike (sum differanse ${kr(diff)} kr).`,
    }));
  }

  // UR2 – kostnadskontoer med fradragskode som standard (én gang per konto med bevegelse).
  const bevegelse = new Map();
  for (const p of d.posteringer) {
    const b = bevegelse.get(p.account.number) ?? { antall: 0, sum: 0 };
    b.antall++; b.sum += p.amount;
    bevegelse.set(p.account.number, b);
  }
  const risikokontoer = d.kontoer.filter((a) => FRADRAG_STANDARD.has(String(a.vatType?.number)) && a.number >= 1000 && a.number <= 7999 && bevegelse.has(a.number));
  if (aarlig && risikokontoer.length) { // kontoplanen endres sjelden – årlig kontroll
    funn.push(lagFunn({
      kontroll: 'UR2', alvor: 'INFO', nivaa: 'klient', regel: 'R-UREG-KONTOPLAN',
      tittel: `${risikokontoer.length} kontoer med fradragskode som standard`,
      detalj: risikokontoer.map((a) => `${a.number} (kode ${a.vatType.number}, ${bevegelse.get(a.number).antall} poster)`).join(', '),
      handling: 'Vurder å sette standardkode 0 på kontoene, så fakturamottak ikke foreslår fradrag (endring i kontoplanen, etter ja).',
      data: risikokontoer.map((a) => a.number),
    }));
  }

  // UR3 – registreringsplikt, rullerende 12 måneder.
  const inntekter = d.saldo12.filter((s) => s.account.number >= 3000 && s.account.number <= 3999 && Math.abs(s.balanceChange) >= 1);
  const klasse = (nrKonto) => profil.inntektKlassifisering.find((k) => iIntervall(nrKonto, k.intervaller))?.klasse ?? null;
  const uklassifisert = inntekter.filter((s) => !klasse(s.account.number));
  const avgiftspliktig = -inntekter.filter((s) => klasse(s.account.number) === 'avgiftspliktig').reduce((s, x) => s + x.balanceChange, 0);
  // Termin: spør bare om inntektskontoer med bevegelse i terminen (nye). Årlig eller uten klassifisering: alle.
  const bevegelseT = new Set(d.saldo.filter((s) => s.account.number >= 3000 && s.account.number <= 3999 && Math.abs(s.balanceChange) >= 1).map((s) => s.account.number));
  const aaSporeOm = uklassifisert.filter((s) => aarlig || !profil.inntektKlassifisering.length || bevegelseT.has(s.account.number));
  if (aaSporeOm.length) {
    funn.push(lagFunn({
      kontroll: 'UR3', alvor: 'SPØR_REGNSKAPSFØRER', nivaa: 'klient', trengerSkjonn: true, regel: 'UR3', hjemmel: 'mval. § 2-1',
      tittel: 'Inntektskontoene er ikke klassifisert for registreringsplikt',
      detalj: `Siste 12 måneder: ${aaSporeOm.map((s) => `${s.account.number} ${kr(-s.balanceChange)} kr`).join(', ')}.`,
      handling: 'Klassifiser hver konto som avgiftspliktig, unntatt (f.eks. salg av fast eiendom, § 3-11) eller utenfor, og lagre i klientprofil.md (inntekt_klassifisering).',
      data: aaSporeOm.map((s) => ({ konto: s.account.number, sum12: -s.balanceChange })),
    }));
  }
  if (avgiftspliktig > 50_000) {
    funn.push(lagFunn({ kontroll: 'UR3', alvor: 'BLOKK', nivaa: 'klient', belop: avgiftspliktig, regel: 'UR3', hjemmel: 'mval. § 2-1',
      tittel: 'Avgiftspliktig omsetning over registreringsgrensen', detalj: `${kr(avgiftspliktig)} kr siste 12 måneder (grense 50 000 kr).`,
      handling: 'Vurder registrering i Merverdiavgiftsregisteret.' }));
  } else if (avgiftspliktig > 40_000) {
    funn.push(lagFunn({ kontroll: 'UR3', alvor: 'INFO', nivaa: 'klient', belop: avgiftspliktig, regel: 'UR3',
      tittel: 'Avgiftspliktig omsetning nær registreringsgrensen', detalj: `${kr(avgiftspliktig)} kr siste 12 måneder (grense 50 000 kr).` }));
  }

  // UR4 – byggearbeid i egen regi (§ 3-26), én gang per klient.
  const sum12 = (fn) => d.saldo12.filter((s) => fn(s.account.number)).reduce((s, x) => s + x.balanceChange, 0);
  const lonn = sum12((n) => n >= 5000 && n <= 5999);
  const aktivering = sum12((n) => n === 1130 || (n >= 1400 && n <= 1499));
  const prosjekt = profil.kontoProsjekt.length ? sum12((n) => iIntervall(n, profil.kontoProsjekt)) : 0;
  // Profilfeltet s3_26_vurdering: «ingen plikt …» lukker punktet. «plikt …» (uttaksplikt konstatert) holder det
  // åpent som noe som må rettes, til klienten er registrert eller regnskapsføreren har konkludert.
  const ingenPlikt = profil.s326 && /ingen\s+(uttaks)?plikt/i.test(profil.s326);
  const plikt = profil.s326 && !ingenPlikt && /plikt/i.test(profil.s326);
  if (plikt) {
    funn.push(lagFunn({ kontroll: 'UR4', alvor: 'BLOKK', nivaa: 'klient', regel: 'R-UREG-3-26', hjemmel: 'mval. §§ 3-26 og 2-1',
      tittel: 'Uttaksplikt etter § 3-26 – klienten er ikke registrert', detalj: profil.s326,
      handling: 'Følg vurderingsnotatet: kartlegg tid på prosjektene, beregn uttaket, avklar registreringstidspunkt og etterberegning.',
      data: { lonn12: lonn, aktivering12: aktivering, prosjekt12: prosjekt } }));
  } else if (lonn > 0 && (Math.abs(aktivering) >= 1 || Math.abs(prosjekt) >= 1) && (!ingenPlikt || aarlig)) {
    funn.push(ingenPlikt
      ? lagFunn({ kontroll: 'UR4', alvor: 'INFO', nivaa: 'klient', regel: 'R-UREG-3-26', tittel: '§ 3-26 er vurdert', detalj: profil.s326 })
      : lagFunn({
        kontroll: 'UR4', alvor: 'SPØR_REGNSKAPSFØRER', nivaa: 'klient', trengerSkjonn: true, regel: 'R-UREG-3-26', hjemmel: 'mval. §§ 3-26 og 2-1',
        tittel: 'Mulig byggearbeid i egen regi (§ 3-26)',
        detalj: `Siste 12 måneder: lønnskostnad ${kr(lonn)} kr, bevegelse på aktivering/lager ${kr(aktivering)} kr${profil.kontoProsjekt.length ? `, prosjektkontoer ${kr(prosjekt)} kr` : ''}. Hvis egne ansatte utfører byggearbeid eller byggeadministrasjon på bygg for salg/utleie, gir det uttaksplikt og kan gi registreringsplikt.`,
        handling: 'Avklar hva de ansatte gjør (byggearbeid, byggeledelse, byggherreombud eller bare administrasjon/salg), og lagre konklusjonen i klientprofil.md (s3_26_vurdering). Legg prosjektkontoene i konto_prosjekt.',
        data: { lonn12: lonn, aktivering12: aktivering, prosjekt12: prosjekt },
      }));
  }

  // UR5 – omvendt avgiftsplikt for kjøper uten registrering, per kalenderkvartal (grense 2 000 kr).
  const levById = new Map(d.leverandorer.map((l) => [l.id, l]));
  // Fjernleverbar tjeneste fra utlandet: vurdert med omvendt-kode (86–89/91/92), eller UT: uten vurdering. VOEC og varer teller ikke.
  const utenlandsk = (l) => {
    if (!l) return false;
    const v = l.vurdering;
    if (v) return v.voec !== true && !/vare/i.test(v.kostnadstype ?? '') && ['86', '87', '88', '89', '91', '92'].includes(String(v.omvendt_avgiftsplikt ?? ''));
    return !!l.nokkel?.startsWith('UT:');
  };
  const brukt = new Set(d.posteringer.map((p) => p.supplier?.id).filter(Boolean));
  const uklassifiserte = d.leverandorer.filter((l) => !l.orgnr && !l.vurdering && !l.nokkel?.startsWith('UT:')
    && (l.valuta?.length || (l.nokkel?.startsWith('?:') && brukt.has(l.id))));
  const perKvartal = {};
  for (const p of d.leverandorposteringer12) {
    if (p.amount >= 0 || !utenlandsk(levById.get(p.supplier?.id))) continue;
    const kv = `${p.date.slice(0, 4)}-K${Math.floor((Number(p.date.slice(5, 7)) - 1) / 3) + 1}`;
    perKvartal[kv] = (perKvartal[kv] ?? 0) - p.amount;
  }
  // Kreditnotaer fra de samme leverandørene reduserer grunnlaget.
  for (const f of d.leverandorfakturaer ?? []) {
    if (!f.isCreditNote || !f.invoiceDate || !utenlandsk(levById.get(f.supplier?.id))) continue;
    const kv = `${f.invoiceDate.slice(0, 4)}-K${Math.floor((Number(f.invoiceDate.slice(5, 7)) - 1) / 3) + 1}`;
    perKvartal[kv] = (perKvartal[kv] ?? 0) - Math.abs(f.amount ?? 0);
  }
  for (const kv of t.kvartaler) {
    const sum = perKvartal[kv] ?? 0;
    if (sum > 2000) {
      funn.push(lagFunn({ kontroll: 'UR5', alvor: 'BLOKK', nivaa: 'klient', belop: sum, regel: 'R-UREG-OMVENDT-2000',
        hjemmel: 'mval. § 11-3 første ledd annet punktum, sktfvf. §§ 8-3-9 og 8-3-10',
        tittel: `Kjøp av tjenester fra utlandet ${kv} over 2 000 kr`, detalj: `Grunnlag ${kr(sum)} kr i kvartalet.`,
        handling: 'Beregn mva med kode 87/89 og lever mva-melding for omvendt avgiftsplikt for kvartalet (frist 10.5, 31.8, 10.11 eller 10.2).' }));
    }
  }
  if (uklassifiserte.length) {
    funn.push(lagFunn({ kontroll: 'UR5', alvor: 'SPØR_REGNSKAPSFØRER', nivaa: 'klient', trengerSkjonn: true, regel: 'R-UREG-OMVENDT-2000',
      tittel: `${uklassifiserte.length} leverandører uten norsk org.nr. og uten vurdering`,
      detalj: uklassifiserte.map((l) => `${l.navn ?? '[navn skjult]'} (${l.valuta.join(',')})`).join(', '),
      handling: 'Vurder om leveransen er fjernleverbare tjenester fra utlandet, og lagre vurderingen i leverandørindeksen (npm run leverandor -- vurder).' }));
  }

  // UR6 – salg som kan være avgiftspliktig (tilvalg, endringsarbeid, viderefakturering, utleie av utstyr).
  const MONSTER = /tilvalg|endringsarbeid|ekstraarbeid|viderefakturer|utleie av (utstyr|maskin)/i;
  const vTekst = new Map(d.bilag.map((v) => [v.id, v.description ?? '']));
  const treff = new Map();
  for (const p of d.posteringer) {
    if (p.account.number < 3000 || p.account.number > 3999 || Math.abs(p.amount) < 5000) continue;
    const ord = `${p.description ?? ''} ${vTekst.get(p.voucher?.id) ?? ''}`.match(MONSTER)?.[0];
    if (ord) treff.set(p.voucher?.id, { bilag: nr(p), konto: p.account.number, belop: -p.amount, ord: ord.toLowerCase() });
  }
  for (const x of treff.values()) {
    funn.push(lagFunn({ kontroll: 'UR6', alvor: 'SPØR_REGNSKAPSFØRER', konto: x.konto, belop: x.belop, bilag: [x.bilag], trengerSkjonn: true,
      regel: 'R-UREG-SALG-AVGIFTSPLIKTIG / R-TILVALG-BOLIGSALG', hjemmel: 'mval. §§ 3-1 og 3-11, BFU 15/13',
      tittel: `Inntekt som kan være avgiftspliktig (teksttreff «${x.ord}»)`,
      detalj: `Bilag ${x.bilag}, konto ${x.konto}, ${kr(x.belop)} kr. Tilvalg til samme kjøper som kjøper eiendommen følger normalt det unntatte salget. Ulike kjøpere eller levering etter overtakelse kan gjøre tilvalget avgiftspliktig.`,
      handling: 'Se kjøpekontrakt og tilvalgsavtale (kjøper, tidspunkt for overtakelse).' }));
  }
  return funn;
}
