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
    updatePhotoUIForDevice();
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
    
    // Butonu gizle ve önceki sonuçları temizle
    document.getElementById('get-recipe-btn').style.display = 'none';
    document.getElementById('detected-ingredients').innerHTML = '';
    currentIngredients = [];

    // AI ile malzeme tanıma
    showLoading(true);

    try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${API_BASE}/api/malzeme/tani`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        console.log('🔍 API Yanıtı:', data);

        // Malzemeleri filtrele - "yok", "bulunmamaktadır" gibi kelimeler içeren cümleleri temizle
        let malzemeler = [];
        if (data.malzemeler && Array.isArray(data.malzemeler)) {
            malzemeler = data.malzemeler.filter(item => {
                const lowerItem = item.toLowerCase();
                // Negatif kelimeler içeriyorsa atla
                const negativeKeywords = [
                    'yok', 'bulunmamaktadır', 'bulunmuyor', 'görünmüyor',
                    'tespit edilemedi', 'tanınamadı', 'herhangi bir', 'hiçbir',
                    'resimde', 'fotoğrafta'
                ];

                const isNegative = negativeKeywords.some(keyword => lowerItem.includes(keyword));
                const isTooShort = item.length < 3;

                return !isNegative && !isTooShort;
            });
        }

        console.log('📦 Filtrelenmiş malzemeler:', malzemeler);
        console.log('🔢 Malzeme sayısı:', malzemeler.length);

        if (malzemeler.length > 0) {
            console.log('✅ Malzeme bulundu');
            currentIngredients = malzemeler;
            displayDetectedIngredients(malzemeler);
        } else {
            console.log('❌ Malzeme bulunamadı');
            currentIngredients = [];
            displayDetectedIngredients([]);
        }

    } catch (error) {
        console.error('❌ Error:', error);
        alert('Bir hata oluştu: ' + error.message);
        currentIngredients = [];
        displayDetectedIngredients([]);
    } finally {
        showLoading(false);
    }
}

// Tanınan malzemeleri göster
function displayDetectedIngredients(ingredients) {
    const container = document.getElementById('detected-ingredients');
    const recipeBtn = document.getElementById('get-recipe-btn');

    console.log('🎨 displayDetectedIngredients çağrıldı');
    console.log('   Gelen ingredients:', ingredients);
    console.log('   Type:', typeof ingredients);
    console.log('   Array mi?', Array.isArray(ingredients));
    console.log('   Length:', ingredients ? ingredients.length : 'null/undefined');

    // Boş, null, undefined veya boş array kontrolü
    if (!ingredients || !Array.isArray(ingredients) || ingredients.length === 0) {
        console.log('❌ Malzeme yok, boş state gösteriliyor');
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">🤷</div>
                <p><strong>Malzeme tanınamadı</strong></p>
                <p style="font-size: 0.9em; color: #718096; margin-top: 10px;">
                    Bu resimde yiyecek malzemesi bulunamadı.<br>
                    Lütfen daha net bir fotoğraf deneyin veya manuel ekleme yapın.
                </p>
            </div>
        `;
        recipeBtn.style.display = 'none';
        console.log('   Buton gizlendi');
        return;
    }

    console.log('✅ Malzemeler var, liste gösteriliyor');
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
    recipeBtn.style.display = 'block';
    console.log('   Buton gösterildi');
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
    
    showLoading(true);

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
            // Formu temizle
            document.getElementById('ingredient-name').value = '';
            document.getElementById('ingredient-amount').value = '1';
            document.getElementById('ingredient-unit').value = 'adet';

            // Manuel malzeme listesini temizle (geçmişi gösterme)
            document.getElementById('manual-ingredients-list').innerHTML = '';

            alert(`✅ ${name} eklendi!`);
        }

    } catch (error) {
        console.error('Error:', error);
        alert('Malzeme eklenirken hata oluştu');
    } finally {
        showLoading(false);
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

async function getTarifOnerisi() {
    showLoading(true);

    try {
        const response = await fetch(`${API_BASE}/api/malzeme/liste`);
        const data = await response.json();

        if (!data.malzemeler || data.malzemeler.length === 0) {
            alert('Lütfen önce malzeme ekleyin');
            showLoading(false);
            return;
        }

        // Sadece malzeme isimlerini al
        const malzemeIsimleri = data.malzemeler.map(m => m.name);
        currentIngredients = malzemeIsimleri;

        console.log('🍽️ Tarif isteniyor, malzemeler:', malzemeIsimleri);

        // Tarif iste
        const tarifResponse = await fetch(`${API_BASE}/api/tarif/oner`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                malzemeler: malzemeIsimleri
            })
        });

        const tarifData = await tarifResponse.json();
        console.log('📖 Tarif geldi:', tarifData);

        if (tarifData.success && tarifData.tarif) {
            currentRecipe = tarifData.tarif;

            // Önce ekranı göster, sonra içeriği doldur
            showScreen('recipe-screen');

            // Biraz bekle ki DOM hazır olsun
            setTimeout(() => {
                displayRecipe(tarifData.tarif);
            }, 100);
        } else {
            alert('❌ Tarif önerilemedi');
        }

    } catch (error) {
        console.error('Error:', error);
        alert('Tarif önerilirken hata oluştu: ' + error.message);
    } finally {
        showLoading(false);
    }
}

