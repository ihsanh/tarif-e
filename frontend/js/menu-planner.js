// Menu Planner JavaScript
// ✅ API: /api/menu-plans endpoints

const API_BASE = window.location.origin;
let currentMenuId = null;
let currentMenuData = null;
let allRecipes = [];

// ============================================================
// INITIALIZATION
// ============================================================

document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
    initializeEventListeners();
    loadActiveMenu();
    loadRecipes();
});

function checkAuth() {
    const token = localStorage.getItem('access_token');
    if (!token) {
        window.location.href = '/login.html';
        return;
    }
}

function getAuthHeaders() {
    return {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'Content-Type': 'application/json'
    };
}

// ============================================================
// EVENT LISTENERS
// ============================================================

function initializeEventListeners() {
    // Logout
    document.getElementById('logoutBtn')?.addEventListener('click', logout);
    
    // Create Menu
    document.getElementById('createMenuBtn')?.addEventListener('click', openCreateMenuModal);
    document.getElementById('createMenuForm')?.addEventListener('submit', handleCreateMenu);
    
    // View Menus
    document.getElementById('viewMenusBtn')?.addEventListener('click', openMenuListModal);
    
    // Menu Actions
    document.getElementById('editMenuBtn')?.addEventListener('click', editMenu);
    document.getElementById('deleteMenuBtn')?.addEventListener('click', deleteMenu);
    
    // Quick Actions
    document.getElementById('viewShoppingListBtn')?.addEventListener('click', viewShoppingList);
    document.getElementById('viewNutritionBtn')?.addEventListener('click', viewNutrition);
    
    // Add Meal
    document.getElementById('addMealForm')?.addEventListener('submit', handleAddMeal);
    document.getElementById('recipeSearch')?.addEventListener('input', filterRecipes);
    
    // Week start date change
    document.getElementById('weekStart')?.addEventListener('change', calculateWeekEnd);
    
    // Shopping list regenerate
    document.getElementById('regenerateListBtn')?.addEventListener('click', () => {
        if (currentMenuId) {
            loadShoppingList(currentMenuId, true);
        }
    });
    
    // Modal close buttons
    document.querySelectorAll('.close-modal').forEach(btn => {
        btn.addEventListener('click', () => closeModal(btn.closest('.modal')));
    });
    
    // Click outside modal to close
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeModal(modal);
            }
        });
    });
}

// ============================================================
// API FUNCTIONS - MENU PLANS
// ============================================================

async function loadActiveMenu() {
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE}/api/menu-plans/active`, {
            headers: getAuthHeaders()
        });
        
        if (response.ok) {
            const menu = await response.json();
            currentMenuId = menu.id;
            currentMenuData = menu;
            displayActiveMenu(menu);
            renderWeekView(menu);
            
            // Enable quick actions
            document.getElementById('viewShoppingListBtn').disabled = false;
            document.getElementById('viewNutritionBtn').disabled = false;
        } else if (response.status === 404) {
            // No active menu
            displayNoMenu();
        } else {
            throw new Error('Menü yüklenemedi');
        }
    } catch (error) {
        console.error('Error loading active menu:', error);
        showToast('Menü yüklenirken hata oluştu', 'error');
        displayNoMenu();
    } finally {
        showLoading(false);
    }
}

async function createMenuPlan(menuData) {
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE}/api/menu-plans`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify(menuData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Menü oluşturulamadı');
        }
        
        const menu = await response.json();
        showToast('Menü başarıyla oluşturuldu!', 'success');
        
        // Reload active menu
        await loadActiveMenu();
        
        return menu;
    } catch (error) {
        console.error('Error creating menu:', error);
        showToast(error.message, 'error');
        throw error;
    } finally {
        showLoading(false);
    }
}

