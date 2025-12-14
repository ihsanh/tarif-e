from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List, Dict
from datetime import date, timedelta
from collections import defaultdict

from app.database import get_db
from app.models.menu_plan import WeeklyMenuPlan, MenuItem, MenuShoppingListItem
from app.models.user import User
from app.models.tarif import FavoriTarif
from app.schemas.menu_plan import (
    WeeklyMenuPlanCreate,
    WeeklyMenuPlanUpdate,
    WeeklyMenuPlanResponse,
    WeeklyMenuPlanSummary,
    MenuItemCreate,
    MenuItemUpdate,
    MenuItemResponse,
    ShoppingListItemResponse,
    ShoppingListItemUpdate,
    WeeklyNutritionSummary,
    DailyNutritionSummary,
)
from app.utils.auth import get_current_user


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


# ============================================================
# SHOPPING LIST - Alışveriş Listesi
# ============================================================

@router.get("/{menu_id}/shopping-list", response_model=List[ShoppingListItemResponse])
async def generate_shopping_list(
        menu_id: int,
        regenerate: bool = False,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Menü için alışveriş listesi oluştur

    - regenerate=True: Mevcut listeyi sil ve yeniden oluştur
    - regenerate=False: Varolan listeyi getir, yoksa oluştur
    """
    # Menü kontrolü
    menu = db.query(WeeklyMenuPlan) \
        .filter(WeeklyMenuPlan.id == menu_id) \
        .filter(WeeklyMenuPlan.user_id == current_user.id) \
        .first()

    if not menu:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menü bulunamadı"
        )

    # Mevcut liste varsa ve regenerate=False ise getir
    if not regenerate and menu.shopping_list_items:
        return menu.shopping_list_items

    # Listeyi sil (regenerate durumu)
    if regenerate:
        db.query(MenuShoppingListItem) \
            .filter(MenuShoppingListItem.menu_plan_id == menu_id) \
            .delete()
        db.commit()

    # Menu items'dan malzemeleri topla
    menu_items = db.query(MenuItem) \
        .filter(MenuItem.menu_plan_id == menu_id) \
        .all()

    if not menu_items:
        return []

    # Malzemeleri grupla ve topla
    ingredients_dict = defaultdict(lambda: {"amount": 0, "unit": None, "category": "OTHER"})

    for item in menu_items:
        if not item.tarif_id:
            continue

        tarif = db.query(FavoriTarif) \
            .filter(FavoriTarif.id == item.tarif_id) \
            .first()

        if not tarif or not tarif.malzemeler:
            continue

        # Malzemeleri parse et (basit text parsing)
        # Format: "200 gram domates, 3 adet yumurta, ..."
        try:
            malzeme_list = tarif.malzemeler.split(',')

            for malzeme_str in malzeme_list:
                malzeme_str = malzeme_str.strip()
                if not malzeme_str:
                    continue

                # Basit parsing: "200 gram domates"
                parts = malzeme_str.split()
                if len(parts) >= 3:
                    try:
                        amount = float(parts[0]) * item.portions
                        unit = parts[1]
                        name = ' '.join(parts[2:])

                        # Aynı malzeme varsa topla
                        key = f"{name}_{unit}"
                        ingredients_dict[key]["amount"] += amount
                        ingredients_dict[key]["unit"] = unit
                        ingredients_dict[key]["name"] = name
                    except ValueError:
                        # Miktar sayı değilse, olduğu gibi ekle
                        name = malzeme_str
                        key = name
                        ingredients_dict[key]["amount"] = 1
                        ingredients_dict[key]["unit"] = "adet"
                        ingredients_dict[key]["name"] = name
                else:
                    # Format farklıysa olduğu gibi ekle
                    name = malzeme_str
                    key = name
                    ingredients_dict[key]["amount"] = 1
                    ingredients_dict[key]["unit"] = "adet"
                    ingredients_dict[key]["name"] = name

        except Exception as e:
            print(f"Malzeme parse hatası: {e}")
            continue

    # Shopping list items oluştur
    shopping_items = []

    for key, data in ingredients_dict.items():
        new_item = MenuShoppingListItem(
            menu_plan_id=menu_id,
            ingredient_name=data["name"],
            total_amount=str(data["amount"]),
            unit=data["unit"],
            category=data.get("category", "OTHER")
        )
        db.add(new_item)
        shopping_items.append(new_item)

    db.commit()

    # Refresh all items
    for item in shopping_items:
        db.refresh(item)

    return shopping_items


@router.put("/shopping-items/{item_id}", response_model=ShoppingListItemResponse)
async def update_shopping_item(
        item_id: int,
        item_data: ShoppingListItemUpdate,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Alışveriş listesi öğesini güncelle
    (Satın alındı, evde var, vb.)
    """
    item = db.query(MenuShoppingListItem) \
        .join(WeeklyMenuPlan) \
        .filter(MenuShoppingListItem.id == item_id) \
        .filter(WeeklyMenuPlan.user_id == current_user.id) \
        .first()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alışveriş öğesi bulunamadı"
        )

    # Güncellemeleri uygula
    update_data = item_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(item, field, value)

    db.commit()
    db.refresh(item)

    return item