// Fotoğraftan tarif öner
async function getRecipeFromPhoto() {
    if (!currentIngredients || currentIngredients.length === 0) {
        alert('Lütfen önce malzeme ekleyin');
        return;
    }

    console.log('🍽️ Tarif öneriliyor, malzemeler:', currentIngredients);
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

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        if (data.success && data.tarif) {
            currentRecipe = data.tarif;
            displayRecipe(data.tarif);
            showScreen('recipe-screen');
        } else {
            alert('❌ Tarif önerilemedi');
        }

    } catch (error) {
        console.error('❌ Error:', error);
        alert('Tarif önerilirken hata oluştu: ' + error.message);
    } finally {
        showLoading(false);
    }
}

// Tarifi göster
function displayRecipe(recipe) {
    console.log('📖 Tarif gösteriliyor:', recipe);

    const container = document.getElementById('recipe-details');

    if (!container) {
        console.error('❌ recipe-details elementi bulunamadı!');
        alert('Tarif ekranı yüklenemedi. Sayfayı yenileyin.');
        return;
    }

    if (!recipe) {
        console.error('❌ Recipe objesi boş!');
        container.innerHTML = '<p>Tarif yüklenemedi</p>';
        return;
    }

    // Malzemeler
    let malzemelerHtml = '<h3>📋 Malzemeler:</h3><ul>';
    if (recipe.malzemeler && Array.isArray(recipe.malzemeler)) {
        recipe.malzemeler.forEach(malzeme => {
            malzemelerHtml += `<li>${malzeme}</li>`;
        });
    }
    malzemelerHtml += '</ul>';

    // Adımlar
    let adimlarHtml = '<h3>👨‍🍳 Hazırlanışı:</h3><ol>';
    if (recipe.adimlar && Array.isArray(recipe.adimlar)) {
        recipe.adimlar.forEach(adim => {
            adimlarHtml += `<li>${adim}</li>`;
        });
    }
    adimlarHtml += '</ol>';

    // Bilgiler
    const sure = recipe.sure ? `⏱️ ${recipe.sure} dakika` : '';
    const zorluk = recipe.zorluk ? `📊 ${recipe.zorluk}` : '';

    container.innerHTML = `
        <div class="recipe-card">
            <h2>${recipe.baslik || 'Tarif'}</h2>
            <p class="recipe-description">${recipe.aciklama || ''}</p>
            <div class="recipe-meta">
                ${sure ? `<span>${sure}</span>` : ''}
                ${zorluk ? `<span>${zorluk}</span>` : ''}
            </div>
            ${malzemelerHtml}
            ${adimlarHtml}
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
    
    showLoading(true);

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
            alert('✅ Ayarlar güncellendi!');
        } else {
            alert('❌ Ayarlar güncellenemedi');
        }

    } catch (error) {
        console.error('Error:', error);
        alert('❌ Ayarlar güncellenemedi: ' + error.message);
    } finally {
        showLoading(false);
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
        const isTamamlandi = liste.durum === 'tamamlandi';

        console.log(`Liste durumu: ${liste.durum}, Tamamlandı mı: ${isTamamlandi}`);

        // Header
        const tarih = new Date(liste.olusturma_tarihi).toLocaleDateString('tr-TR', {
            day: 'numeric',
            month: 'long',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });

        // Dinamik sayılar
        const toplamUrun = liste.urunler.length;
        const alinanUrun = liste.urunler.filter(u => u.alinma_durumu).length;
        const kalanUrun = toplamUrun - alinanUrun;

        const headerContainer = document.getElementById('shopping-detail-header');
        headerContainer.innerHTML = `
            <div class="detail-header-card">
                <h3>🛒 Alışveriş Listesi</h3>
                <p style="color: #718096; margin: 8px 0;">📅 ${tarih}</p>
                <p style="color: #718096; margin: 8px 0;">
                    Durum: ${isTamamlandi ? '✅ Tamamlandı' : '📝 Aktif'}
                </p>
                <div style="margin-top: 15px; padding: 12px; background: ${isTamamlandi ? '#C6F6D5' : '#EDF2F7'}; border-radius: 8px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                        <span>📦 Toplam ürün:</span>
                        <strong>${toplamUrun}</strong>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                        <span>✅ Alınan:</span>
                        <strong style="color: #48BB78;">${alinanUrun}</strong>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span>⏳ Kalan:</span>
                        <strong style="color: #F6AD55;">${kalanUrun}</strong>
                    </div>
                </div>
            </div>
        `;

        // Items
        const itemsContainer = document.getElementById('shopping-detail-items');

        if (toplamUrun === 0) {
            itemsContainer.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">📭</div>
                    <p>Liste boş</p>
                    ${!isTamamlandi ? '<p style="font-size: 0.9em; color: #718096;">➕ Ürün Ekle butonuyla malzeme ekleyin</p>' : ''}
                </div>
            `;
        } else {
            let itemsHtml = '';

            liste.urunler.forEach(urun => {
                const checkedClass = urun.alinma_durumu ? 'checked' : '';
                const checked = urun.alinma_durumu ? 'checked' : '';
                const disabled = isTamamlandi ? 'disabled' : '';

                itemsHtml += `
                    <div class="shopping-item ${checkedClass}">
                        <input
                            type="checkbox"
                            class="shopping-checkbox"
                            ${checked}
                            ${disabled}
                            onchange="toggleShoppingItem(${urun.id}, this.checked)"
                        >
                        <div class="shopping-item-info">
                            <div class="shopping-item-name">${urun.name}</div>
                            <div class="shopping-item-amount">${urun.miktar} ${urun.birim}</div>
                        </div>
                        ${!isTamamlandi ? `
                            <button
                                class="btn-icon-delete"
                                onclick="deleteShoppingItem(${urun.id})"
                                title="Sil"
                            >
                                🗑️
                            </button>
                        ` : ''}
                    </div>
                `;
            });

            itemsContainer.innerHTML = itemsHtml;
        }

        // Butonları göster/gizle
        const addBtn = document.querySelector('button[onclick="showAddItemModal()"]');
        const completeBtn = document.getElementById('complete-list-btn');

        if (isTamamlandi) {
            // Tamamlanmış listede sadece silme butonu görünsün
            if (addBtn) addBtn.style.display = 'none';
            if (completeBtn) completeBtn.style.display = 'none';
            console.log('🔒 Liste tamamlanmış, düzenleme butonları gizlendi');
        } else {
            // Aktif listede tüm butonlar görünsün
            if (addBtn) addBtn.style.display = 'block';
            if (completeBtn) completeBtn.style.display = toplamUrun > 0 ? 'block' : 'none';
            console.log('✅ Liste aktif, düzenleme butonları gösteriliyor');
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
    console.log('=' .repeat(50));
    console.log(`📦 Ürün durumu değiştiriliyor`);
    console.log(`   Ürün ID: ${urunId}`);
    console.log(`   Yeni durum: ${checked}`);

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

        console.log(`   Response status: ${response.status}`);

        const data = await response.json();
        console.log(`   Response data:`, data);

        if (data.success) {
            console.log('✅ Durum güncellendi, sayfa yenileniyor...');
            // Liste detayını yenile
            await loadShoppingDetail(currentShoppingListId);
            console.log('✅ Sayfa yenilendi');
        } else {
            console.error('❌ Backend success:false döndü');
            alert('Durum güncellenemedi');
        }

    } catch (error) {
        console.error('❌ Error:', error);
        alert('Durum güncellenemedi: ' + error.message);
    }
    console.log('=' .repeat(50));
}

