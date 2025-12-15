"""
Subscription Routes - Subscription management endpoints
backend/app/routes/subscription.py
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import logging

from app.database import get_db
from app.models.user import User
from app.models.subscription import Subscription
from app.utils.auth import get_current_user
from app.utils.rate_limiter import get_usage_stats
from app.config import settings
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/subscription", tags=["subscription"])


# ============================================
# SCHEMAS
# ============================================

class SubscriptionResponse(BaseModel):
    """Abonelik bilgisi response"""
    tier: str
    billing_cycle: str
    status: str
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    auto_renew: bool

    class Config:
        from_attributes = True


class UsageStatsResponse(BaseModel):
    """Kullanım istatistikleri response"""
    tier: str
    used_today: int
    limit: int
    remaining: int
    percentage_used: float


class SubscriptionUpdateRequest(BaseModel):
    """Abonelik güncelleme request"""
    tier: Optional[str] = None
    billing_cycle: Optional[str] = None
    auto_renew: Optional[bool] = None


# ============================================
# ENDPOINTS
# ============================================

@router.get("/status", response_model=SubscriptionResponse)
async def get_subscription_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Kullanıcının mevcut abonelik durumunu getir"""
    try:
        subscription = db.query(Subscription).filter(
            Subscription.user_id == current_user.id
        ).first()

        if not subscription:
            # Abonelik yoksa varsayılan olarak oluştur
            subscription = Subscription(
                user_id=current_user.id,
                tier=settings.DEFAULT_SUBSCRIPTION_TIER,
                billing_cycle="monthly",
                status="active",
                auto_renew=True
            )
            subscription.calculate_end_date()
            db.add(subscription)
            db.commit()
            db.refresh(subscription)
            logger.info(f"[SUBSCRIPTION] Created default subscription for user {current_user.id}")

        return SubscriptionResponse(
            tier=subscription.tier,
            billing_cycle=subscription.billing_cycle,
            status=subscription.status,
            start_date=subscription.start_date,
            end_date=subscription.end_date,
            auto_renew=subscription.auto_renew
        )

    except Exception as e:
        logger.error(f"[SUBSCRIPTION] Error getting subscription status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Abonelik durumu alınırken bir hata oluştu"
        )


@router.get("/usage", response_model=UsageStatsResponse)
async def get_usage_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Kullanıcının bugünkü kullanım istatistiklerini getir"""
    try:
        stats = get_usage_stats(current_user, db)

        return UsageStatsResponse(
            tier=stats["tier"],
            used_today=stats["used_today"],
            limit=stats["limit"],
            remaining=stats["remaining"],
            percentage_used=stats["percentage_used"]
        )

    except Exception as e:
        logger.error(f"[SUBSCRIPTION] Error getting usage stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Kullanım istatistikleri alınırken bir hata oluştu"
        )


@router.post("/upgrade")
async def upgrade_to_pro(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Pro pakete yükselt (ileride ödeme entegrasyonu eklenecek)"""
    try:
        subscription = db.query(Subscription).filter(
            Subscription.user_id == current_user.id
        ).first()

        if not subscription:
            # Yeni abonelik oluştur
            subscription = Subscription(
                user_id=current_user.id,
                tier="pro",
                billing_cycle="monthly",
                status="active",
                auto_renew=True
            )
            subscription.calculate_end_date()
            db.add(subscription)
        else:
            # Mevcut aboneliği güncelle
            subscription.tier = "pro"
            subscription.status = "active"
            subscription.start_date = datetime.utcnow()
            subscription.calculate_end_date()

        db.commit()
        db.refresh(subscription)

        logger.info(f"[SUBSCRIPTION] User {current_user.id} upgraded to PRO")

        return {
            "success": True,
            "message": "Pro pakete başarıyla yükseltildiniz",
            "subscription": {
                "tier": subscription.tier,
                "billing_cycle": subscription.billing_cycle,
                "end_date": subscription.end_date
            }
        }

    except Exception as e:
        logger.error(f"[SUBSCRIPTION] Error upgrading to PRO: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Pro pakete yükseltme sırasında bir hata oluştu"
        )


@router.put("/update")
async def update_subscription(
    request: SubscriptionUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Abonelik ayarlarını güncelle (billing_cycle, auto_renew)"""
    try:
        subscription = db.query(Subscription).filter(
            Subscription.user_id == current_user.id
        ).first()

        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Abonelik bulunamadı"
            )

        # Sadece izin verilen alanları güncelle
        if request.billing_cycle and request.billing_cycle in ["monthly", "yearly"]:
            subscription.billing_cycle = request.billing_cycle
            subscription.calculate_end_date()

        if request.auto_renew is not None:
            subscription.auto_renew = request.auto_renew

        # Tier değiştirme sadece upgrade endpoint'i üzerinden
        # request.tier parametresi varsa ignore et

        db.commit()
        db.refresh(subscription)

        logger.info(f"[SUBSCRIPTION] User {current_user.id} updated subscription settings")

        return {
            "success": True,
            "message": "Abonelik ayarları güncellendi",
            "subscription": {
                "tier": subscription.tier,
                "billing_cycle": subscription.billing_cycle,
                "auto_renew": subscription.auto_renew,
                "end_date": subscription.end_date
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[SUBSCRIPTION] Error updating subscription: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Abonelik güncellenirken bir hata oluştu"
        )


@router.get("/pricing")
async def get_pricing():
    """Abonelik fiyatlarını getir"""
    return {
        "standard": {
            "tier": "standard",
            "price": 0,
            "currency": "TL",
            "features": [
                f"Günde {settings.STANDARD_DAILY_RECIPE_LIMIT} tarif önerisi",
                "Temel özellikler"
            ]
        },
        "pro": {
            "tier": "pro",
            "monthly_price": settings.PRO_MONTHLY_PRICE,
            "yearly_price": settings.PRO_YEARLY_PRICE,
            "currency": "TL",
            "features": [
                "Sınırsız tarif önerisi",
                "Reklamsız deneyim (yakında)",
                "Öncelikli destek (yakında)"
            ]
        }
    }
