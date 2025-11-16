"""
API Routes
"""
from .malzeme import router as malzeme_router
from .tarif import router as tarif_router
from .alisveris import router as alisveris_router
from .health import router as health_router
from .auth import router as auth_router
from .alisveris_extended import router as alısveris_extended_router
from .paylasim import router as paslasim_router

__all__ = [
    "malzeme_router",
    "tarif_router",
    "alisveris_router",
    "health_router",
    "auth_router",
    "alısveris_extended_router",
    "paslasim_router"
]