async function updateMenuPlan(menuId, updateData) {
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE}/api/menu-plans/${menuId}`, {
            method: 'PUT',
            headers: getAuthHeaders(),
            body: JSON.stringify(updateData)
        });
        
        if (!response.ok) {
            throw new Error('Menü güncellenemedi');
        }
        
        const menu = await response.json();
        showToast('Menü güncellendi!', 'success');
        
        await loadActiveMenu();
        
        return menu;
    } catch (error) {
        console.error('Error updating menu:', error);
        showToast('Güncelleme hatası', 'error');
        throw error;
    } finally {
        showLoading(false);
    }
}

async function deleteMenuPlan(menuId) {
    if (!confirm('Bu menüyü silmek istediğinize emin misiniz?')) {
        return;
    }
    
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE}/api/menu-plans/${menuId}`, {
            method: 'DELETE',
            headers: getAuthHeaders()
        });
        
        if (!response.ok) {
            throw new Error('Menü silinemedi');
        }
        
        showToast('Menü silindi', 'success');
        
        // Clear current menu
        currentMenuId = null;
        currentMenuData = null;
        displayNoMenu();
        
    } catch (error) {
        console.error('Error deleting menu:', error);
        showToast('Silme hatası', 'error');
    } finally {
        showLoading(false);
    }
}

async function getAllMenus() {
    try {
        const response = await fetch(`${API_BASE}/api/menu-plans`, {
            headers: getAuthHeaders()
        });
        
        if (!response.ok) {
            throw new Error('Menüler yüklenemedi');
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error loading menus:', error);
        showToast('Menüler yüklenirken hata', 'error');
        return [];
    }
}

// ============================================================
// API FUNCTIONS - MENU ITEMS
// ============================================================

async function addMenuItem(menuId, itemData) {
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE}/api/menu-plans/${menuId}/items`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify(itemData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Öğün eklenemedi');
        }
        
        const item = await response.json();
        showToast('Öğün eklendi!', 'success');
        
        // Reload menu
        await loadActiveMenu();
        
        return item;
    } catch (error) {
        console.error('Error adding menu item:', error);
        showToast(error.message, 'error');
        throw error;
    } finally {
        showLoading(false);
    }
}

async function deleteMenuItem(itemId) {
    if (!confirm('Bu öğünü silmek istediğinize emin misiniz?')) {
        return;
    }
    
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE}/api/menu-plans/items/${itemId}`, {
            method: 'DELETE',
            headers: getAuthHeaders()
        });
        
        if (!response.ok) {
            throw new Error('Öğün silinemedi');
        }
        
        showToast('Öğün silindi', 'success');
        
        // Reload menu
        await loadActiveMenu();
        
    } catch (error) {
        console.error('Error deleting menu item:', error);
        showToast('Silme hatası', 'error');
    } finally {
        showLoading(false);
    }
}