async function updateShoppingListHeader(listeId) {
    const response = await fetch(`${API_BASE}/api/alisveris/${listeId}`);
    const data = await response.json();

    if (data.success) {
        const liste = data.liste;
        const toplamUrun = liste.urunler.length;
        const alinanUrun = liste.urunler.filter(u => u.alinma_durumu).length;
        const kalanUrun = toplamUrun - alinanUrun;

        // Sadece sayıları güncelle
        const headerContainer = document.getElementById('shopping-detail-header');
        const tarih = new Date(liste.olusturma_tarihi).toLocaleDateString('tr-TR', {
            day: 'numeric',
            month: 'long',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });

        headerContainer.innerHTML = `
            <div class="detail-header-card">
                <h3>🛒 Alışveriş Listesi</h3>
                <p style="color: #718096; margin: 8px 0;">📅 ${tarih}</p>
                <p style="color: #718096; margin: 8px 0;">
                    Durum: ${liste.durum === 'tamamlandi' ? '✅ Tamamlandı' : '📝 Aktif'}
                </p>
                <div style="margin-top: 15px; padding: 12px; background: #EDF2F7; border-radius: 8px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                        <span>📦 Toplam ürün:</span>
                        <strong>${toplamUrun}</strong>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                        <span>✅ Alınan:</span>
                        <strong style="color: #48BB78;">${alinanUrun}</strong>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span>⏳ Kalan:</span>
                        <strong style="color: #F6AD55;">${kalanUrun}</strong>
                    </div>
                </div>
            </div>
        `;
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

// Mobil cihaz kontrolü
function isMobileDevice() {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
}

// Dokunmatik ekran kontrolü (tablet'ler için)
function isTouchDevice() {
    return ('ontouchstart' in window) || (navigator.maxTouchPoints > 0);
}

// Gerçekten fotoğraf çekebilir mi kontrolü
function canCapturePhoto() {
    return isMobileDevice() && navigator.mediaDevices && navigator.mediaDevices.getUserMedia;
}

// UI'ı cihaza göre güncelle
function updatePhotoUIForDevice() {
    const isMobile = canCapturePhoto();
    const icon = isMobile ? '📷' : '📁';
    const text = isMobile ? 'Fotoğraf Çek' : 'Fotoğraf Yükle';

    // Ana menü butonu
    const menuIcon = document.getElementById('photo-icon');
    const menuText = document.getElementById('photo-text');
    if (menuIcon) menuIcon.textContent = icon;
    if (menuText) menuText.textContent = text;

    // Kamera ekranı başlığı
    const title = document.getElementById('camera-screen-title');
    if (title) title.textContent = `${icon} ${text}`;

    // Kamera butonu
    const labelIcon = document.getElementById('camera-label-icon');
    const labelText = document.getElementById('camera-label-text');
    if (labelIcon) labelIcon.textContent = icon;
    if (labelText) labelText.textContent = text;

    // Input capture attribute'unu ayarla
    const photoInput = document.getElementById('photo-input');
    if (photoInput) {
        if (isMobile) {
            photoInput.setAttribute('capture', 'environment');
        } else {
            photoInput.removeAttribute('capture');
        }
    }

    console.log(`📱 Cihaz tipi: ${isMobile ? 'Mobil (fotoğraf çek)' : 'Masaüstü (dosya yükle)'}`);
}

// Sayfa yüklendiğinde çalıştır
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Uygulama başlatılıyor...');
    updatePhotoUIForDevice();
    loadSettings();
});

