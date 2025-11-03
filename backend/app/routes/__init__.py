"""
API Routes
"""
from .malzeme import router as malzeme_router
from .tarif import router as tarif_router
from .alisveris import router as alisveris_router
from .health import router as health_router

__all__ = [
    "malzeme_router",
    "tarif_router",
    "alisveris_router",
    "health_router",
]
