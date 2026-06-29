"""Base commune aux adaptateurs : pilotage Playwright + helpers anti-bot."""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Callable

from playwright.sync_api import Page, Response, sync_playwright

log = logging.getLogger(__name__)

# User-agent desktop realiste (Chrome recent sous Windows).
DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

# Libelles des boutons de consentement cookies rencontres (Didomi, etc.).
COOKIE_BUTTON_SELECTORS = [
    "#didomi-notice-agree-button",
    "button#onetrust-accept-btn-handler",
    "button:has-text('Tout accepter')",
    "button:has-text('Tout accepter et fermer')",
    'button:has-text("J\'accepte")',
    "button:has-text('Accepter')",
]


@dataclass
class AvailabilityResult:
    """Resultat d'une verification de disponibilite pour un produit."""

    available: bool
    detail: str = ""
    # Liste de magasins disponibles (retrait), si applicable.
    stores: list[str] = field(default_factory=list)
    # True si la verification a echoue (anti-bot, timeout...) -> on n'alerte pas.
    error: bool = False

    @classmethod
    def failed(cls, reason: str) -> "AvailabilityResult":
        return cls(available=False, detail=reason, error=True)


class Adapter:
    """Adaptateur de base : a sous-classer par enseigne.

    Le contrat : implementer `check(page, product) -> AvailabilityResult`.
    La gestion du navigateur, des cookies et de l'interception reseau est fournie ici.
    """

    store_key = "generic"

    def __init__(self, settings: dict[str, Any] | None = None):
        self.settings = settings or {}
        self.page_timeout_ms = int(self.settings.get("page_timeout_ms", 45000))
        self.headless = bool(self.settings.get("headless", True))

    # ---- API publique ---------------------------------------------------

    def run(self, product: dict[str, Any]) -> AvailabilityResult:
        """Lance un navigateur, ouvre la page produit, delegue a check()."""
        try:
            with sync_playwright() as p:
                browser = self._launch(p)
                context = browser.new_context(
                    locale="fr-FR",
                    user_agent=DEFAULT_UA,
                    viewport={"width": 1366, "height": 900},
                    timezone_id="Europe/Paris",
                )
                # Anti-detection basique : masque navigator.webdriver.
                context.add_init_script(
                    "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
                )
                page = context.new_page()
                page.set_default_timeout(self.page_timeout_ms)
                try:
                    result = self.check(page, product)
                finally:
                    context.close()
                    browser.close()
                return result
        except Exception as exc:  # noqa: BLE001 - on veut ne jamais crasher la boucle
            log.warning("Echec verification (%s) : %s", product.get("url"), exc)
            return AvailabilityResult.failed(f"exception: {exc}")

    # ---- A implementer par les sous-classes -----------------------------

    def check(self, page: Page, product: dict[str, Any]) -> AvailabilityResult:
        raise NotImplementedError

    # ---- Helpers --------------------------------------------------------

    def _launch(self, p):
        """Lance Chromium, en utilisant le binaire preinstalle si present."""
        launch_kwargs: dict[str, Any] = {
            "headless": self.headless,
            "args": ["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        }
        exec_path = os.environ.get("PLAYWRIGHT_CHROMIUM_PATH")
        if exec_path and os.path.exists(exec_path):
            launch_kwargs["executable_path"] = exec_path
        return p.chromium.launch(**launch_kwargs)

    def goto(self, page: Page, url: str) -> None:
        page.goto(url, wait_until="domcontentloaded", timeout=self.page_timeout_ms)

    def accept_cookies(self, page: Page) -> None:
        """Tente de cliquer un bouton de consentement cookies (best-effort)."""
        for selector in COOKIE_BUTTON_SELECTORS:
            try:
                btn = page.locator(selector).first
                if btn.is_visible(timeout=2500):
                    btn.click(timeout=2500)
                    log.debug("Cookies acceptes via %s", selector)
                    page.wait_for_timeout(800)
                    return
            except Exception:  # noqa: BLE001 - selecteur absent = on continue
                continue

    def capture_json_responses(
        self, page: Page, url_predicate: Callable[[str], bool]
    ) -> list[dict[str, Any]]:
        """Enregistre un listener qui capture les reponses JSON correspondant au predicat.

        Retourne une liste vivante remplie au fil du chargement de la page.
        A appeler AVANT goto().
        """
        captured: list[dict[str, Any]] = []

        def _on_response(response: Response) -> None:
            try:
                if not url_predicate(response.url):
                    return
                ctype = response.headers.get("content-type", "")
                if "json" not in ctype:
                    return
                captured.append({"url": response.url, "json": response.json()})
            except Exception:  # noqa: BLE001 - reponse illisible -> ignore
                return

        page.on("response", _on_response)
        return captured