// Pencere boyutu değiştiğinde güncelle (responsive)
window.addEventListener('resize', () => {
    updatePhotoUIForDevice();
});

// Ürün ekleme modalını aç
function showAddItemModal() {
    if (!currentShoppingListId) return;

    // Formu temizle
    document.getElementById('add-item-name').value = '';
    document.getElementById('add-item-amount').value = '1';
    document.getElementById('add-item-unit').value = 'adet';

    document.getElementById('add-item-modal').style.display = 'flex';
}

// Ürün ekleme modalını kapat
function closeAddItemModal() {
    document.getElementById('add-item-modal').style.display = 'none';
}

// Alışveriş listesine ürün ekle
async function addItemToShoppingList() {
    if (!currentShoppingListId) return;

    const malzeme_adi = document.getElementById('add-item-name').value.trim();
    const miktar = parseFloat(document.getElementById('add-item-amount').value);
    const birim = document.getElementById('add-item-unit').value;

    if (!malzeme_adi) {
        alert('Lütfen malzeme adı girin');
        return;
    }

    if (!miktar || miktar <= 0) {
        alert('Lütfen geçerli bir miktar girin');
        return;
    }

    showLoading(true);

    try {
        const response = await fetch(`${API_BASE}/api/alisveris/${currentShoppingListId}/urun`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                malzeme_adi: malzeme_adi,
                miktar: miktar,
                birim: birim
            })
        });

        const data = await response.json();

        if (data.success) {
            alert('✅ Ürün eklendi!');
            closeAddItemModal();
            loadShoppingDetail(currentShoppingListId);
        } else {
            alert('❌ Ürün eklenemedi');
        }

    } catch (error) {
        console.error('Error:', error);
        alert('❌ Hata: ' + error.message);
    } finally {
        showLoading(false);
    }
}

