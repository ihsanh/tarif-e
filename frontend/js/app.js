// Tarif-e JavaScript

// API Base URL
const API_BASE = window.location.origin;

// Global state
let currentIngredients = [];
let currentRecipe = null;

// Sayfa yüklendiğinde
document.addEventListener('DOMContentLoaded', () => {
    console.log('🍳 Tarif-e başlatılıyor...');
    loadMyIngredients();
    loadSettings();
    
    // Fotoğraf seçildiğinde
    document.getElementById('photo-input').addEventListener('change', handlePhotoSelect);
});

function showScreen(screenId) {
    // Tüm ekranları gizle
    document.querySelectorAll('.screen').forEach(screen => {
        screen.classList.remove('active');
    });

    // Seçilen ekranı göster
    document.getElementById(screenId).classList.add('active');

    // Malzemelerim ekranına geçildiğinde yeniden yükle
    if (screenId === 'my-ingredients-screen') {
        loadMyIngredients();
    }
}

// Loading göster/gizle
function showLoading(show = true) {
    document.getElementById('loading').style.display = show ? 'flex' : 'none';
}

// Fotoğraf seçildiğinde
async function handlePhotoSelect(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    // Önizleme göster
    const reader = new FileReader();
    reader.onload = (e) => {
        const preview = document.getElementById('photo-preview');
        preview.innerHTML = `<img src="${e.target.result}" alt="Seçilen fotoğraf">`;
    };
    reader.readAsDataURL(file);
    
    // AI ile malzeme tanıma
    showLoading(true);
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch(`${API_BASE}/api/malzeme/tani`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentIngredients = data.malzemeler;
            displayDetectedIngredients(data.malzemeler);
            document.getElementById('get-recipe-btn').style.display = 'block';
        } else {
            alert('Malzemeler tanınamadı. Manuel ekleme yapabilirsiniz.');
        }
        
    } catch (error) {
        console.error('Error:', error);
        alert('Bir hata oluştu: ' + error.message);
    } finally {
        showLoading(false);
    }
}

