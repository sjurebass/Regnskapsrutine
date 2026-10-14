"""Kontroll av ferdige Silfer-filer før de lagres i Tally.

    uv run --with openpyxl --with pypdf python .claude/skills/silfer-rapport/scripts/sjekk.py <fil.xlsx> [<fil.pdf> …]

LibreOffice finnes ikke på maskinene, så formlene kan ikke beregnes her; sjekken er strukturell.
xlsx: feilverdier (#REF! …), formler med semikolon eller norske/ukjente funksjonsnavn, referanser til ark som ikke
finnes eller rader utenfor arket, logo i hvert ark med topp, betingede formater, frys og filter (vises).
pdf: antall sider, «Side n av N» på hver side, tittel og «Org.nr.» på side 1, logo (bilde) på side 1,
/Title og /Author = «Silfer AS».
Exit 0 = alt i orden, 1 = minst én feil.
"""

from __future__ import annotations

import posixpath
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent))

from silfer.filer import os_sti  # noqa: E402

FEILVERDIER = {"#REF!", "#VALUE!", "#DIV/0!", "#NAME?", "#N/A", "#NUM!", "#NULL!", "#SPILL!", "#CALC!"}
ENGELSKE = {"SUM", "SUMIF", "SUMIFS", "COUNT", "COUNTA", "COUNTIF", "COUNTIFS", "COUNTBLANK", "IF", "IFS", "IFERROR",
            "ABS", "ROUND", "ROUNDUP", "ROUNDDOWN", "AND", "OR", "NOT", "MIN", "MAX", "AVERAGE", "SUBTOTAL", "TEXT",
            "VLOOKUP", "XLOOKUP", "HLOOKUP", "INDEX", "MATCH", "DATE", "YEAR", "MONTH", "DAY", "EOMONTH", "TODAY",
            "LEFT", "RIGHT", "MID", "LEN", "CONCATENATE", "TRIM", "UPPER", "LOWER", "SUMPRODUCT", "ISBLANK",
            "ISNUMBER", "INT", "MOD", "N", "VALUE"}
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
      "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
      "xdr": "http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing"}
REF = re.compile(r"(?:'((?:[^']|'')+)'|([A-Za-z_][\w.]*))!\$?([A-Z]{1,3})\$?(\d+)(?::\$?([A-Z]{1,3})\$?(\d+))?")
LOKAL = re.compile(r"(?<![!'\w$])\$?([A-Z]{1,3})\$?(\d+)\b")


def _uten_strenger(f: str) -> str:
    return re.sub(r'"[^"]*"', '""', f)


def _bilder_per_ark(sti) -> dict[str, int]:
    """Teller bilder (xdr:pic) per ark direkte i zip-filen – trenger ikke Pillow."""
    ut: dict[str, int] = {}
    with zipfile.ZipFile(os_sti(sti)) as z:
        navn = set(z.namelist())
        wb = ET.fromstring(z.read("xl/workbook.xml"))
        rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        mal = {r.get("Id"): r.get("Target") for r in rels.findall("rel:Relationship", NS)}
        for ark in wb.findall("m:sheets/m:sheet", NS):
            rid = ark.get(f"{{{NS['r']}}}id")
            mål = mal.get(rid, "")
            arkfil = posixpath.normpath(posixpath.join("xl", mål.lstrip("/").removeprefix("xl/")))
            relfil = posixpath.join(posixpath.dirname(arkfil), "_rels", posixpath.basename(arkfil) + ".rels")
            antall = 0
            if relfil in navn:
                for r in ET.fromstring(z.read(relfil)).findall("rel:Relationship", NS):
                    if r.get("Type", "").endswith("/drawing"):
                        mål_t = r.get("Target", "")
                        tegn = (mål_t.lstrip("/") if mål_t.startswith("/")
                                else posixpath.normpath(posixpath.join(posixpath.dirname(arkfil), mål_t)))
                        if tegn in navn:
                            antall += len(ET.fromstring(z.read(tegn)).findall(".//xdr:pic", NS))
            ut[ark.get("name")] = antall
    return ut