// Alışveriş listesinden ürün sil
async function deleteShoppingItem(urunId) {
    if (!confirm('Bu ürünü listeden silmek istediğinizden emin misiniz?')) {
        return;
    }

    showLoading(true);

    try {
        const response = await fetch(`${API_BASE}/api/alisveris/urun/${urunId}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (data.success) {
            // Liste detayını yenile
            loadShoppingDetail(currentShoppingListId);
        } else {
            alert('❌ Ürün silinemedi');
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
    const editModal = document.getElementById('edit-ingredient-modal');
    const addModal = document.getElementById('add-item-modal');

    if (e.target === editModal) {
        closeEditModal();
    }
    if (e.target === addModal) {
        closeAddItemModal();
    }
});

// Yeni tarif öner (aynı malzemelerle)
async function getNewRecipe() {
    if (!currentIngredients || currentIngredients.length === 0) {
        alert('Malzeme bilgisi bulunamadı');
        return;
    }

    if (!confirm('Aynı malzemelerle yeni bir tarif önerilsin mi?')) {
        return;
    }

    console.log('🔄 Yeni tarif öneriliyor, malzemeler:', currentIngredients);
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

        if (data.success && data.tarif) {
            currentRecipe = data.tarif;
            displayRecipe(data.tarif);
            alert('✅ Yeni tarif önerildi!');
        } else {
            alert('❌ Yeni tarif önerilemedi');
        }

    } catch (error) {
        console.error('Error:', error);
        alert('Tarif önerilirken hata oluştu');
    } finally {
        showLoading(false);
    }
}

// Tarifi favorilere ekle
async function addRecipeToFavorites() {
    if (!currentRecipe) {
        alert('Önce bir tarif seçin');
        return;
    }

    console.log('⭐ Tarif favorilere ekleniyor:', currentRecipe);
    showLoading(true);

    try {
        const response = await fetch(`${API_BASE}/api/favoriler/ekle`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                tarif: currentRecipe
            })
        });

        const data = await response.json();

        if (data.success) {
            alert('⭐ Tarif favorilere eklendi!');
        } else {
            alert('❌ Tarif eklenemedi');
        }

    } catch (error) {
        console.error('Error:', error);
        alert('Tarif eklenirken hata oluştu');
    } finally {
        showLoading(false);
    }
}

// Global değişken
let currentFavoriteId = null;

// Favori tarifleri yükle
async function loadFavorites() {
    console.log('⭐ Favori tarifler yükleniyor...');
    showLoading(true);

    try {
        const response = await fetch(`${API_BASE}/api/favoriler/liste`);
        const data = await response.json();

        const container = document.getElementById('favorites-container');

        if (!data.favoriler || data.favoriler.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">⭐</div>
                    <p>Henüz favori tarifiniz yok</p>
                    <p style="font-size: 0.9em; color: #718096;">
                        Beğendiğiniz tarifleri favorilere ekleyin
                    </p>
                </div>
            `;
            return;
        }

        let html = '';
        data.favoriler.forEach(fav => {
            const tarih = new Date(fav.eklenme_tarihi).toLocaleDateString('tr-TR', {
                day: 'numeric',
                month: 'long',
                year: 'numeric'
            });

            const sure = fav.sure ? `⏱️ ${fav.sure} dk` : '';
            const zorluk = fav.zorluk ? `📊 ${fav.zorluk}` : '';
            const malzemeSayisi = fav.malzemeler ? `📋 ${fav.malzemeler.length} malzeme` : '';

            html += `
                <div class="favorite-card" onclick="loadFavoriteDetail(${fav.id})">
                    <div class="favorite-card-header">
                        <div style="flex: 1;">
                            <div class="favorite-card-title">${fav.baslik}</div>
                            <div class="favorite-card-date">⭐ ${tarih}</div>
                        </div>
                    </div>

                    ${fav.aciklama ? `
                        <div class="favorite-card-description">${fav.aciklama}</div>
                    ` : ''}

                    <div class="favorite-card-meta">
                        ${malzemeSayisi ? `<span class="favorite-card-badge">${malzemeSayisi}</span>` : ''}
                        ${sure ? `<span class="favorite-card-badge">${sure}</span>` : ''}
                        ${zorluk ? `<span class="favorite-card-badge">${zorluk}</span>` : ''}
                    </div>
                </div>
            `;
        });

        container.innerHTML = html;

    } catch (error) {
        console.error('❌ Error:', error);
        alert('Favoriler yüklenirken hata oluştu');
    } finally {
        showLoading(false);
    }
}

