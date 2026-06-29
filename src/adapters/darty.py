"""Adaptateur Darty (bonus) : dispo en ligne. Herite de la logique generique."""
from __future__ import annotations

from .generic import GenericAdapter


class DartyAdapter(GenericAdapter):
    store_key = "darty"