// Tanınan malzemeleri göster
function displayDetectedIngredients(ingredients) {
    const container = document.getElementById('detected-ingredients');
    
    if (ingredients.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">🤷</div>
                <p>Malzeme tanınamadı</p>
            </div>
        `;
        return;
    }
    
    let html = '<h3>✅ Tanınan Malzemeler:</h3>';
    
    ingredients.forEach((ingredient, index) => {
        html += `
            <div class="ingredient-item">
                <span class="ingredient-name">${ingredient}</span>
                <button class="ingredient-remove" onclick="removeIngredient(${index})">Kaldır</button>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

// Malzeme kaldır
function removeIngredient(index) {
    currentIngredients.splice(index, 1);
    displayDetectedIngredients(currentIngredients);
    
    if (currentIngredients.length === 0) {
        document.getElementById('get-recipe-btn').style.display = 'none';
    }
}

// Manuel malzeme ekleme
async function addManualIngredient() {
    const name = document.getElementById('ingredient-name').value.trim();
    const amount = parseFloat(document.getElementById('ingredient-amount').value);
    const unit = document.getElementById('ingredient-unit').value;
    
    if (!name) {
        alert('Lütfen malzeme adı girin');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/malzeme/ekle`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ name, miktar: amount, birim: unit })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Listeye ekle
            currentIngredients.push(name);
            
            // Formu temizle
            document.getElementById('ingredient-name').value = '';
            document.getElementById('ingredient-amount').value = '1';
            
            // Liste güncelle
            updateManualIngredientsList();
            
            alert(`${name} eklendi!`);
        }
        
    } catch (error) {
        console.error('Error:', error);
        alert('Malzeme eklenirken hata oluştu');
    }
}

// Manuel malzeme listesini güncelle
function updateManualIngredientsList() {
    const container = document.getElementById('manual-ingredients-list');
    
    if (currentIngredients.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📝</div>
                <p>Henüz malzeme eklemediniz</p>
            </div>
        `;
        return;
    }
    
    let html = '<h3>📋 Eklenen Malzemeler:</h3>';
    
    currentIngredients.forEach((ingredient, index) => {
        html += `
            <div class="ingredient-item">
                <span class="ingredient-name">${ingredient}</span>
                <button class="ingredient-remove" onclick="removeIngredient(${index})">Sil</button>
            </div>
        `;
    });
    
    html += '<button class="btn btn-success" style="margin-top: 20px;" onclick="getTarifOnerisi()">🍽️ Tarif Öner</button>';
    
    container.innerHTML = html;
}

// Global değişkenler
let currentEditingIngredient = null;

// Malzemeleri listelerken düzenle butonu ekle
async function loadMyIngredients() {
    console.log('🔄 Malzemeler yükleniyor...');

    try {
        const response = await fetch(`${API_BASE}/api/malzeme/liste`);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log('✅ Malzemeler:', data);

        const container = document.getElementById('my-ingredients-list');

        if (!data.malzemeler || data.malzemeler.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">🗂️</div>
                    <p>Malzeme listeniz boş</p>
                    <p style="font-size: 0.9em; color: #718096;">Manuel Ekle'den malzeme ekleyin</p>
                </div>
            `;
            return;
        }

        let html = '';
        data.malzemeler.forEach(item => {
            html += `
                <div class="ingredient-item">
                    <span class="ingredient-name">${item.name}</span>
                    <span class="ingredient-amount">${item.miktar} ${item.birim}</span>
                    <div class="ingredient-actions">
                        <button class="btn-edit" onclick="editIngredient(${item.id}, '${item.name}', ${item.miktar}, '${item.birim}')">
                            ✏️ Düzenle
                        </button>
                        <button class="ingredient-remove" onclick="deleteIngredient(${item.id})">
                            🗑️ Sil
                        </button>
                    </div>
                </div>
            `;
        });

        container.innerHTML = html;

    } catch (error) {
        console.error('❌ Error loading ingredients:', error);
        const container = document.getElementById('my-ingredients-list');
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">⚠️</div>
                <p>Malzemeler yüklenirken hata oluştu</p>
                <p style="font-size: 0.9em; color: #718096;">${error.message}</p>
            </div>
        `;
    }
}

// Malzeme düzenleme modalını aç
function editIngredient(id, name, miktar, birim) {
    currentEditingIngredient = id;

    document.getElementById('edit-ingredient-name').value = name;
    document.getElementById('edit-ingredient-amount').value = miktar;
    document.getElementById('edit-ingredient-unit').value = birim;

    document.getElementById('edit-ingredient-modal').style.display = 'flex';
}

// Modal'ı kapat
function closeEditModal() {
    document.getElementById('edit-ingredient-modal').style.display = 'none';
    currentEditingIngredient = null;
}

// Güncellemeyi kaydet
async function saveIngredientUpdate() {
    if (!currentEditingIngredient) return;

    const miktar = parseFloat(document.getElementById('edit-ingredient-amount').value);
    const birim = document.getElementById('edit-ingredient-unit').value;

    if (!miktar || miktar <= 0) {
        alert('Lütfen geçerli bir miktar girin');
        return;
    }

    showLoading(true);

    try {
        const response = await fetch(`${API_BASE}/api/malzeme/${currentEditingIngredient}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                miktar: miktar,
                birim: birim
            })
        });

        const data = await response.json();

        if (data.success) {
            alert('✅ Malzeme güncellendi!');
            closeEditModal();
            loadMyIngredients(); // Listeyi yenile
        } else {
            alert('❌ Güncelleme başarısız');
        }

    } catch (error) {
        console.error('Error:', error);
        alert('❌ Hata: ' + error.message);
    } finally {
        showLoading(false);
    }
}

// Modal dışına tıklayınca kapat
document.addEventListener('click', (e) => {
    const modal = document.getElementById('edit-ingredient-modal');
    if (e.target === modal) {
        closeEditModal();
    }
});

// Malzemelerimden tarif öner
function getTarifFromMyIngredients() {
    // TODO: Gerçek malzemeleri al
    currentIngredients = ['domates', 'biber', 'soğan'];
    getTarifOnerisi();
}

// Tarif önerisi al
async function getTarifOnerisi() {
    if (currentIngredients.length === 0) {
        alert('Lütfen en az bir malzeme ekleyin');
        return;
    }
    
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE}/api/tarif/oner`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                malzemeler: currentIngredients
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentRecipe = data.tarif;
            displayRecipe(data.tarif);
            showScreen('recipe-screen');
        } else {
            alert('Tarif önerisi alınamadı');
        }
        
    } catch (error) {
        console.error('Error:', error);
        alert('Bir hata oluştu: ' + error.message);
    } finally {
        showLoading(false);
    }
}

// Tarif göster
function displayRecipe(recipe) {
    const container = document.getElementById('recipe-content');
    
    let malzemelerHtml = '';
    recipe.malzemeler.forEach(m => {
        malzemelerHtml += `<li>${m}</li>`;
    });
    
    let adimlarHtml = '';
    recipe.adimlar.forEach((adim, index) => {
        adimlarHtml += `<li>${adim}</li>`;
    });
    
    container.innerHTML = `
        <h2 class="recipe-title">${recipe.baslik}</h2>
        
        <div class="recipe-meta">
            <span>⏱️ ${recipe.sure} dk</span>
            <span>📊 ${recipe.zorluk}</span>
            <span>🍽️ ${recipe.kategori}</span>
        </div>
        
        <p style="margin-bottom: 20px; color: #4A5568;">${recipe.aciklama}</p>
        
        <div class="recipe-section">
            <h3>🥗 Malzemeler</h3>
            <ul>${malzemelerHtml}</ul>
        </div>
        
        <div class="recipe-section">
            <h3>👨‍🍳 Yapılışı</h3>
            <ol>${adimlarHtml}</ol>
        </div>
        
        <div style="margin-top: 30px;">
            <button class="btn btn-success" onclick="createShoppingList()">
                🛒 Alışveriş Listesi Oluştur
            </button>
        </div>
    `;
}

// Alışveriş listesi oluştur
async function createShoppingList() {
    if (!currentRecipe) {
        console.error('❌ currentRecipe yok!');
        return;
    }

    console.log('🛒 Alışveriş listesi oluşturuluyor...');
    console.log('📋 Current recipe:', currentRecipe);
    console.log('📦 Malzemeler:', currentRecipe.malzemeler);

    showLoading(true);

    try {
        const requestBody = {
            malzemeler: currentRecipe.malzemeler
        };

        console.log('📤 Gönderilen request:', requestBody);

        const response = await fetch(`${API_BASE}/api/alisveris/olustur`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestBody)
        });

        console.log('📥 Response status:', response.status);

        const data = await response.json();
        console.log('📥 Response data:', data);

    if (data.success) {
        if (data.eksik_malzemeler.length === 0) {
            alert('🎉 Harika! Tüm malzemeler evinizde var!');
        } else {
            let message = '✅ Alışveriş listesi oluşturuldu!\n\n';
            message += `📋 ${data.eksik_malzemeler.length} eksik malzeme bulundu.\n\n`;
            message += 'Alışveriş listelerime gitmek ister misiniz?';

            if (confirm(message)) {
                loadShoppingLists();
                showScreen('shopping-lists-screen');
            }
        }
    } else {
            console.error('❌ Backend success:false döndü');
            alert('❌ Alışveriş listesi oluşturulamadı: ' + (data.message || 'Bilinmeyen hata'));
        }

    } catch (error) {
        console.error('❌ Catch bloğunda hata:', error);
        alert('❌ Hata: ' + error.message);
    } finally {
        showLoading(false);
    }
}

// Ayarları yükle
async function loadSettings() {
    try {
        const response = await fetch(`${API_BASE}/api/ayarlar`);
        const data = await response.json();
        
        document.getElementById('ai-mode-select').value = data.ai_mode;
        document.getElementById('ai-quota').textContent = data.ai_quota;
        
        updateAIStatusDisplay(data.ai_mode);
        
    } catch (error) {
        console.error('Error loading settings:', error);
    }
}

// AI modunu güncelle
async function updateAIMode() {
    const mode = document.getElementById('ai-mode-select').value;
    
    try {
        const response = await fetch(`${API_BASE}/api/ayarlar`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ ai_mode: mode })
        });
        
        const data = await response.json();
        
        if (data.success) {
            updateAIStatusDisplay(mode);
            alert('Ayarlar güncellendi!');
        }
        
    } catch (error) {
        console.error('Error:', error);
        alert('Ayarlar güncellenemedi');
    }
}

