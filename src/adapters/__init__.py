"""Registre des adaptateurs par enseigne."""
from .base import AvailabilityResult, Adapter
from .leroymerlin import LeroyMerlinAdapter
from .darty import DartyAdapter
from .boulanger import BoulangerAdapter
from .generic import GenericAdapter

# Mappe la cle `store` du config.yaml vers la classe d'adaptateur.
REGISTRY = {
    "leroymerlin": LeroyMerlinAdapter,
    "darty": DartyAdapter,
    "boulanger": BoulangerAdapter,
    "generic": GenericAdapter,
}


def get_adapter(store: str):
    """Retourne la classe d'adaptateur pour une enseigne, ou GenericAdapter par defaut."""
    return REGISTRY.get((store or "").lower(), GenericAdapter)


__all__ = [
    "AvailabilityResult",
    "Adapter",
    "REGISTRY",
    "get_adapter",
]
