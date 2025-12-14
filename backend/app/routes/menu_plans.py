"""
Menu Plans Routes
Haftalık menü planlama API endpoint'leri
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List
from datetime import date, timedelta

from app.database import get_db
from app.models.menu_plan import WeeklyMenuPlan, MenuItem, MenuShoppingListItem
from app.models.user import User
from app.schemas.menu_plan import (
    WeeklyMenuPlanCreate,
    WeeklyMenuPlanUpdate,
    WeeklyMenuPlanResponse,
    WeeklyMenuPlanSummary,
    MenuItemCreate,
    MenuItemUpdate,
    MenuItemResponse,
)
from app.dependencies import get_current_user


router = APIRouter(prefix="/api/menu-plans", tags=["Menu Planning"])


# ============================================================
# WEEKLY MENU PLANS - CRUD
# ============================================================

@router.get("", response_model=List[WeeklyMenuPlanSummary])
async def get_menu_plans(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Kullanıcının tüm menü planlarını listele
    """
    menus = db.query(WeeklyMenuPlan)\
        .filter(WeeklyMenuPlan.user_id == current_user.id)\
        .order_by(WeeklyMenuPlan.week_start_date.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()
    
    # Summary bilgileri ekle
    result = []
    for menu in menus:
        result.append(WeeklyMenuPlanSummary(
            id=menu.id,
            name=menu.name,
            week_start_date=menu.week_start_date,
            week_end_date=menu.week_end_date,
            is_active=menu.is_active,
            is_ai_generated=menu.is_ai_generated,
            total_recipes=len(menu.menu_items),
            total_shopping_items=len(menu.shopping_list_items),
            created_at=menu.created_at
        ))
    
    return result


@router.post("", response_model=WeeklyMenuPlanResponse, status_code=status.HTTP_201_CREATED)
async def create_menu_plan(
    menu_data: WeeklyMenuPlanCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Yeni haftalık menü planı oluştur
    """
    # Tarih kontrolü
    if menu_data.week_end_date <= menu_data.week_start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bitiş tarihi başlangıç tarihinden sonra olmalı"
        )
    
    # Hafta kontrolü (7 gün)
    days_diff = (menu_data.week_end_date - menu_data.week_start_date).days
    if days_diff != 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Menü planı tam 7 gün olmalı (Pazartesi-Pazar)"
        )
    
    # Aktif menü varsa pasif yap
    if menu_data.is_active:
        db.query(WeeklyMenuPlan)\
            .filter(WeeklyMenuPlan.user_id == current_user.id)\
            .filter(WeeklyMenuPlan.is_active == True)\
            .update({"is_active": False})
    
    # Yeni menü oluştur
    new_menu = WeeklyMenuPlan(
        user_id=current_user.id,
        name=menu_data.name,
        description=menu_data.description,
        week_start_date=menu_data.week_start_date,
        week_end_date=menu_data.week_end_date,
        is_active=menu_data.is_active
    )
    
    db.add(new_menu)
    db.commit()
    db.refresh(new_menu)
    
    return new_menu


@router.get("/active", response_model=WeeklyMenuPlanResponse)
async def get_active_menu(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Aktif menü planını getir
    """
    menu = db.query(WeeklyMenuPlan)\
        .filter(WeeklyMenuPlan.user_id == current_user.id)\
        .filter(WeeklyMenuPlan.is_active == True)\
        .options(
            joinedload(WeeklyMenuPlan.menu_items),
            joinedload(WeeklyMenuPlan.shopping_list_items)
        )\
        .first()
    
    if not menu:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aktif menü bulunamadı"
        )
    
    return menu


@router.get("/{menu_id}", response_model=WeeklyMenuPlanResponse)
async def get_menu_plan(
    menu_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Belirli bir menü planının detaylarını getir
    """
    menu = db.query(WeeklyMenuPlan)\
        .filter(WeeklyMenuPlan.id == menu_id)\
        .filter(WeeklyMenuPlan.user_id == current_user.id)\
        .options(
            joinedload(WeeklyMenuPlan.menu_items),
            joinedload(WeeklyMenuPlan.shopping_list_items)
        )\
        .first()
    
    if not menu:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menü bulunamadı"
        )
    
    return menu


@router.put("/{menu_id}", response_model=WeeklyMenuPlanResponse)
async def update_menu_plan(
    menu_id: int,
    menu_data: WeeklyMenuPlanUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Menü planını güncelle
    """
    menu = db.query(WeeklyMenuPlan)\
        .filter(WeeklyMenuPlan.id == menu_id)\
        .filter(WeeklyMenuPlan.user_id == current_user.id)\
        .first()
    
    if not menu:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menü bulunamadı"
        )
    
    # Güncellemeleri uygula
    update_data = menu_data.dict(exclude_unset=True)
    
    # Aktif yapılıyorsa diğerlerini pasif yap
    if update_data.get("is_active") == True:
        db.query(WeeklyMenuPlan)\
            .filter(WeeklyMenuPlan.user_id == current_user.id)\
            .filter(WeeklyMenuPlan.id != menu_id)\
            .update({"is_active": False})
    
    for field, value in update_data.items():
        setattr(menu, field, value)
    
    db.commit()
    db.refresh(menu)
    
    return menu


@router.delete("/{menu_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_menu_plan(
    menu_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Menü planını sil
    """
    menu = db.query(WeeklyMenuPlan)\
        .filter(WeeklyMenuPlan.id == menu_id)\
        .filter(WeeklyMenuPlan.user_id == current_user.id)\
        .first()
    
    if not menu:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menü bulunamadı"
        )
    
    db.delete(menu)
    db.commit()
    
    return None


# ============================================================
# MENU ITEMS - Öğün Yönetimi
# ============================================================

@router.post("/{menu_id}/items", response_model=MenuItemResponse, status_code=status.HTTP_201_CREATED)
async def add_menu_item(
    menu_id: int,
    item_data: MenuItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Menüye yeni öğün ekle
    """
    # Menü kontrolü
    menu = db.query(WeeklyMenuPlan)\
        .filter(WeeklyMenuPlan.id == menu_id)\
        .filter(WeeklyMenuPlan.user_id == current_user.id)\
        .first()
    
    if not menu:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menü bulunamadı"
        )
    
    # Tarif kontrolü (eğer tarif_id verilmişse)
    if item_data.tarif_id:
        from app.models.favori_tarif import FavoriTarif
        tarif = db.query(FavoriTarif)\
            .filter(FavoriTarif.id == item_data.tarif_id)\
            .filter(FavoriTarif.user_id == current_user.id)\
            .first()
        
        if not tarif:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tarif bulunamadı"
            )
    
    # Yeni öğün oluştur
    new_item = MenuItem(
        menu_plan_id=menu_id,
        tarif_id=item_data.tarif_id,
        day_of_week=item_data.day_of_week,
        meal_type=item_data.meal_type,
        portions=item_data.portions,
        notes=item_data.notes
    )
    
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    
    return new_item


