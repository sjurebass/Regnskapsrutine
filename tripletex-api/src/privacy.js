// Personvern (GDPR): masker personopplysninger før data vises, logges eller lagres.
// Brukes på all utskrift fra CLI-et. Rådata i minnet røres ikke, så beregninger virker som før.

// Felt som alltid er personopplysninger, uansett hvor de står.
const ALWAYS = new Set([
  'nationalIdentityNumber', 'dnumber', 'dateOfBirth', 'internationalId',
  'bankAccountNumber', 'iban', 'bic', 'bankAccount',
  'email', 'invoiceEmail', 'overdueNoticeEmail', 'emailAddress',
  'phoneNumber', 'phoneNumberMobile', 'phoneNumberWork', 'phoneNumberHome', 'phoneNumberMobileCountry',
]);

// Objekter som handler om en person – her maskeres også navn og adresse.
const PERSON_KEYS = new Set([
  'employee', 'employees', 'contact', 'contacts', 'nextOfKin', 'actualEmployee', 'approvedBy',
  'completedBy', 'projectManager', 'accountManager', 'attn', 'participant', 'participants', 'passenger', 'passengers',
]);
const PERSON_FIELDS = new Set([
  'firstName', 'lastName', 'name', 'displayName', 'addressLine1', 'addressLine2', 'postalCode', 'city',
  'address', 'address1', 'address2', 'homeAddress', 'postalAddress', 'physicalAddress', 'deliveryAddress',
]);

function maskValue(key, v) {
  if (v === null || v === undefined || v === '') return v;
  if (typeof v === 'object') return '[skjult]';
  const s = String(v);
  if (key === 'firstName' || key === 'lastName') return s ? `${s[0]}.` : s;
  if (key.toLowerCase().includes('email')) return '***@***';
  return '[skjult]';
}

/** Returnerer en kopi med personopplysninger maskert. */
export function redact(data, inPerson = false) {
  if (Array.isArray(data)) return data.map((x) => redact(x, inPerson));
  if (!data || typeof data !== 'object') return data;
  // Objektet er en person hvis det har personnavn/fødselsnr., eller er en kunde/leverandør som er privatperson.
  const person = inPerson || 'firstName' in data || 'lastName' in data || 'nationalIdentityNumber' in data || data.isPrivateIndividual === true;
  const out = {};
  for (const [k, v] of Object.entries(data)) {
    if (ALWAYS.has(k) || (person && PERSON_FIELDS.has(k))) out[k] = maskValue(k, v);
    else out[k] = redact(v, PERSON_KEYS.has(k)); // arves ikke: avdeling o.l. under en person er ikke personopplysning
  }
  return out;
}

/** Endepunkter der hele svaret i praksis er personopplysninger (lønn, ansatte, pårørende osv.). */
export const PERSONAL_PATHS = [/^\/employee/, /^\/salary/, /^\/contact/, /^\/timesheet/, /^\/travelExpense/];

export function isPersonalPath(path) {
  return PERSONAL_PATHS.some((re) => re.test(path));
}

// Fritekst (posteringstekst, kontonavn, EHF-merknader, PDF-tekst) maskeres ikke av redact(), som bare
// kjenner feltnavn. redactText() fjerner mønstrene som kan kjennes igjen maskinelt. Personnavn kan
// ikke fjernes pålitelig, så fritekst skal uansett ikke siteres i rapporter eller chat – bruk
// bilagsnummer, konto og beløp.
const TEKSTMONSTRE = [
  [/[^\n]*\b(pin|pin-kode|passord|password|engangskode|brukernavn|username|login)\b[^\n]*/gi, '[linje med tilgangsinfo fjernet]'],
  [/[\w.+-]+@[\w-]+(\.[\w-]+)+/g, '***@***'], // e-post
  [/\b[A-Z]{2}\d{2}(?:[ ]?[A-Z0-9]{4}){2,7}(?:[ ]?[A-Z0-9]{1,4})?\b/g, '[IBAN]'],
  [/\b\d{4}[. ]?\d{2}[. ]?\d{5}\b/g, '[kontonr]'], // kontonummer, også uten skilletegn
  [/\b\d{6}[ -]?\d{5}\b/g, '[11 siffer]'], // fødselsnummer (også med bindestrek)
  [/(?:\+47[ ]?|0047[ ]?)?\b[2-9]\d(?:[ ]?\d{2}){3}\b/g, '[tlf]'], // 8 siffer: 91234567, 91 23 45 67, 912 34 567, +4791234567
  [/(?:\+47[ ]?|0047[ ]?)?\b[2-9]\d{2}[ ]\d{2}[ ]\d{3}\b/g, '[tlf]'], // 912 34 567
  [/(?:\+47[ ]?|0047[ ]?)\d{8}\b/g, '[tlf]'],
];

/** Returnerer teksten med e-post, kontonummer, IBAN, 11-sifrede nummer, telefonnummer og PIN/passord maskert. */
export function redactText(tekst) {
  if (tekst === null || tekst === undefined) return tekst;
  let s = String(tekst);
  for (const [re, til] of TEKSTMONSTRE) s = s.replace(re, til);
  return s;
}

// Strukturerte strengfelt som ikke er fritekst og skal stå urørt (org.nr., KID, nummer, lenker).
const STRUKTUR = new Set(['organizationNumber', 'kid', 'kidNumber', 'url', 'number', 'numberAsString', 'invoiceNumber',
  'vendorInvoiceNumber', 'displayNumber', 'externalVoucherNumber', 'version', 'changes', 'currencyCode', 'code', 'isoAlpha2Code']);

/** redactText() på alle strengfelt i et svar (fritekst som beskrivelser, kommentarer og filnavn). */
export function redactFritekst(data, key = '') {
  if (typeof data === 'string') return STRUKTUR.has(key) ? data : redactText(data);
  if (Array.isArray(data)) return data.map((x) => redactFritekst(x, key));
  if (!data || typeof data !== 'object') return data;
  return Object.fromEntries(Object.entries(data).map(([k, v]) => [k, redactFritekst(v, k)]));
}

/** Standard maskering av API-svar før utskrift eller lagring: personfelt (redact) og fritekst (redactText). */
export function maskert(data) {
  return redactFritekst(redact(data));
}
