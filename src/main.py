"""Orchestrateur : charge la config, verifie chaque produit, notifie, persiste l'etat.

Usage :
    python -m src.main --once                 # un seul passage (mode CI / cron)
    python -m src.main --loop --interval 900  # boucle locale (test), pause 900s
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
import time

import yaml

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # noqa: BLE001 - dotenv optionnel
    pass

from .adapters import get_adapter
from . import notifier, state as state_mod

log = logging.getLogger("scraper")


def _setup_logging() -> None:
    level = os.environ.get("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s %(levelname)-7s %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )


def load_config(path: str = "config.yaml") -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def run_once(config: dict) -> int:
    """Effectue un passage sur tous les produits actifs. Retourne le nb d'alertes envoyees."""
    settings = config.get("settings", {})
    products = [p for p in config.get("products", []) if p.get("enabled", True)]
    if not products:
        log.warning("Aucun produit actif dans config.yaml")
        return 0

    state = state_mod.load_state()
    delay = int(settings.get("delay_between_products", 5))
    alerts = 0

    for i, product in enumerate(products):
        name = product.get("name", product.get("url", "?"))
        store = product.get("store", "generic")
        url = product["url"]
        log.info("Verification [%s] %s", store, name)

        adapter = get_adapter(store)(settings)
        result = adapter.run(product)

        if result.error:
            log.warning("  -> erreur/indetermine : %s (pas d'alerte)", result.detail)
        elif result.available:
            log.info("  -> DISPONIBLE : %s", result.detail)
            if state_mod.should_notify(state, url, True):
                try:
                    notifier.send_stock_alert(name, url, result.detail, result.stores)
                    alerts += 1
                    state_mod.update(state, url, True, notified=True, detail=result.detail)
                    log.info("  -> mail d'alerte envoye")
                except Exception as exc:  # noqa: BLE001
                    log.error("  -> echec envoi mail : %s", exc)
                    state_mod.update(state, url, True, notified=False, detail=result.detail)
            else:
                log.info("  -> deja signale precedemment, pas de nouveau mail")
                state_mod.update(state, url, True, notified=False, detail=result.detail)
        else:
            log.info("  -> indisponible : %s", result.detail)
            state_mod.update(state, url, False, notified=False, detail=result.detail)

        if i < len(products) - 1:
            time.sleep(delay)

    state_mod.save_state(state)
    log.info("Passage termine. Alertes envoyees : %d", alerts)
    return alerts


def _maybe_test_email() -> None:
    if os.environ.get("SEND_TEST_EMAIL", "0") == "1":
        log.info("SEND_TEST_EMAIL=1 -> envoi d'un mail de test")
        notifier.send_email(
            "[TEST] Scraper Clim Portable",
            "Ceci est un mail de test : la configuration SMTP fonctionne.",
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scraper de stock clim portable")
    parser.add_argument("--once", action="store_true", help="un seul passage (defaut)")
    parser.add_argument("--loop", action="store_true", help="boucle infinie (test local)")
    parser.add_argument("--interval", type=int, default=900, help="pause entre passages (s)")
    parser.add_argument("--config", default="config.yaml", help="chemin du config.yaml")
    args = parser.parse_args(argv)

    _setup_logging()
    config = load_config(args.config)

    try:
        _maybe_test_email()
    except Exception as exc:  # noqa: BLE001
        log.error("Echec mail de test : %s", exc)

    if args.loop:
        log.info("Mode boucle : pause de %ds entre passages (Ctrl+C pour arreter)", args.interval)
        while True:
            try:
                run_once(config)
            except Exception as exc:  # noqa: BLE001
                log.error("Erreur durant le passage : %s", exc)
            time.sleep(args.interval)
    else:
        run_once(config)
    return 0


if __name__ == "__main__":
    sys.exit(main())