async function toggleMealComplete(itemId) {
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE}/api/menu-plans/items/${itemId}/complete`, {
            method: 'PATCH',
            headers: getAuthHeaders()
        });
        
        if (!response.ok) {
            throw new Error('Durum güncellenemedi');
        }
        
        // Reload menu
        await loadActiveMenu();
        
    } catch (error) {
        console.error('Error toggling completion:', error);
        showToast('Güncelleme hatası', 'error');
    } finally {
        showLoading(false);
    }
}

// ============================================================
// API FUNCTIONS - RECIPES (Favoriler)
// ============================================================

async function loadRecipes() {
    try {
        // Load from favori_tarifler
        console.log('Loading recipes from:', `${API_BASE}/api/favoriler`);
        const response = await fetch(`${API_BASE}/api/favoriler`, {
            headers: getAuthHeaders()
        });

        console.log('Response status:', response.status);

        if (response.ok) {
            const data = await response.json();
            console.log('Loaded recipes data:', data);

            // Backend returns { success: true, favoriler: [...] }
            if (data.favoriler && Array.isArray(data.favoriler)) {
                allRecipes = data.favoriler;
            } else if (Array.isArray(data)) {
                allRecipes = data;
            } else {
                allRecipes = [];
            }

            console.log('All recipes count:', allRecipes.length);
        } else {
            console.error('Failed to load recipes:', response.status, response.statusText);
            allRecipes = [];
        }
    } catch (error) {
        console.error('Error loading recipes:', error);
        allRecipes = [];
    }
}

// ============================================================
// API FUNCTIONS - SHOPPING LIST
// ============================================================

async function loadShoppingList(menuId, regenerate = false) {
    showLoading(true);
    
    try {
        const url = `${API_BASE}/api/menu-plans/${menuId}/shopping-list${regenerate ? '?regenerate=true' : ''}`;
        const response = await fetch(url, {
            headers: getAuthHeaders()
        });
        
        if (!response.ok) {
            throw new Error('Alışveriş listesi oluşturulamadı');
        }
        
        const items = await response.json();
        displayShoppingList(items);
        
        if (regenerate) {
            showToast('Liste yenilendi', 'success');
        }
        
    } catch (error) {
        console.error('Error loading shopping list:', error);
        showToast('Liste yüklenirken hata', 'error');
    } finally {
        showLoading(false);
    }
}

async function updateShoppingItem(itemId, updateData) {
    try {
        const response = await fetch(`${API_BASE}/api/menu-plans/shopping-items/${itemId}`, {
            method: 'PUT',
            headers: getAuthHeaders(),
            body: JSON.stringify(updateData)
        });
        
        if (!response.ok) {
            throw new Error('Güncelleme başarısız');
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error updating shopping item:', error);
        showToast('Güncelleme hatası', 'error');
    }
}

// ============================================================
// API FUNCTIONS - NUTRITION
// ============================================================

async function loadNutrition(menuId) {
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE}/api/menu-plans/${menuId}/nutrition`, {
            headers: getAuthHeaders()
        });
        
        if (!response.ok) {
            throw new Error('Besin değerleri yüklenemedi');
        }
        
        const nutrition = await response.json();
        displayNutrition(nutrition);
        
    } catch (error) {
        console.error('Error loading nutrition:', error);
        showToast('Besin değerleri yüklenirken hata', 'error');
    } finally {
        showLoading(false);
    }
}

// Continue in Part 2...
// Menu Planner JavaScript - Part 2: UI Functions

// ============================================================
// UI FUNCTIONS - DISPLAY
// ============================================================

function displayActiveMenu(menu) {
    const infoCard = document.getElementById('activeMenuInfo');
    const menuName = document.getElementById('activeMenuName');
    const menuDates = document.getElementById('activeMenuDates');
    
    infoCard.style.display = 'block';
    menuName.textContent = menu.name;
    
    const startDate = new Date(menu.week_start_date).toLocaleDateString('tr-TR');
    const endDate = new Date(menu.week_end_date).toLocaleDateString('tr-TR');
    menuDates.textContent = `${startDate} - ${endDate}`;
}

function displayNoMenu() {
    document.getElementById('activeMenuInfo').style.display = 'none';
    document.getElementById('weekView').innerHTML = `
        <div class="no-menu-message" style="grid-column: 1 / -1; text-align: center; padding: 3rem;">
            <i class="fas fa-calendar-plus" style="font-size: 4rem; color: var(--gray); margin-bottom: 1rem;"></i>
            <h3>Henüz aktif menü yok</h3>
            <p style="color: var(--gray); margin-bottom: 1.5rem;">Yeni bir menü oluşturarak başlayın</p>
            <button class="btn btn-primary" onclick="openCreateMenuModal()">
                <i class="fas fa-plus"></i> Yeni Menü Oluştur
            </button>
        </div>
    `;
    
    // Disable quick actions
    document.getElementById('viewShoppingListBtn').disabled = true;
    document.getElementById('viewNutritionBtn').disabled = true;
}

