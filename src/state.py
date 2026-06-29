"""Persistance de l'etat de disponibilite entre les runs (anti-spam mail)."""
from __future__ import annotations

import json
import logging
import os
from typing import Any

log = logging.getLogger(__name__)

STATE_PATH = os.environ.get("STATE_PATH", "state.json")


def load_state(path: str = STATE_PATH) -> dict[str, Any]:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception as exc:  # noqa: BLE001
        log.warning("Etat illisible (%s), on repart de zero : %s", path, exc)
        return {}


def save_state(state: dict[str, Any], path: str = STATE_PATH) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(state, fh, ensure_ascii=False, indent=2, sort_keys=True)


def should_notify(state: dict[str, Any], url: str, now_available: bool) -> bool:
    """Retourne True uniquement lors de la transition indisponible -> disponible."""
    prev = state.get(url, {})
    was_available = bool(prev.get("available", False))
    return now_available and not was_available


def update(state: dict[str, Any], url: str, available: bool, notified: bool, detail: str) -> None:
    entry = state.setdefault(url, {})
    entry["available"] = available
    entry["detail"] = detail
    if notified:
        entry["last_notified"] = True
    state[url] = entry