// AI durum göstergesini güncelle
function updateAIStatusDisplay(mode) {
    const statusElement = document.getElementById('ai-status');
    
    const modeTexts = {
        'auto': '🤖 AI: Aktif',
        'manual': '✍️ AI: Manuel',
        'hybrid': '⚙️ AI: Hibrit',
        'off': '🚫 AI: Kapalı'
    };
    
    statusElement.textContent = modeTexts[mode] || '🤖 AI: Aktif';
}

// Utility functions
function formatDate(date) {
    return new Date(date).toLocaleDateString('tr-TR');
}

// Malzeme silme
async function deleteIngredient(ingredientId) {
    if (!confirm('Bu malzemeyi silmek istediğinizden emin misiniz?')) {
        return;
    }

    showLoading(true);

    try {
        const response = await fetch(`${API_BASE}/api/malzeme/${ingredientId}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (data.success) {
            // Listeyi yenile
            loadMyIngredients();
            alert('Malzeme silindi!');
        }

    } catch (error) {
        console.error('Error:', error);
        alert('Malzeme silinirken hata oluştu');
    } finally {
        showLoading(false);
    }
}

// Global değişken
let currentShoppingListId = null;

// Alışveriş listelerini yükle
async function loadShoppingLists() {
    console.log('🛒 Alışveriş listeleri yükleniyor...');
    showLoading(true);

    try {
        const response = await fetch(`${API_BASE}/api/alisveris/listeler`);
        const data = await response.json();

        const container = document.getElementById('shopping-lists-container');

        if (!data.listeler || data.listeler.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">🛒</div>
                    <p>Henüz alışveriş listeniz yok</p>
                    <p style="font-size: 0.9em; color: #718096;">Tarif önerisi alıp liste oluşturun</p>
                </div>
            `;
            return;
        }

        let html = '';
        data.listeler.forEach(liste => {
            const progress = liste.toplam_urun > 0
                ? (liste.tamamlanan_urun / liste.toplam_urun * 100).toFixed(0)
                : 0;

            const statusClass = liste.durum === 'tamamlandi' ? 'completed' : '';
            const statusBadge = liste.durum === 'tamamlandi'
                ? '<span class="shopping-list-status status-completed">✅ Tamamlandı</span>'
                : '<span class="shopping-list-status status-active">📝 Aktif</span>';

            const tarih = new Date(liste.olusturma_tarihi).toLocaleDateString('tr-TR', {
                day: 'numeric',
                month: 'long',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });

            html += `
                <div class="shopping-list-card ${statusClass}" onclick="loadShoppingDetail(${liste.id})">
                    <div class="shopping-list-header">
                        <div>
                            <div style="font-weight: 600; font-size: 1.1em; margin-bottom: 5px;">
                                ${liste.notlar || 'Alışveriş Listesi'}
                            </div>
                            <div class="shopping-list-date">📅 ${tarih}</div>
                        </div>
                        ${statusBadge}
                    </div>

                    <div class="shopping-list-progress">
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${progress}%"></div>
                        </div>
                    </div>

                    <div class="shopping-list-summary">
                        📦 ${liste.tamamlanan_urun} / ${liste.toplam_urun} ürün alındı
                        ${progress > 0 ? `(${progress}%)` : ''}
                    </div>
                </div>
            `;
        });

        container.innerHTML = html;

    } catch (error) {
        console.error('❌ Error:', error);
        alert('Listeler yüklenirken hata oluştu');
    } finally {
        showLoading(false);
    }
}

