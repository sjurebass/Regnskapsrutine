"""Tripletex REST API v2 – klient.

Autentisering følger Tripletex' standard: consumer token + employee token byttes
i et session token, som deretter brukes som HTTP Basic-passord med companyId som
brukernavn. Som regnskapsfører setter man klientens companyId for å jobbe i
klientselskapet med samme employee token.

Endepunkter og feltnavn er hentet fra https://tripletex.no/v2/openapi.json (v2.75).
"""

from __future__ import annotations

import base64
import json
import os
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, timedelta

BASE = os.environ.get("TRIPLETEX_BASE", "https://tripletex.no/v2")
SIDESTORRELSE = 1000
MAKS_FORSOK = 5


class TripletexFeil(RuntimeError):
    """Feil fra API-et som kallekoden bør forholde seg til."""


class Tripletex:
    def __init__(
        self,
        consumer_token: str,
        employee_token: str,
        company_id: str | int = "0",
        base: str = BASE,
    ) -> None:
        if not consumer_token or not employee_token:
            raise TripletexFeil(
                "Mangler TRIPLETEX_CONSUMER_TOKEN og/eller TRIPLETEX_EMPLOYEE_TOKEN. "
                "Se SETUP.md."
            )
        self.base = base.rstrip("/")
        self._consumer_token = consumer_token
        self._employee_token = employee_token
        self.company_id = str(company_id)
        self._session_token: str | None = None
        self._session_utloper: date | None = None
        self._ctx = ssl.create_default_context()
        self.kall_teller = 0

    # -- autentisering ----------------------------------------------------

    def _hent_session_token(self) -> str:
        """Session token varer til expirationDate. Vi ber om 2 dager og
        gjenbruker det gjennom hele kjøringen."""
        utloper = date.today() + timedelta(days=2)
        url = "{}/token/session/:create?{}".format(
            self.base,
            urllib.parse.urlencode(
                {
                    "consumerToken": self._consumer_token,
                    "employeeToken": self._employee_token,
                    "expirationDate": utloper.isoformat(),
                }
            ),
        )
        req = urllib.request.Request(url, method="PUT")
        req.add_header("Accept", "application/json")
        try:
            with urllib.request.urlopen(req, context=self._ctx, timeout=60) as r:
                data = json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            kropp = e.read().decode("utf-8", "replace")[:500]
            raise TripletexFeil(
                f"Fikk ikke session token ({e.code}). Sjekk at consumer- og "
                f"employee token er gyldige og ikke utløpt.\n{kropp}"
            ) from e
        except urllib.error.URLError as e:
            raise TripletexFeil(
                f"Kom ikke til {self.base}: {e.reason}. Ved sertifikatfeil bak "
                f"bedriftsproxy: sjekk at rot-sertifikatet ligger i Windows' "
                f"sertifikatlager."
            ) from e
        token = (data.get("value") or {}).get("token")
        if not token:
            raise TripletexFeil(f"Uventet svar på session token: {data}")
        self._session_utloper = utloper
        return token

    def _auth(self) -> str:
        if self._session_token is None:
            self._session_token = self._hent_session_token()
        par = f"{self.company_id}:{self._session_token}".encode("utf-8")
        return "Basic " + base64.b64encode(par).decode("ascii")

    def bytt_selskap(self, company_id: str | int) -> None:
        """Bytt klientselskap. Session token gjenbrukes – bare basic-auth-
        brukernavnet endres."""
        self.company_id = str(company_id)

    # -- lavnivå ----------------------------------------------------------

    def get(self, sti: str, **params) -> dict:
        params = {k: v for k, v in params.items() if v is not None}
        # ':' og '>' i Tripletex-stier skal ikke prosentkodes
        url = f"{self.base}{sti}"
        if params:
            url += "?" + urllib.parse.urlencode(params, safe=":>*(),")
        siste_feil: Exception | None = None
        for forsok in range(MAKS_FORSOK):
            req = urllib.request.Request(url, method="GET")
            req.add_header("Authorization", self._auth())
            req.add_header("Accept", "application/json")
            try:
                self.kall_teller += 1
                with urllib.request.urlopen(req, context=self._ctx, timeout=120) as r:
                    return json.loads(r.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                kropp = e.read().decode("utf-8", "replace")[:400]
                if e.code in (429, 500, 502, 503, 504):
                    siste_feil = TripletexFeil(f"{e.code} på {sti}: {kropp}")
                    time.sleep(2 ** forsok)
                    continue
                if e.code == 401:
                    # session token kan ha utløpt midt i en lang kjøring
                    self._session_token = None
                    siste_feil = TripletexFeil(f"401 på {sti}: {kropp}")
                    if forsok == 0:
                        continue
                raise TripletexFeil(f"{e.code} på {sti}: {kropp}") from e
            except urllib.error.URLError as e:
                siste_feil = TripletexFeil(f"Nettverksfeil på {sti}: {e.reason}")
                time.sleep(2 ** forsok)
        raise siste_feil or TripletexFeil(f"Ga opp på {sti}")

    def liste(self, sti: str, **params) -> list[dict]:
        """Henter alle sider av et listeendepunkt."""
        ut: list[dict] = []
        start = 0
        while True:
            svar = self.get(sti, **params, **{"from": start, "count": SIDESTORRELSE})
            verdier = svar.get("values")
            if verdier is None:
                verdi = svar.get("value")
                return [verdi] if isinstance(verdi, dict) else []
            ut.extend(verdier)
            totalt = svar.get("fullResultSize")
            start += len(verdier)
            if not verdier or totalt is None or start >= totalt:
                return ut

    def verdi(self, sti: str, **params):
        """Henter et enkeltobjekt (ResponseWrapper)."""
        return self.get(sti, **params).get("value")


def fra_miljo(company_id: str | int = "0") -> Tripletex:
    return Tripletex(
        os.environ.get("TRIPLETEX_CONSUMER_TOKEN", ""),
        os.environ.get("TRIPLETEX_EMPLOYEE_TOKEN", ""),
        company_id,
    )