# ============================================================
# NUTRITION - Besin Değerleri
# ============================================================

@router.get("/{menu_id}/nutrition", response_model=WeeklyNutritionSummary)
async def get_nutrition_summary(
        menu_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Haftalık besin değerleri özeti

    NOT: Bu basit bir implementasyon.
    Gerçek besin değerleri için recipe_nutritions tablosu kullanılmalı.
    """
    # Menü kontrolü
    menu = db.query(WeeklyMenuPlan) \
        .filter(WeeklyMenuPlan.id == menu_id) \
        .filter(WeeklyMenuPlan.user_id == current_user.id) \
        .first()

    if not menu:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menü bulunamadı"
        )

    # Menu items'ları grupla (gün bazında)
    daily_data = defaultdict(lambda: {
        "calories": 0,
        "protein": 0,
        "carbs": 0,
        "fat": 0,
        "fiber": 0,
        "meal_count": 0
    })

    day_names = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]

    menu_items = db.query(MenuItem) \
        .filter(MenuItem.menu_plan_id == menu_id) \
        .all()

    # Her öğün için besin değerlerini topla
    for item in menu_items:
        day = item.day_of_week

        # Basit tahmini değerler (gerçek uygulamada recipe_nutritions kullanılmalı)
        # Bu sadece örnek
        calories = 500 * item.portions  # Öğün başına ortalama 500 kalori
        protein = 20 * item.portions
        carbs = 50 * item.portions
        fat = 15 * item.portions
        fiber = 5 * item.portions

        daily_data[day]["calories"] += calories
        daily_data[day]["protein"] += protein
        daily_data[day]["carbs"] += carbs
        daily_data[day]["fat"] += fat
        daily_data[day]["fiber"] += fiber
        daily_data[day]["meal_count"] += 1

    # Daily summaries oluştur
    daily_summaries = []
    total_calories = 0

    for day in range(7):
        data = daily_data[day]

        daily_summary = DailyNutritionSummary(
            day_of_week=day,
            day_name=day_names[day],
            total_calories=data["calories"],
            total_protein=data["protein"],
            total_carbs=data["carbs"],
            total_fat=data["fat"],
            total_fiber=data["fiber"],
            meal_count=data["meal_count"]
        )

        daily_summaries.append(daily_summary)
        total_calories += data["calories"]

    # Haftalık özet
    weekly_summary = WeeklyNutritionSummary(
        menu_plan_id=menu_id,
        daily_summaries=daily_summaries,
        weekly_total_calories=total_calories,
        weekly_avg_calories=total_calories / 7 if total_calories > 0 else 0,
        weekly_total_protein=sum(d["protein"] for d in daily_data.values()),
        weekly_total_carbs=sum(d["carbs"] for d in daily_data.values()),
        weekly_total_fat=sum(d["fat"] for d in daily_data.values())
    )

    return weekly_summary
