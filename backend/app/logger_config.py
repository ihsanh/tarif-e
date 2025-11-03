# app/logger_config.py

import logging
import sys
from app.config import settings


def configure_logging():
    """
    Uygulama genelindeki tüm loglama seviyesini ve formatını ayarlar.
    """

    # settings.LOG_LEVEL'i (örn. "DEBUG", "INFO") config.py dosyanızdan alın
    log_level = settings.LOG_LEVEL.upper() if settings.DEBUG else "INFO"

    logging.basicConfig(
        level=log_level,
        # Formatı ayarlayın: %(name)s logger ismini (örn: app.routes.malzeme) gösterir
        format='%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        stream=sys.stdout
    )

    # FastAPI/Uvicorn loglarını daha sessiz yapmak için seviyeyi yükseltin
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)

    # SQLAlchemy'nin arka plandaki sorgu loglarını kapatın (gürültüyü azaltmak için)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    # Uygulama başladığında konfigürasyonun başarılı olduğunu loglayın
    logging.info(f"Loglama seviyesi '{log_level}' olarak ayarlandı.")