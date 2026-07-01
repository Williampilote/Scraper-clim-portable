"""Adaptateur generique : detection simple de la dispo en ligne via texte de page."""
from __future__ import annotations

import logging
from typing import Any

from playwright.sync_api import Page

from .base import Adapter, AvailabilityResult

log = logging.getLogger(__name__)

UNAVAILABLE_TEXTS = (
    "indisponible",
    "rupture",
    "epuise",
    "épuisé",
    "non disponible",
    "bientot disponible",
    "bientôt disponible",
    "produit non disponible",
)

AVAILABLE_TEXTS = (
    "ajouter au panier",
    "en stock",
    "disponible",
    "ajouter au panier",
    "retrait en magasin",
    "livraison",
)


class GenericAdapter(Adapter):
    store_key = "generic"

    def check(self, page: Page, product: dict[str, Any]) -> AvailabilityResult:
        response = self.goto(page, product["url"])
        self.accept_cookies(page)
        page.wait_for_timeout(3000)

        if self.is_blocked(page, response):
            return AvailabilityResult.failed("bloque par anti-bot")

        try:
            text = page.locator("body").inner_text(timeout=5000).lower()
        except Exception:  # noqa: BLE001
            text = body

        has_unavail = any(t in text for t in UNAVAILABLE_TEXTS)
        has_avail = any(t in text for t in AVAILABLE_TEXTS)

        if has_avail and not has_unavail:
            return AvailabilityResult(available=True, detail="dispo (texte page)")
        if has_unavail:
            return AvailabilityResult(available=False, detail="indisponible (texte page)")
        return AvailabilityResult(available=False, detail="indetermine")