function renderWeekView(menu) {
    const weekView = document.getElementById('weekView');
    const days = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi', 'Pazar'];
    const mealTypes = [
        { type: 'breakfast', icon: 'fa-coffee', label: 'Kahvaltı' },
        { type: 'lunch', icon: 'fa-utensils', label: 'Öğle' },
        { type: 'dinner', icon: 'fa-moon', label: 'Akşam' }
    ];
    
    weekView.innerHTML = '';
    
    // Get start date
    const startDate = new Date(menu.week_start_date);
    
    for (let dayIndex = 0; dayIndex < 7; dayIndex++) {
        const currentDate = new Date(startDate);
        currentDate.setDate(startDate.getDate() + dayIndex);
        
        const dayColumn = document.createElement('div');
        dayColumn.className = 'day-column';
        
        // Day header
        const dayHeader = document.createElement('div');
        dayHeader.className = 'day-header';
        dayHeader.innerHTML = `
            <h3>${days[dayIndex]}</h3>
            <p>${currentDate.toLocaleDateString('tr-TR', { day: 'numeric', month: 'short' })}</p>
        `;
        
        // Day content
        const dayContent = document.createElement('div');
        dayContent.className = 'day-content';
        
        // Add meal slots/cards
        mealTypes.forEach(meal => {
            const menuItem = menu.menu_items?.find(
                item => item.day_of_week === dayIndex && item.meal_type === meal.type
            );
            
            if (menuItem) {
                dayContent.appendChild(createMealCard(menuItem, meal));
            } else {
                dayContent.appendChild(createMealSlot(dayIndex, meal));
            }
        });
        
        dayColumn.appendChild(dayHeader);
        dayColumn.appendChild(dayContent);
        weekView.appendChild(dayColumn);
    }
}

function createMealSlot(dayIndex, meal) {
    const slot = document.createElement('div');
    slot.className = 'meal-slot';
    slot.innerHTML = `
        <i class="fas ${meal.icon}"></i>
        <span>${meal.label} Ekle</span>
    `;
    
    slot.addEventListener('click', () => openAddMealModal(dayIndex, meal.type));
    
    return slot;
}

function createMealCard(menuItem, meal) {
    const card = document.createElement('div');
    card.className = `meal-card ${menuItem.is_completed ? 'meal-completed' : ''}`;
    
    // Get recipe name (if available)
    const recipeName = menuItem.tarif_baslik || `Tarif #${menuItem.tarif_id || 'Bilinmiyor'}`;
    
    card.innerHTML = `
        <div class="meal-header">
            <span class="meal-icon"><i class="fas ${meal.icon}"></i></span>
            <div class="meal-actions">
                <button class="btn-icon" onclick="toggleMealComplete(${menuItem.id})" title="${menuItem.is_completed ? 'Tamamlanmadı işaretle' : 'Tamamlandı işaretle'}">
                    <i class="fas ${menuItem.is_completed ? 'fa-undo' : 'fa-check'}"></i>
                </button>
                <button class="btn-icon" onclick="deleteMenuItem(${menuItem.id})" title="Sil">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </div>
        <div class="meal-body">
            <h4>${recipeName}</h4>
            <div class="meal-meta">
                <span><i class="fas fa-users"></i> ${menuItem.portions} kişilik</span>
                ${menuItem.notes ? `<span><i class="fas fa-sticky-note"></i> Not var</span>` : ''}
            </div>
        </div>
    `;
    
    return card;
}

