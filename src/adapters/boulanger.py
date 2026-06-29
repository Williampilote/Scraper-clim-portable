"""Adaptateur Boulanger (bonus) : dispo en ligne. Herite de la logique generique."""
from __future__ import annotations

from .generic import GenericAdapter


class BoulangerAdapter(GenericAdapter):
    store_key = "boulanger"
