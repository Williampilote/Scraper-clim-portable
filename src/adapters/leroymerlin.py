"""Adaptateur Leroy Merlin : detection du stock retrait magasin (toute la France)."""
from __future__ import annotations

import logging
from typing import Any

from playwright.sync_api import Page

from .base import Adapter, AvailabilityResult

log = logging.getLogger(__name__)

# Mots-cles d'URL des API internes LM liees a la disponibilite / au stock.
_AVAILABILITY_URL_HINTS = (
    "availability",
    "disponibilit",
    "stock",
    "store",
    "magasin",
    "pickup",
    "fulfilment",
    "fulfillment",
    "click-and-collect",
)

# Libelles DOM indiquant une indisponibilite (fallback).
_UNAVAILABLE_TEXTS = (
    "indisponible",
    "produit indisponible",
    "actuellement indisponible",
    "rupture",
    "bientot de retour",
    "bientôt de retour",
    "non disponible",
    "victime de son succes",
    "victime de son succès",
)

# Libelles DOM indiquant une disponibilite retrait/magasin (fallback).
_AVAILABLE_TEXTS = (
    "retrait en magasin",
    "disponible en magasin",
    "retirer en magasin",
    "disponible pour le retrait",
    "en stock en magasin",
)


def _looks_like_availability_api(url: str) -> bool:
    low = url.lower()
    return any(h in low for h in _AVAILABILITY_URL_HINTS)


def _scan_json_for_stock(node: Any) -> tuple[bool, list[str]]:
    """Parcours recursif d'un JSON pour reperer un stock magasin > 0.

    Heuristique tolerante : on cherche des cles de quantite/stock positives, ou des
    statuts textuels "available/in_stock", en collectant un eventuel nom de magasin.
    Retourne (stock_trouve, noms_de_magasins).
    """
    found = False
    stores: list[str] = []

    def _store_name(d: dict) -> str | None:
        for key in ("storeName", "name", "label", "storeLabel", "pointOfSaleName"):
            val = d.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip()
        return None

    def _walk(obj: Any, ctx_name: str | None = None) -> None:
        nonlocal found
        if isinstance(obj, dict):
            local_name = _store_name(obj) or ctx_name
            for key, val in obj.items():
                klow = str(key).lower()
                # Quantites numeriques positives.
                if klow in ("quantity", "stock", "stocklevel", "availablequantity", "qty"):
                    if isinstance(val, (int, float)) and val > 0:
                        found = True
                        if local_name:
                            stores.append(local_name)
                # Statuts textuels / booleens.
                if klow in ("available", "isavailable", "instock", "in_stock", "pickupavailable"):
                    if val is True:
                        found = True
                        if local_name:
                            stores.append(local_name)
                if klow in ("availability", "status", "availabilitystatus", "stockstatus"):
                    if isinstance(val, str) and any(
                        s in val.lower() for s in ("available", "in_stock", "instock", "disponible")
                    ) and "unavailable" not in val.lower() and "indisponible" not in val.lower():
                        found = True
                        if local_name:
                            stores.append(local_name)
                _walk(val, local_name)
        elif isinstance(obj, list):
            for item in obj:
                _walk(item, ctx_name)

    _walk(node)
    # Dedoublonne en gardant l'ordre.
    seen: set[str] = set()
    uniq = [s for s in stores if not (s in seen or seen.add(s))]
    return found, uniq


class LeroyMerlinAdapter(Adapter):
    store_key = "leroymerlin"

    def check(self, page: Page, product: dict[str, Any]) -> AvailabilityResult:
        url = product["url"]
        # 1) Capture les reponses JSON d'API de dispo AVANT de naviguer.
        captured = self.capture_json_responses(page, _looks_like_availability_api)

        response = self.goto(page, url)
        self.accept_cookies(page)

        # Detection d'un VRAI mur anti-bot (403/captcha) -> erreur, pas rupture.
        if self.is_blocked(page, response):
            return AvailabilityResult.failed("bloque par anti-bot (DataDome/captcha)")

        # Laisse le temps aux appels XHR de disponibilite de partir.
        page.wait_for_timeout(4000)
        # Tente de declencher le widget "retrait en magasin" s'il existe.
        self._trigger_store_widget(page)
        page.wait_for_timeout(3000)

        # 2) Analyse les reponses API captees.
        for entry in captured:
            ok, stores = _scan_json_for_stock(entry["json"])
            if ok:
                detail = "stock magasin detecte via API"
                if stores:
                    detail += f" ({', '.join(stores[:5])})"
                return AvailabilityResult(available=True, detail=detail, stores=stores)

        # 3) Fallback DOM : analyse du texte visible.
        visible = self._visible_text(page)
        low = visible.lower()
        if any(t in low for t in _AVAILABLE_TEXTS) and not any(
            t in low for t in _UNAVAILABLE_TEXTS
        ):
            return AvailabilityResult(
                available=True, detail="dispo detectee via texte de la page"
            )
        if any(t in low for t in _UNAVAILABLE_TEXTS):
            return AvailabilityResult(available=False, detail="produit indisponible (texte page)")

        # Indetermine : pas de signal clair -> on considere indisponible sans erreur.
        return AvailabilityResult(
            available=False, detail="aucun signal de dispo clair (indetermine)"
        )

    def _trigger_store_widget(self, page: Page) -> None:
        """Tente d'ouvrir le bloc de disponibilite magasin pour declencher l'API."""
        selectors = [
            "button:has-text('Retrait en magasin')",
            "button:has-text('Verifier la disponibilite')",
            "button:has-text('Vérifier la disponibilité')",
            "button:has-text('disponibilite en magasin')",
            "text=Retrait en magasin",
        ]
        for sel in selectors:
            try:
                loc = page.locator(sel).first
                if loc.is_visible(timeout=1500):
                    loc.click(timeout=1500)
                    page.wait_for_timeout(1500)
                    return
            except Exception:  # noqa: BLE001
                continue

    def _visible_text(self, page: Page) -> str:
        try:
            return page.locator("body").inner_text(timeout=5000)
        except Exception:  # noqa: BLE001
            return page.content() or ""