function displayShoppingList(items) {
    const content = document.getElementById('shoppingListContent');
    
    if (items.length === 0) {
        content.innerHTML = `
            <div style="text-align: center; padding: 3rem; color: var(--gray);">
                <i class="fas fa-shopping-basket" style="font-size: 3rem; margin-bottom: 1rem;"></i>
                <p>Henüz alışveriş listesi yok</p>
                <p>Menüye öğün ekleyin</p>
            </div>
        `;
        return;
    }
    
    // Group by category
    const grouped = {};
    items.forEach(item => {
        const category = item.category || 'OTHER';
        if (!grouped[category]) {
            grouped[category] = [];
        }
        grouped[category].push(item);
    });
    
    content.innerHTML = '';
    
    const categoryNames = {
        'VEGETABLES': 'Sebzeler',
        'FRUITS': 'Meyveler',
        'MEAT': 'Et/Tavuk',
        'FISH': 'Balık',
        'DAIRY': 'Süt Ürünleri',
        'GRAINS': 'Tahıllar',
        'SPICES': 'Baharatlar',
        'OILS': 'Yağlar',
        'BEVERAGES': 'İçecekler',
        'OTHER': 'Diğer'
    };
    
    Object.entries(grouped).forEach(([category, categoryItems]) => {
        const categorySection = document.createElement('div');
        categorySection.innerHTML = `<h4 style="margin-bottom: 1rem; color: var(--dark);">${categoryNames[category] || category}</h4>`;
        
        categoryItems.forEach(item => {
            const itemDiv = document.createElement('div');
            itemDiv.className = `shopping-item ${item.is_purchased ? 'purchased' : ''}`;
            itemDiv.innerHTML = `
                <input type="checkbox" 
                       ${item.is_purchased ? 'checked' : ''} 
                       onchange="handleShoppingItemCheck(${item.id}, this.checked)">
                <div class="item-details">
                    <div class="item-name">${item.ingredient_name}</div>
                    <div class="item-amount">${item.total_amount} ${item.unit}</div>
                </div>
                ${item.is_in_stock ? '<span class="badge badge-success">Evde var</span>' : ''}
            `;
            categorySection.appendChild(itemDiv);
        });
        
        content.appendChild(categorySection);
    });
}

function displayNutrition(nutrition) {
    const content = document.getElementById('nutritionContent');
    
    // Weekly summary
    const summaryDiv = document.createElement('div');
    summaryDiv.className = 'nutrition-summary';
    summaryDiv.innerHTML = `
        <h3>Haftalık Özet</h3>
        <div class="nutrition-stats">
            <div class="stat-item">
                <div class="stat-value">${Math.round(nutrition.weekly_avg_calories)}</div>
                <div class="stat-label">Ortalama Günlük Kalori</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">${Math.round(nutrition.weekly_total_protein)}g</div>
                <div class="stat-label">Toplam Protein</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">${Math.round(nutrition.weekly_total_carbs)}g</div>
                <div class="stat-label">Toplam Karbonhidrat</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">${Math.round(nutrition.weekly_total_fat)}g</div>
                <div class="stat-label">Toplam Yağ</div>
            </div>
        </div>
    `;
    
    // Daily breakdown
    const dailyDiv = document.createElement('div');
    dailyDiv.className = 'daily-nutrition';
    dailyDiv.innerHTML = '<h3 style="margin-bottom: 1rem;">Günlük Detay</h3>';
    
    nutrition.daily_summaries.forEach(day => {
        const dayDiv = document.createElement('div');
        dayDiv.className = 'day-nutrition';
        dayDiv.innerHTML = `
            <h4>${day.day_name} - ${day.meal_count} öğün</h4>
            <div class="day-stats">
                <div class="day-stat">Kalori: <strong>${Math.round(day.total_calories)}</strong></div>
                <div class="day-stat">Protein: <strong>${Math.round(day.total_protein)}g</strong></div>
                <div class="day-stat">Karbonhidrat: <strong>${Math.round(day.total_carbs)}g</strong></div>
                <div class="day-stat">Yağ: <strong>${Math.round(day.total_fat)}g</strong></div>
            </div>
        `;
        dailyDiv.appendChild(dayDiv);
    });
    
    content.innerHTML = '';
    content.appendChild(summaryDiv);
    content.appendChild(dailyDiv);
}

// ============================================================
// MODAL FUNCTIONS
// ============================================================

function openCreateMenuModal() {
    const modal = document.getElementById('createMenuModal');
    modal.classList.add('active');
    
    // Set default dates (next Monday)
    const today = new Date();
    const nextMonday = getNextMonday(today);
    document.getElementById('weekStart').valueAsDate = nextMonday;
    calculateWeekEnd();
}