// Alışveriş listesi detayını yükle
async function loadShoppingDetail(listeId) {
    currentShoppingListId = listeId;
    console.log(`📋 Liste detayı yükleniyor: ${listeId}`);
    showLoading(true);

    try {
        const response = await fetch(`${API_BASE}/api/alisveris/${listeId}`);
        const data = await response.json();

        if (!data.success) {
            alert('Liste bulunamadı');
            return;
        }

        const liste = data.liste;

        // Header
        const tarih = new Date(liste.olusturma_tarihi).toLocaleDateString('tr-TR', {
            day: 'numeric',
            month: 'long',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });

        const headerContainer = document.getElementById('shopping-detail-header');
        headerContainer.innerHTML = `
            <div class="detail-header-card">
                <h3>${liste.notlar || 'Alışveriş Listesi'}</h3>
                <p style="color: #718096;">📅 ${tarih}</p>
                <p style="color: #718096;">
                    Durum: ${liste.durum === 'tamamlandi' ? '✅ Tamamlandı' : '📝 Aktif'}
                </p>
            </div>
        `;

        // Items
        const itemsContainer = document.getElementById('shopping-detail-items');
        let itemsHtml = '';

        liste.urunler.forEach(urun => {
            const checkedClass = urun.alinma_durumu ? 'checked' : '';
            const checked = urun.alinma_durumu ? 'checked' : '';

            itemsHtml += `
                <div class="shopping-item ${checkedClass}">
                    <input
                        type="checkbox"
                        class="shopping-checkbox"
                        ${checked}
                        onchange="toggleShoppingItem(${urun.id}, this.checked)"
                    >
                    <div class="shopping-item-info">
                        <div class="shopping-item-name">${urun.name}</div>
                        <div class="shopping-item-amount">${urun.miktar} ${urun.birim}</div>
                    </div>
                </div>
            `;
        });

        itemsContainer.innerHTML = itemsHtml;

        // Tamamla butonu
        const completeBtn = document.getElementById('complete-list-btn');
        if (liste.durum === 'tamamlandi') {
            completeBtn.style.display = 'none';
        } else {
            completeBtn.style.display = 'block';
        }

        showScreen('shopping-detail-screen');

    } catch (error) {
        console.error('❌ Error:', error);
        alert('Liste yüklenirken hata oluştu');
    } finally {
        showLoading(false);
    }
}