@router.put("/items/{item_id}", response_model=MenuItemResponse)
async def update_menu_item(
    item_id: int,
    item_data: MenuItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Menü öğesini güncelle
    """
    item = db.query(MenuItem)\
        .join(WeeklyMenuPlan)\
        .filter(MenuItem.id == item_id)\
        .filter(WeeklyMenuPlan.user_id == current_user.id)\
        .first()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Öğün bulunamadı"
        )
    
    # Güncellemeleri uygula
    update_data = item_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(item, field, value)
    
    db.commit()
    db.refresh(item)
    
    return item


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_menu_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Menü öğesini sil
    """
    item = db.query(MenuItem)\
        .join(WeeklyMenuPlan)\
        .filter(MenuItem.id == item_id)\
        .filter(WeeklyMenuPlan.user_id == current_user.id)\
        .first()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Öğün bulunamadı"
        )
    
    db.delete(item)
    db.commit()
    
    return None


@router.patch("/items/{item_id}/complete", response_model=MenuItemResponse)
async def toggle_menu_item_completion(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Öğünü tamamlandı olarak işaretle / işareti kaldır
    """
    item = db.query(MenuItem)\
        .join(WeeklyMenuPlan)\
        .filter(MenuItem.id == item_id)\
        .filter(WeeklyMenuPlan.user_id == current_user.id)\
        .first()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Öğün bulunamadı"
        )
    
    from datetime import datetime
    
    # Toggle completion
    item.is_completed = not item.is_completed
    item.completed_at = datetime.utcnow() if item.is_completed else None
    
    db.commit()
    db.refresh(item)
    
    return item