function openAddMealModal(dayIndex, mealType) {
    if (!currentMenuId) {
        showToast('Önce bir menü oluşturun', 'warning');
        return;
    }
    
    const modal = document.getElementById('addMealModal');
    modal.classList.add('active');
    
    document.getElementById('mealDay').value = dayIndex;
    document.getElementById('mealType').value = mealType;
    document.getElementById('selectedRecipeId').value = '';
    
    // Display recipes
    displayRecipeList(allRecipes);
}

function openMenuListModal() {
    const modal = document.getElementById('menuListModal');
    modal.classList.add('active');
    loadAllMenus();
}

function closeModal(modal) {
    modal.classList.remove('active');
    
    // Reset forms
    modal.querySelectorAll('form').forEach(form => form.reset());
}

function viewShoppingList() {
    if (!currentMenuId) return;
    
    const modal = document.getElementById('shoppingListModal');
    modal.classList.add('active');
    loadShoppingList(currentMenuId);
}

function viewNutrition() {
    if (!currentMenuId) return;
    
    const modal = document.getElementById('nutritionModal');
    modal.classList.add('active');
    loadNutrition(currentMenuId);
}

// ============================================================
// FORM HANDLERS
// ============================================================

async function handleCreateMenu(e) {
    e.preventDefault();
    
    const menuData = {
        name: document.getElementById('menuName').value,
        description: document.getElementById('menuDescription').value,
        week_start_date: document.getElementById('weekStart').value,
        week_end_date: document.getElementById('weekEnd').value,
        is_active: document.getElementById('setActive').checked
    };
    
    try {
        await createMenuPlan(menuData);
        closeModal(document.getElementById('createMenuModal'));
    } catch (error) {
        // Error already shown in createMenuPlan
    }
}

async function handleAddMeal(e) {
    e.preventDefault();
    
    const recipeId = document.getElementById('selectedRecipeId').value;
    
    if (!recipeId) {
        showToast('Lütfen bir tarif seçin', 'warning');
        return;
    }
    
    const itemData = {
        tarif_id: parseInt(recipeId),
        day_of_week: parseInt(document.getElementById('mealDay').value),
        meal_type: document.getElementById('mealType').value,
        portions: parseInt(document.getElementById('portions').value),
        notes: document.getElementById('mealNotes').value
    };
    
    try {
        await addMenuItem(currentMenuId, itemData);
        closeModal(document.getElementById('addMealModal'));
    } catch (error) {
        // Error already shown
    }
}

async function handleShoppingItemCheck(itemId, checked) {
    await updateShoppingItem(itemId, { is_purchased: checked });
}

// Continue in Part 3...
// Menu Planner JavaScript - Part 3: Utility Functions

// ============================================================
// UTILITY FUNCTIONS
// ============================================================

function calculateWeekEnd() {
    const weekStart = document.getElementById('weekStart').value;
    if (!weekStart) return;
    
    const startDate = new Date(weekStart);
    const endDate = new Date(startDate);
    endDate.setDate(startDate.getDate() + 6); // +6 days = Sunday
    
    document.getElementById('weekEnd').valueAsDate = endDate;
}

function getNextMonday(date) {
    const d = new Date(date);
    const day = d.getDay();
    const diff = day === 0 ? 1 : 8 - day; // If Sunday (0), next day is Monday
    d.setDate(d.getDate() + diff);
    return d;
}

