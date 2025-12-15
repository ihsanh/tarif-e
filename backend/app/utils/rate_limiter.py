"""
Rate Limiter Utility - Subscription-based rate limiting
backend/app/utils/rate_limiter.py
"""
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.subscription import Subscription
from app.models.usage_log import UsageLog
from app.config import settings
import logging

logger = logging.getLogger(__name__)


def check_recipe_limit(user: User, db: Session) -> dict:
    """
    Kullanıcının tarif önerisi alıp alamayacağını kontrol eder

    Returns:
        dict: {
            "allowed": bool,
            "tier": str,
            "used_today": int,
            "limit": int,
            "remaining": int
        }
    """
    try:
        # Kullanıcının aboneliğini getir
        subscription = db.query(Subscription).filter(
            Subscription.user_id == user.id
        ).first()

        # Pro kullanıcılar: sınırsız
        if subscription and subscription.tier == "pro" and subscription.is_active():
            logger.debug(f"[RATE_LIMITER] User {user.id} has active PRO subscription - unlimited access")
            return {
                "allowed": True,
                "tier": "pro",
                "used_today": 0,
                "limit": -1,  # -1 = sınırsız
                "remaining": -1
            }

        # Standard kullanıcılar: günlük limiti kontrol et
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        used_today = db.query(UsageLog).filter(
            UsageLog.user_id == user.id,
            UsageLog.action_type == "recipe_suggestion",
            UsageLog.created_at >= today_start
        ).count()

        limit = settings.STANDARD_DAILY_RECIPE_LIMIT
        remaining = max(0, limit - used_today)
        allowed = used_today < limit

        logger.debug(f"[RATE_LIMITER] User {user.id} (STANDARD): {used_today}/{limit} recipes used today")

        return {
            "allowed": allowed,
            "tier": "standard",
            "used_today": used_today,
            "limit": limit,
            "remaining": remaining
        }

    except Exception as e:
        logger.error(f"[RATE_LIMITER] Error checking recipe limit for user {user.id}: {e}")
        # Hata durumunda güvenli tarafta kal - izin verme
        return {
            "allowed": False,
            "tier": "unknown",
            "used_today": 0,
            "limit": 0,
            "remaining": 0,
            "error": str(e)
        }


def log_recipe_usage(user: User, db: Session) -> bool:
    """
    Tarif önerisi kullanımını logla

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        usage_log = UsageLog(
            user_id=user.id,
            action_type="recipe_suggestion"
        )
        db.add(usage_log)
        db.commit()
        logger.debug(f"[RATE_LIMITER] Logged recipe usage for user {user.id}")
        return True
    except Exception as e:
        logger.error(f"[RATE_LIMITER] Error logging recipe usage for user {user.id}: {e}")
        db.rollback()
        return False


def get_usage_stats(user: User, db: Session) -> dict:
    """
    Kullanıcının bugünkü kullanım istatistiklerini getir

    Returns:
        dict: {
            "tier": str,
            "used_today": int,
            "limit": int,
            "remaining": int,
            "percentage_used": float
        }
    """
    limit_info = check_recipe_limit(user, db)

    stats = {
        "tier": limit_info["tier"],
        "used_today": limit_info["used_today"],
        "limit": limit_info["limit"],
        "remaining": limit_info["remaining"]
    }

    # Pro kullanıcılar için percentage_used: 0
    if limit_info["tier"] == "pro":
        stats["percentage_used"] = 0.0
    else:
        # Standard kullanıcılar için yüzde hesapla
        if limit_info["limit"] > 0:
            stats["percentage_used"] = (limit_info["used_today"] / limit_info["limit"]) * 100
        else:
            stats["percentage_used"] = 100.0

    return stats
