"""PDF via Edge/Chrome headless – samme motor og samme løsninger som Silfer-notatene i Tripletex-CLI-et (lagPdf).

- Egen profil (--user-data-dir): ellers overtar en Edge som allerede kjører kallet og avslutter uten å skrive PDF-en.
- Exit-koden ignoreres: Edge kan avslutte med feilkode selv når PDF-en er skrevet – derfor sjekkes filen.
- Edge-starteren kan avslutte før utskriften er ferdig: vent til PDF-en finnes og har stabil størrelse.
- Skriv til en midlertidig fil og kopier: en feilet utskrift skal aldri gi en gammel målfil tilbake.
- Profilmappen kan være låst en stund: slett med nye forsøk, og la den ligge hvis det ikke går.

«Side n av N» stemples etterpå med pypdf (Chromium kan ikke sette egen bunntekst fra kommandolinjen).
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from . import tema
from .filer import os_sti


class NettleserMangler(RuntimeError):
    def __init__(self, html_fil: Path):
        super().__init__(f"Fant verken Edge eller Chrome. PDF ikke laget – åpne {html_fil} i nettleseren og skriv ut til PDF.")
        self.html_fil = html_fil


def _kandidater() -> list[str]:
    lokal = os.environ.get("LOCALAPPDATA", "")
    liste = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.join(lokal, r"Google\Chrome\Application\chrome.exe") if lokal else "",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    ]
    for navn in ("msedge", "microsoft-edge", "google-chrome", "chromium", "chromium-browser", "chrome"):
        funnet = shutil.which(navn)
        if funnet:
            liste.append(funnet)
    return [p for p in liste if p]


def finn_nettleser() -> str | None:
    """SILFER_BROWSER overstyrer; ellers Edge (x86, x64), så Chrome."""
    eget = os.environ.get("SILFER_BROWSER")
    if eget:
        return eget if os.path.exists(eget) else None
    return next((p for p in _kandidater() if os.path.exists(p)), None)


def html_til_pdf(html: str, ut: Path, *, exe: str | None = None, timeout_s: int = 120) -> int:
    """Skriver HTML til PDF med Edge/Chrome headless. Gir antall byte."""
    exe = exe or finn_nettleser()
    if not exe:
        raise FileNotFoundError("Fant verken Edge eller Chrome for PDF-utskrift.")
    ut = Path(ut)
    mappe = Path(tempfile.mkdtemp(prefix="silfer-notat-"))
    tmp_pdf = mappe / "notat.pdf"
    try:
        html_fil = mappe / "notat.html"
        html_fil.write_text(html, encoding="utf-8")
        try:
            subprocess.run(
                [exe, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--no-first-run",
                 "--no-default-browser-check", f"--user-data-dir={mappe / 'profil'}", f"--print-to-pdf={tmp_pdf}",
                 html_fil.resolve().as_uri()],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=timeout_s, check=False)
        except (subprocess.SubprocessError, OSError):
            pass  # sjekkes under
        forrige = -1
        for _ in range(240):
            n = tmp_pdf.stat().st_size if tmp_pdf.exists() else -1
            if n > 0 and n == forrige:
                break
            forrige = n
            time.sleep(0.5)
        if not tmp_pdf.exists() or tmp_pdf.stat().st_size == 0:
            raise RuntimeError(f"PDF ble ikke laget: {ut}")
        shutil.copyfile(tmp_pdf, os_sti(ut))
    finally:
        for _ in range(10):
            try:
                shutil.rmtree(mappe)
                break
            except FileNotFoundError:
                break
            except OSError:
                time.sleep(0.5)
    return os.stat(os_sti(ut)).st_size


# Helvetica-bredder (1/1000 em) for tegnene i «Side n av N».
_BREDDE = {"S": 667, "i": 222, "d": 556, "e": 556, " ": 278, "a": 556, "v": 500, **{str(d): 556 for d in range(10)}}


def stemple_sidetall(pdf: Path, *, tittel: str, forfatter: str = tema.FORFATTER, skrift: float = 7,
                     hoyre_mm: float = 13, bunn_mm: float = 7, stemple: bool = True) -> int:
    """Legger «Side n av N» nederst til høyre på hver side (stemple=True) og setter /Title og /Author. Gir antall sider."""
    from pypdf import PageObject, PdfReader, PdfWriter
    from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

    pdf = Path(pdf)
    leser = PdfReader(os_sti(pdf))
    skriver = PdfWriter(clone_from=leser)
    n = len(skriver.pages)
    mm = 72 / 25.4
    r, g, b = (int(tema.GRA[i:i + 2], 16) / 255 for i in (2, 4, 6))
    for i, side_ in enumerate(skriver.pages if stemple else [], start=1):
        bredde = float(side_.mediabox.width)
        hoyde = float(side_.mediabox.height)
        tekst = f"Side {i} av {n}"
        tb = sum(_BREDDE.get(ch, 556) for ch in tekst) * skrift / 1000
        x = bredde - hoyre_mm * mm - tb
        y = bunn_mm * mm
        lag = PageObject.create_blank_page(width=bredde, height=hoyde)
        font = DictionaryObject({NameObject("/Type"): NameObject("/Font"), NameObject("/Subtype"): NameObject("/Type1"),
                                 NameObject("/BaseFont"): NameObject("/Helvetica"),
                                 NameObject("/Encoding"): NameObject("/WinAnsiEncoding")})
        lag[NameObject("/Resources")] = DictionaryObject({
            NameObject("/Font"): DictionaryObject({NameObject("/FSilfer"): font})})
        strom = DecodedStreamObject()
        strom.set_data(f"q {r:.3f} {g:.3f} {b:.3f} rg BT /FSilfer {skrift:g} Tf {x:.2f} {y:.2f} Td ({tekst}) Tj ET Q".encode("ascii"))
        lag[NameObject("/Contents")] = skriver._add_object(strom)
        side_.merge_page(lag)
    skriver.add_metadata({"/Title": tittel, "/Author": forfatter})
    tmp = pdf.with_name(pdf.name + ".tmp")
    with open(os_sti(tmp), "wb") as f:
        skriver.write(f)
    os.replace(os_sti(tmp), os_sti(pdf))
    return n


def bygg_pdf(spec: dict, ut, *, behold_html: bool = False) -> Path:
    """Validert spec → PDF. Uten nettleser: skriver <ut>.html og kaster NettleserMangler."""
    from .html import render

    ut = Path(ut)
    html = render(spec)
    html_fil = ut.with_suffix(".html")
    exe = finn_nettleser()
    if not exe or behold_html:
        with open(os_sti(html_fil), "w", encoding="utf-8") as f:
            f.write(html)
    if not exe:
        raise NettleserMangler(html_fil)
    html_til_pdf(html, ut, exe=exe)
    try:
        stemple_sidetall(ut, tittel=spec["dokument"]["tittel"], stemple=spec["dokument"].get("sidetall", True))
    except ImportError:
        print("Advarsel: pypdf mangler – sidetall og metadata ikke satt (kjør med --with pypdf).")
    return ut