// Alışveriş ürünü durumunu değiştir
async function toggleShoppingItem(urunId, checked) {
    try {
        const response = await fetch(`${API_BASE}/api/alisveris/urun/${urunId}/durum`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                alinma_durumu: checked
            })
        });

        const data = await response.json();

        if (data.success) {
            // Liste detayını yenile
            loadShoppingDetail(currentShoppingListId);
        }

    } catch (error) {
        console.error('❌ Error:', error);
        alert('Durum güncellenemedi');
    }
}

// Alışverişi tamamla
async function completeShoppingList() {
    if (!currentShoppingListId) return;

    if (!confirm('Bu listeyi tamamlamak istediğinizden emin misiniz?')) {
        return;
    }

    showLoading(true);

    try {
        const response = await fetch(`${API_BASE}/api/alisveris/${currentShoppingListId}/tamamla`, {
            method: 'PUT'
        });

        const data = await response.json();

        if (data.success) {
            alert('✅ Liste tamamlandı!');
            showScreen('shopping-lists-screen');
            loadShoppingLists();
        }

    } catch (error) {
        console.error('❌ Error:', error);
        alert('Liste tamamlanamadı');
    } finally {
        showLoading(false);
    }
}

// Alışveriş listesini sil
async function deleteShoppingList() {
    if (!currentShoppingListId) return;

    if (!confirm('Bu listeyi silmek istediğinizden emin misiniz?')) {
        return;
    }

    showLoading(true);

    try {
        const response = await fetch(`${API_BASE}/api/alisveris/${currentShoppingListId}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (data.success) {
            alert('✅ Liste silindi!');
            showScreen('shopping-lists-screen');
            loadShoppingLists();
        }

    } catch (error) {
        console.error('❌ Error:', error);
        alert('Liste silinemedi');
    } finally {
        showLoading(false);
    }
}

console.log('✅ Tarif-e hazır!');