// Favori tarif detayını göster
async function loadFavoriteDetail(favoriId) {
    currentFavoriteId = favoriId;
    console.log(`📖 Favori tarif detayı yükleniyor: ${favoriId}`);
    showLoading(true);

    try {
        const response = await fetch(`${API_BASE}/api/favoriler/${favoriId}`);
        const data = await response.json();

        if (!data.favoriler) {
            alert('Tarif bulunamadı');
            return;
        }

        const favori = data.favoriler.find(f => f.id === favoriId);

        if (!favori) {
            alert('Tarif bulunamadı');
            return;
        }

        // Tarifi göster
        const container = document.getElementById('favorite-recipe-details');

        // Malzemeler
        let malzemelerHtml = '<h3>📋 Malzemeler:</h3><ul>';
        if (favori.malzemeler && Array.isArray(favori.malzemeler)) {
            favori.malzemeler.forEach(malzeme => {
                malzemelerHtml += `<li>${malzeme}</li>`;
            });
        }
        malzemelerHtml += '</ul>';

        // Adımlar
        let adimlarHtml = '<h3>👨‍🍳 Hazırlanışı:</h3><ol>';
        if (favori.adimlar && Array.isArray(favori.adimlar)) {
            favori.adimlar.forEach(adim => {
                adimlarHtml += `<li>${adim}</li>`;
            });
        }
        adimlarHtml += '</ol>';

        const sure = favori.sure ? `⏱️ ${favori.sure} dakika` : '';
        const zorluk = favori.zorluk ? `📊 ${favori.zorluk}` : '';

        container.innerHTML = `
            <div class="recipe-card">
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
                    <h2 style="margin: 0;">${favori.baslik}</h2>
                    <span style="font-size: 1.5em;">⭐</span>
                </div>
                ${favori.aciklama ? `<p class="recipe-description">${favori.aciklama}</p>` : ''}
                <div class="recipe-meta">
                    ${sure ? `<span>${sure}</span>` : ''}
                    ${zorluk ? `<span>${zorluk}</span>` : ''}
                </div>
                ${malzemelerHtml}
                ${adimlarHtml}
            </div>
        `;

        // currentRecipe'yi set et (alışveriş listesi için)
        currentRecipe = favori;

        showScreen('favorite-detail-screen');

    } catch (error) {
        console.error('❌ Error:', error);
        alert('Tarif yüklenirken hata oluştu');
    } finally {
        showLoading(false);
    }
}

// Favoriden alışveriş listesi oluştur
async function createShoppingListFromFavorite() {
    if (!currentRecipe) {
        alert('Tarif bilgisi bulunamadı');
        return;
    }

    // Mevcut createShoppingList fonksiyonunu kullan
    await createShoppingList();
}

// Favori tarifi sil
async function deleteFavoriteRecipe() {
    if (!currentFavoriteId) return;

    if (!confirm('Bu tarifi favorilerden çıkarmak istediğinizden emin misiniz?')) {
        return;
    }

    showLoading(true);

    try {
        const response = await fetch(`${API_BASE}/api/tarif/favoriler/${currentFavoriteId}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (data.success) {
            alert('✅ Tarif favorilerden çıkarıldı!');
            showScreen('favorites-screen');
            loadFavorites();
        } else {
            alert('❌ Tarif silinemedi');
        }

    } catch (error) {
        console.error('❌ Error:', error);
        alert('Tarif silinirken hata oluştu');
    } finally {
        showLoading(false);
    }
}

console.log('✅ Tarif-e hazır!');