def sjekk_xlsx(sti: Path) -> list[str]:
    import openpyxl

    feil: list[str] = []
    wb = openpyxl.load_workbook(os_sti(sti))
    bilder = _bilder_per_ark(sti)
    maks = {ws.title: ws.max_row for ws in wb}
    for ws in wb:
        formler = 0
        for rad in ws.iter_rows():
            for c in rad:
                v = c.value
                if c.data_type == "e" or (isinstance(v, str) and v.strip() in FEILVERDIER):
                    feil.append(f"{ws.title}!{c.coordinate}: feilverdi {v}")
                if c.data_type != "f" or not isinstance(v, str):
                    continue
                formler += 1
                f = _uten_strenger(v)
                if ";" in f:
                    feil.append(f"{ws.title}!{c.coordinate}: semikolon i formel (bruk komma): {v}")
                for navn in re.findall(r"([A-Za-zÆØÅæøå][\w.ÆØÅæøå]*)\(", f):
                    if navn.upper() not in ENGELSKE:
                        feil.append(f"{ws.title}!{c.coordinate}: ukjent eller norsk funksjon {navn}() i {v}")
                for m in REF.finditer(f):
                    ark = (m.group(1) or m.group(2)).replace("''", "'")
                    if ark not in maks:
                        feil.append(f"{ws.title}!{c.coordinate}: arket «{ark}» finnes ikke ({v})")
                        continue
                    for rr in (m.group(4), m.group(6)):
                        if rr and int(rr) > maks[ark]:
                            feil.append(f"{ws.title}!{c.coordinate}: rad {rr} er utenfor arket «{ark}» ({v})")
                for m in LOKAL.finditer(REF.sub("", f)):
                    if int(m.group(2)) > ws.max_row:
                        feil.append(f"{ws.title}!{c.coordinate}: rad {m.group(2)} er utenfor arket ({v})")
        topp = ws["D2"].value is not None
        n_bilder = bilder.get(ws.title, 0)
        if topp and n_bilder < 1:
            feil.append(f"{ws.title}: mangler logo (kjør byggingen med --with pillow)")
        cf = [str(r.sqref) for r in ws.conditional_formatting]
        print(f"  {ws.title}: {ws.max_row} rader, {formler} formler, {n_bilder} bilde(r), "
              f"statusformat {', '.join(cf) or '–'}, frys {ws.freeze_panes or '–'}, filter {ws.auto_filter.ref or '–'}")
    verdier = openpyxl.load_workbook(os_sti(sti), data_only=True)
    for ws in verdier:
        for rad in ws.iter_rows():
            for c in rad:
                if isinstance(c.value, str) and c.value.strip() in FEILVERDIER:
                    feil.append(f"{ws.title}!{c.coordinate}: lagret feilverdi {c.value}")
    return feil


def _har_bilde(obj, sett=None) -> bool:
    sett = sett if sett is not None else set()
    res = obj.get("/Resources")
    res = res.get_object() if res is not None else None
    if not res or "/XObject" not in res:
        return False
    for x in res["/XObject"].get_object().values():
        x = x.get_object()
        if id(x) in sett:
            continue
        sett.add(id(x))
        if x.get("/Subtype") == "/Image":
            return True
        if x.get("/Subtype") == "/Form" and _har_bilde(x, sett):
            return True
    return False


def sjekk_pdf(sti: Path) -> list[str]:
    from pypdf import PdfReader

    feil: list[str] = []
    r = PdfReader(os_sti(sti))
    n = len(r.pages)
    meta = r.metadata or {}
    tittel = str(meta.get("/Title") or "")
    if n < 1:
        return ["ingen sider"]
    for i, side in enumerate(r.pages, start=1):
        tekst = side.extract_text() or ""
        if f"Side {i} av {n}" not in tekst:
            feil.append(f"side {i}: mangler «Side {i} av {n}»")
        if i == 1:
            flat = re.sub(r"\s+", " ", tekst)
            if not tittel or re.sub(r"\s+", " ", tittel) not in flat:
                feil.append(f"side 1: tittelen «{tittel}» står ikke på siden")
            if "Org.nr." not in flat:
                print("  merk: «Org.nr.» står ikke på side 1 (mangler orgnr i spec?)")
            if not _har_bilde(side):
                feil.append("side 1: fant ikke logoen (bilde)")
    if meta.get("/Author") != "Silfer AS":
        feil.append(f"/Author er «{meta.get('/Author')}», skal være «Silfer AS»")
    if not tittel:
        feil.append("/Title mangler")
    storrelse = Path(os_sti(sti)).stat().st_size
    print(f"  {n} side(r), tittel «{tittel}», {storrelse // 1024} KB")
    return feil


def main(argv=None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    filer = argv if argv is not None else sys.argv[1:]
    if not filer:
        print(__doc__)
        return 1
    kode = 0
    for f in filer:
        sti = Path(f)
        print(f"{sti.name}")
        try:
            if sti.suffix.lower() == ".xlsx":
                feil = sjekk_xlsx(sti)
            elif sti.suffix.lower() == ".pdf":
                feil = sjekk_pdf(sti)
            else:
                feil = [f"ukjent filtype {sti.suffix} (bare .xlsx og .pdf)"]
        except FileNotFoundError:
            feil = ["finnes ikke"]
        except Exception as e:  # noqa: BLE001
            feil = [f"kunne ikke leses: {e}"]
        for x in feil:
            print(f"  FEIL {x}")
        if feil:
            kode = 1
        else:
            print("  ✓ i orden")
    return kode


if __name__ == "__main__":
    sys.exit(main())