function displayRecipeList(recipes) {
    const listDiv = document.getElementById('recipeList');

    console.log('Displaying recipes:', recipes);

    if (!recipes || recipes.length === 0) {
        listDiv.innerHTML = '<p style="text-align: center; color: var(--gray); padding: 2rem;">Henüz favori tarif yok. Ana sayfadan favori ekleyin.</p>';
        return;
    }

    listDiv.innerHTML = '';

    recipes.forEach(recipe => {
        const item = document.createElement('div');
        item.className = 'recipe-item';
        item.innerHTML = `
            <h4>${recipe.baslik}</h4>
            <p>${recipe.kategori || 'Kategori yok'} ${recipe.sure ? `• ${recipe.sure} dk` : ''}</p>
        `;

        item.addEventListener('click', () => {
            // Deselect all
            document.querySelectorAll('.recipe-item').forEach(i => i.classList.remove('selected'));
            // Select this
            item.classList.add('selected');
            document.getElementById('selectedRecipeId').value = recipe.id;
        });

        listDiv.appendChild(item);
    });
}

function filterRecipes() {
    const searchTerm = document.getElementById('recipeSearch').value.toLowerCase();

    // Ensure allRecipes is an array
    if (!Array.isArray(allRecipes)) {
        console.error('allRecipes is not an array:', allRecipes);
        displayRecipeList([]);
        return;
    }

    const filtered = allRecipes.filter(recipe =>
        recipe.baslik.toLowerCase().includes(searchTerm) ||
        (recipe.kategori && recipe.kategori.toLowerCase().includes(searchTerm))
    );
    displayRecipeList(filtered);
}

async function loadAllMenus() {
    const content = document.getElementById('menuListContent');
    content.innerHTML = '<div style="text-align: center; padding: 2rem;"><div class="spinner"></div></div>';
    
    const menus = await getAllMenus();
    
    if (menus.length === 0) {
        content.innerHTML = '<p style="text-align: center; color: var(--gray); padding: 2rem;">Henüz menü yok</p>';
        return;
    }
    
    content.innerHTML = '';
    
    menus.forEach(menu => {
        const item = document.createElement('div');
        item.className = `menu-list-item ${menu.is_active ? 'active' : ''}`;
        
        const startDate = new Date(menu.week_start_date).toLocaleDateString('tr-TR');
        const endDate = new Date(menu.week_end_date).toLocaleDateString('tr-TR');
        
        item.innerHTML = `
            <h4>${menu.name} ${menu.is_active ? '<span class="badge badge-success">Aktif</span>' : ''}</h4>
            <p>${startDate} - ${endDate}</p>
            <p style="font-size: 0.85rem;">
                ${menu.total_recipes} tarif • ${menu.total_shopping_items} malzeme
            </p>
        `;
        
        item.addEventListener('click', async () => {
            if (!menu.is_active) {
                if (confirm('Bu menüyü aktif yapmak ister misiniz?')) {
                    await updateMenuPlan(menu.id, { is_active: true });
                    closeModal(document.getElementById('menuListModal'));
                }
            } else {
                closeModal(document.getElementById('menuListModal'));
            }
        });
        
        content.appendChild(item);
    });
}

async function editMenu() {
    if (!currentMenuData) return;
    
    // Open edit modal with current data
    const name = prompt('Menü adı:', currentMenuData.name);
    if (name && name !== currentMenuData.name) {
        await updateMenuPlan(currentMenuId, { name });
    }
}

async function deleteMenu() {
    if (!currentMenuId) return;
    await deleteMenuPlan(currentMenuId);
}

function showLoading(show) {
    document.getElementById('loadingSpinner').style.display = show ? 'flex' : 'none';
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    const icons = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle'
    };
    
    toast.innerHTML = `
        <i class="fas ${icons[type] || icons.info}"></i>
        <span>${message}</span>
    `;
    
    container.appendChild(toast);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        toast.style.animation = 'slideOutRight 0.3s';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function logout() {
    if (confirm('Çıkış yapmak istediğinize emin misiniz?')) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
        window.location.href = '/login.html';
    }
}

// ============================================================
// EXPORT (for global access)
// ============================================================

// Make functions available globally
window.toggleMealComplete = toggleMealComplete;
window.deleteMenuItem = deleteMenuItem;
window.handleShoppingItemCheck = handleShoppingItemCheck;
window.openCreateMenuModal = openCreateMenuModal;
