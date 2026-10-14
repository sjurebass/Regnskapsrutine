// Legger inn en nøkkel i tripletex-api/.env uten at den vises på skjermen eller havner i kommandohistorikken.
//   npm run set-token              -> TRIPLETEX_TOKEN            (din egen nøkkel – det vanlige)
//   npm run set-token -- <navn>    -> TRIPLETEX_TOKEN_<NAVN>     (bare ved tilgang via flere byråer)
//   npm run set-token -- employee  -> TRIPLETEX_EMPLOYEE_TOKEN   (employeeToken, krever også consumer)
//   npm run set-token -- consumer  -> TRIPLETEX_CONSUMER_TOKEN
//
// Nøkkelen skrives aldri ut – heller ikke deler av den. tripletex-api/.env er git-ignorert.

import { readFileSync, writeFileSync, existsSync, copyFileSync } from 'node:fs';

const arg = process.argv[2]?.trim();
if (arg && !/^[a-z0-9_]+$/i.test(arg)) {
  console.error('Navnet kan bare inneholde bokstaver a–z, tall og _ (f.eks. byraa2).');
  process.exit(1);
}
const navn = arg?.toLowerCase();
const key =
  navn === 'consumer' ? 'TRIPLETEX_CONSUMER_TOKEN'
  : navn === 'employee' ? 'TRIPLETEX_EMPLOYEE_TOKEN'
  : !navn || navn === 'standard' ? 'TRIPLETEX_TOKEN'
  : `TRIPLETEX_TOKEN_${navn.toUpperCase()}`;
const ENV = new URL('../.env', import.meta.url); // tripletex-api/.env
const EXAMPLE = new URL('../.env.example', import.meta.url);

const CTRL_C = String.fromCharCode(3);
const BACKSPACE = [String.fromCharCode(8), String.fromCharCode(127)];
const CLEAR_LINE = String.fromCharCode(27) + '[K';

function readHidden(prompt) {
  return new Promise((resolve, reject) => {
    const { stdin, stdout } = process;
    if (!stdin.isTTY) {
      reject(new Error('Kjør kommandoen direkte i en terminal (ikke via pipe).'));
      return;
    }
    stdout.write(prompt);
    stdin.setRawMode(true);
    stdin.resume();
    stdin.setEncoding('utf8');
    let value = '';
    const done = (err) => {
      stdin.setRawMode(false);
      stdin.pause();
      stdin.off('data', onData);
      stdout.write('\n');
      err ? reject(err) : resolve(value);
    };
    const onData = (chunk) => {
      for (const ch of chunk) {
        if (ch === '\r' || ch === '\n') return done();
        if (ch === CTRL_C) return done(new Error('Avbrutt – ingenting er endret.'));
        if (BACKSPACE.includes(ch)) value = value.slice(0, -1);
        else if (ch >= ' ') value += ch;
      }
      // Bare et fast merke for at noe er limt inn – verken lengde eller tegn vises.
      stdout.write(`\r${prompt}${value ? '[mottatt]' : ''}${CLEAR_LINE}`);
    };
    stdin.on('data', onData);
  });
}

try {
  if (!existsSync(ENV)) {
    if (existsSync(EXAMPLE)) copyFileSync(EXAMPLE, ENV);
    else writeFileSync(ENV, '');
  }

  const token = (await readHidden(`Lim inn ${key} og trykk Enter: `)).trim().replace(/^["']|["']$/g, '');
  if (!token) throw new Error('Tom nøkkel – ingenting er endret.');
  if (/\s/.test(token)) throw new Error('Nøkkelen inneholder mellomrom/linjeskift – sjekk at du kopierte riktig. Ingenting er endret.');

  const lines = readFileSync(ENV, 'utf8').replace(/^﻿/, '').split(/\r?\n/);
  const i = lines.findIndex((l) => l.startsWith(`${key}=`));
  if (i >= 0) lines[i] = `${key}=${token}`;
  else lines.push(`${key}=${token}`);
  writeFileSync(ENV, lines.join('\n'));

  console.log(`${key} er lagret i tripletex-api/.env. Sjekk med: npm run token`);
} catch (err) {
  console.error(`Feil: ${err.message}`);
  process.exitCode = 1;
}
