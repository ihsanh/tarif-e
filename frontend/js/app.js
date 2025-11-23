// Tarif-e JavaScript

// ============================================
// AKıLLI NAVİGASYON SİSTEMİ
// ============================================

let screenHistory = ['main-menu'];

// Orijinal showScreen'i kaydet
const originalShowScreen = showScreen;

// showScreen'i override et
function showScreen(screenId) {
    const currentScreen = document.querySelector('.screen.active')?.id;

    // Geçmişe ekle
    if (currentScreen && currentScreen !== screenId && screenId !== 'main-menu') {
        if (screenHistory[screenHistory.length - 1] !== currentScreen) {
            screenHistory.push(currentScreen);
        }
    }

    // Ana menüye gidince geçmişi temizle
    if (screenId === 'main-menu') {
        screenHistory = ['main-menu'];
    }

    // Orijinal fonksiyonu çağır
    originalShowScreen(screenId);
}

// Geri dönüş fonksiyonu
function goBack() {
    if (screenHistory.length > 1) {
        screenHistory.pop(); // Mevcut ekranı çıkar
        const previousScreen = screenHistory[screenHistory.length - 1];

        // Direkt geçiş yap (geçmişe tekrar eklenmemesi için)
        document.querySelectorAll('.screen').forEach(screen => {
            screen.classList.remove('active');
        });
        document.getElementById(previousScreen)?.classList.add('active');
    } else {
        showScreen('main-menu');
    }
}

console.log('✅ Akıllı navigasyon sistemi yüklendi');

// SAYFA YÜKLENİRKEN HEMEN KONTROL ET
(function() {
    const token = localStorage.getItem('access_token');
    const path = window.location.pathname;

    console.log('🔍 İlk kontrol - Path:', path, 'Token:', token ? 'VAR' : 'YOK');

    // Login sayfasında app.js çalışmasın
    if (path.includes('login.html')) {
        console.log('🔓 Login sayfası, app.js iptal edildi');
        return;
    }

    // Token yoksa login'e git
    if (!token) {
        console.log('❌ Token yok, login\'e gidiyor...');
        window.location.href = '/login.html';
    }
})();

// API Base URL
const API_BASE = window.location.origin;

// Global state
let currentIngredients = [];
let currentRecipe = null;

// ============================================
// AUTH & TOKEN MANAGEMENT
// ============================================

// Token helper
function getToken() {
    return localStorage.getItem('access_token');
}

// Fetch with authentication
async function fetchWithAuth(url, options = {}) {
    const token = getToken();

    if (!token) {
        console.error('❌ Token yok!');
        window.location.href = '/login.html';
        throw new Error('No token');
    }

    // Headers ekle
    options.headers = {
        ...options.headers,
        'Authorization': `Bearer ${token}`
    };

    const response = await fetch(url, options);

    // 401 Unauthorized - Token geçersiz veya süresi dolmuş
    if (response.status === 401) {
        console.error('❌ Token geçersiz, logout yapılıyor...');
        handleLogout(false); // confirm olmadan direkt logout
        throw new Error('Unauthorized');
    }

    return response;
}

// Logout fonksiyonu
window.handleLogout = async function handleLogout(confirm = true) {
    if (confirm) {
        const confirmLogout = window.confirm('Çıkış yapmak istediğinize emin misiniz?');
        if (!confirmLogout) return;
    }

    const loadingEl = document.getElementById('loading');
    if (loadingEl) loadingEl.style.display = 'flex';

    try {
        // Backend'e logout isteği (opsiyonel)
        const token = getToken();
        if (token) {
            await fetchWithAuth(`${API_BASE}/api/auth/logout`, {
                method: 'POST'
            }).catch(() => {}); // Hata olsa da devam et
        }
    } finally {
        // Token'ları temizle
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');

        console.log('👋 Logout başarılı');

        // Login sayfasına yönlendir
        window.location.href = '/login.html';
    }
}

// Kullanıcı bilgisini göster
function displayUserInfo() {
    const userStr = localStorage.getItem('user');
    if (!userStr) return;

    try {
        const user = JSON.parse(userStr);
        console.log('👤 Giriş yapannnnnn:', user.username, '(' + user.email + ')');

        // UI'da göster (element varsa)
        const userDisplay = document.getElementById('user-display');
        if (userDisplay) {
            userDisplay.textContent = `Merhaba, ${user.username}!`;
        }
    } catch (e) {
        console.error('User parse error:', e);
    }
}

// ============================================
// APP INITIALIZATION
// ============================================

// Sayfa yüklendiğinde
document.addEventListener('DOMContentLoaded', () => {
    const currentPath = window.location.pathname;

    console.log('📍 Sayfa:', currentPath);

    // Login sayfasındaysa app.js'i yükleme
    if (currentPath.includes('login.html')) {
        console.log('🔓 Login sayfası, app.js atlandı');
        return;
    }

    // Token kontrolü - küçük gecikme ile
    setTimeout(() => {
        const token = getToken();

        console.log('🔐 Token kontrolü:', token ? 'Var ✅' : 'Yok ❌');

        if (!token) {
            console.log('❌ Token yok, login\'e yönlendiriliyor...');
            window.location.href = '/login.html';
            return;
        }

        // Token OK, app başlat
        console.log('✅ Auth OK, sayfa yükleniyor...');
        console.log('🍳 Tarif-e başlatılıyor...!!!!!!!!!');

        // Kullanıcı bilgisini göster
        displayUserInfo();

        // Diğer başlangıç işlemleri
        loadMyIngredients();
        updatePhotoUIForDevice();
        loadSettings();

        // Fotoğraf seçildiğinde
        const photoInput = document.getElementById('photo-input');
        if (photoInput) {
            photoInput.addEventListener('change', handlePhotoSelect);
        }
    }, 100); // 100ms gecikme - localStorage'ın flush olmasını bekle
});

// ============================================
// UTILITY FUNCTIONS
// ============================================

function showScreen(screenId) {
    document.querySelectorAll('.screen').forEach(screen => {
        screen.classList.remove('active');
    });

    document.getElementById(screenId).classList.add('active');

    if (screenId === 'my-ingredients-screen') {
        loadMyIngredients();
    }
}

function showLoading(show = true) {
    const loadingEl = document.getElementById('loading');
    if (loadingEl) {
        loadingEl.style.display = show ? 'flex' : 'none';
    }
}

// ============================================
// PHOTO HANDLING
// ============================================

async function handlePhotoSelect(event) {
    const file = event.target.files[0];
    if (!file) return;

    // Önizleme göster
    const reader = new FileReader();
    reader.onload = (e) => {
        const preview = document.getElementById('photo-preview');
        if (preview) {
            preview.innerHTML = `<img src="${e.target.result}" alt="Seçilen fotoğraf">`;
        }
    };
    reader.readAsDataURL(file);

    // Butonu gizle ve önceki sonuçları temizle
    const getRecipeBtn = document.getElementById('get-recipe-btn');
    if (getRecipeBtn) getRecipeBtn.style.display = 'none';

    const detectedIngredients = document.getElementById('detected-ingredients');
    if (detectedIngredients) detectedIngredients.innerHTML = '';

    currentIngredients = [];

    // AI ile malzeme tanıma
    showLoading(true);

    try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetchWithAuth(`${API_BASE}/api/malzeme/tani`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log('🔍 AI Yanıtı:', data);

        // Malzemeleri filtrele
        let malzemeler = [];
        if (data.malzemeler && Array.isArray(data.malzemeler)) {
            malzemeler = data.malzemeler.filter(item => {
                const lowerItem = item.toLowerCase();
                const negativeKeywords = [
                    'yok', 'bulunmamaktadır', 'bulunmuyor', 'görünmüyor',
                    'tespit edilemedi', 'tanınamadı', 'herhangi bir', 'hiçbir',
                    'resimde', 'fotoğrafta'
                ];
                return !negativeKeywords.some(keyword => lowerItem.includes(keyword));
            });
        }

        if (malzemeler.length > 0) {
            currentIngredients = malzemeler;
            displayDetectedIngredients(malzemeler);
            if (getRecipeBtn) getRecipeBtn.style.display = 'block';
        } else {
            alert('❌ Fotoğrafta malzeme tespit edilemedi. Lütfen daha net bir fotoğraf çekin.');
        }

    } catch (error) {
        console.error('❌ Error:', error);
        if (error.message !== 'Unauthorized') {
            alert('Malzeme tanıma sırasında hata oluştu: ' + error.message);
        }
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

        const response = await fetchWithAuth(`${API_BASE}/api/malzeme/ekle`, {
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

        const response = await fetchWithAuth(`${API_BASE}/api/malzeme/liste`, {
            headers: {

            }
        });

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

        const response = await fetchWithAuth(`${API_BASE}/api/malzeme/${currentEditingIngredient}`, {
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

        const response = await fetchWithAuth(`${API_BASE}/api/malzeme/liste`, {
            headers: {

            }
        });
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

        const tarifResponse = await fetchWithAuth(`${API_BASE}/api/tarif/oner`, {
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

        const response = await fetchWithAuth(`${API_BASE}/api/tarif/oner`, {
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
    console.log('🛒 Alışveriş listesi oluşturuluyor...');

    try {
        const currentRecipe = getCurrentRecipe();

        if (!currentRecipe?.malzemeler?.length) {
            showNotification('Tarif bilgisi bulunamadı', 'error');
            return;
        }

        // Malzemeleri formatla: "Patates: 2 adet" → "patates - 2 adet"
        const malzemeler = currentRecipe.malzemeler.map(m => {
            const parts = m.split(':');
            if (parts.length >= 2) {
                const adi = parts[0].trim().toLowerCase();
                const miktar = parts[1].replace(/\(.*?\)/g, '').trim();
                return `${adi} - ${miktar}`;
            }
            return m.toLowerCase();
        });

        // Backend'e gönder
        const response = await fetchWithAuth('/api/alisveris/olustur', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                baslik: currentRecipe.baslik,
                malzemeler: malzemeler
            })
        });

        const data = await response.json();

        if (response.ok && data.success) {
            // Başarılı
            if (data.eksik_malzemeler?.length > 0) {
                const eksikler = data.eksik_malzemeler
                    .map(m => `${m.malzeme}: ${m.gereken} (${m.mevcut} mevcut)`)
                    .join('\n');
                showNotification(`✅ Liste oluşturuldu!\n\n⚠️ Eksik:\n${eksikler}`, 'warning', 5000);
            } else {
                showNotification('✅ Liste oluşturuldu! Tüm malzemeler mevcut!', 'success');
            }
            // Liste oluşturuldu, alışveriş ekranına git
            loadShoppingLists();
            showScreen('shopping-lists-screen');
        } else {
            showNotification(data.message || 'Hata oluştu', 'error');
        }

    } catch (error) {
        console.error('Hata:', error);
        showNotification('Liste oluşturulamadı', 'error');
    }
}

/**
 * Şu anda görüntülenen tarifin bilgilerini al
 */
function getCurrentRecipe() {
    // currentRecipe global değişkenini kullan
    if (!currentRecipe) {
        console.error('❌ currentRecipe bulunamadı');
        return null;
    }

    return currentRecipe;
}

// Modal kapatma fonksiyonu artık gerekli değil - ekran sistemi kullanıyoruz

function showNotification(message, type = 'info', duration = 3000) {
    const existing = document.querySelector('.notification');
    if (existing) existing.remove();

    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed; top: 20px; right: 20px;
        padding: 15px 20px;
        background: ${type === 'success' ? '#4CAF50' : type === 'error' ? '#f44336' : type === 'warning' ? '#ff9800' : '#2196F3'};
        color: white; border-radius: 4px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.3);
        z-index: 10000; max-width: 400px;
        white-space: pre-line;
    `;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transition = 'opacity 0.3s';
        setTimeout(() => notification.remove(), 300);
    }, duration);
}

// Ayarları yükle
async function loadSettings() {
    try {

        const response = await fetchWithAuth(`${API_BASE}/api/ayarlar`);
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

        const response = await fetchWithAuth(`${API_BASE}/api/ayarlar`, {
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

        const response = await fetchWithAuth(`${API_BASE}/api/malzeme/${ingredientId}`, {
            method: 'DELETE',
            headers: {

            }
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

        const response = await fetchWithAuth(`${API_BASE}/api/alisveris/listeler`, {
            headers: {

            }
        });
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

            const statusClass = liste.tamamlandi ? 'completed' : '';
            const statusBadge = liste.tamamlandi
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
                                ${liste.baslik || 'Alışveriş Listesi'}
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

        const response = await fetchWithAuth(`${API_BASE}/api/alisveris/${listeId}`, {
            headers: {

            }
        });
        const data = await response.json();

        if (!data.success) {
            alert('Liste bulunamadı');
            return;
        }

        const liste = data.liste;
        const isTamamlandi = liste.tamamlandi;

        console.log(`Liste durumu: ${liste.tamamlandi ? 'Tamamlandı' : 'Aktif'}, Tamamlandı mı: ${isTamamlandi}`);

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

        const response = await fetchWithAuth(`${API_BASE}/api/alisveris/urun/${urunId}/durum`, {
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

    const response = await fetchWithAuth(`${API_BASE}/api/alisveris/${listeId}`, {
        headers: {
             // YENİ
        }
    });
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
                    Durum: ${liste.tamamlandi ? '✅ Tamamlandı' : '📝 Aktif'}
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

        const response = await fetchWithAuth(`${API_BASE}/api/alisveris/${currentShoppingListId}/tamamla`, {
            method: 'PUT',
            headers: {

            }
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

        const response = await fetchWithAuth(`${API_BASE}/api/alisveris/${currentShoppingListId}`, {
            method: 'DELETE',
            headers: {

            }
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

        const response = await fetchWithAuth(`${API_BASE}/api/alisveris/${currentShoppingListId}/urun`, {
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

        const response = await fetchWithAuth(`${API_BASE}/api/alisveris/urun/${urunId}`, {
            method: 'DELETE',
            headers: {

            }
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

        const response = await fetchWithAuth(`${API_BASE}/api/tarif/oner`, {
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

        const response = await fetchWithAuth(`${API_BASE}/api/favoriler/ekle`, {
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

        const response = await fetchWithAuth(`${API_BASE}/api/favoriler/liste`, {
            headers: {

            }
        });
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

async function loadFavoriteDetail(favoriId) {
    currentFavoriteId = favoriId;
    console.log(`📖 Favori tarif detayı yükleniyor: ${favoriId}`);
    showLoading(true);

    try {

        const response = await fetchWithAuth(`${API_BASE}/api/favoriler/${favoriId}`, {
            headers: {

            }
        });

        // HTTP hata kontrolü
        if (!response.ok) {
            console.error(`❌ HTTP Error: ${response.status} ${response.statusText}`);
            if (response.status === 404) {
                alert('Tarif bulunamadı');
            } else if (response.status === 500) {
                alert('Sunucu hatası oluştu');
            } else {
                alert(`Hata: ${response.status}`);
            }
            return;
        }

        const data = await response.json();
        console.log('📦 Backend response:', data);

        if (!data || !data.success || !data.favori) {
            console.error('❌ Geçersiz response:', data);
            alert('Tarif bulunamadı');
            return;
        }

        const favori = data.favori;

        // Tarifi göster
        const container = document.getElementById('favorite-recipe-details');

        // Malzemeler
        let malzemelerHtml = '<h3>📋 Malzemeler:</h3><ul>';
        if (favori.malzemeler && Array.isArray(favori.malzemeler)) {
            favori.malzemeler.forEach(malzeme => {
                malzemelerHtml += `<li>${malzeme}</li>`;
            });
        } else {
            malzemelerHtml += '<li>Malzeme bilgisi yok</li>';
        }
        malzemelerHtml += '</ul>';

        // Adımlar
        let adimlarHtml = '<h3>👨‍🍳 Hazırlanışı:</h3><ol>';
        if (favori.adimlar && Array.isArray(favori.adimlar)) {
            favori.adimlar.forEach(adim => {
                adimlarHtml += `<li>${adim}</li>`;
            });
        } else {
            adimlarHtml += '<li>Hazırlanış bilgisi yok</li>';
        }
        adimlarHtml += '</ol>';

        const sure = favori.sure ? `⏱️ ${favori.sure} dakika` : '';
        const zorluk = favori.zorluk ? `📊 ${favori.zorluk}` : '';

        container.innerHTML = `
            <div class="recipe-card">
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
                    <h2 style="margin: 0;">${favori.baslik || 'İsimsiz Tarif'}</h2>
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
        console.error('❌ Favori detay hatası:', error);
        console.error('❌ Hata detayı:', error.message);
        alert('Tarif yüklenirken hata oluştu: ' + error.message);
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

        const response = await fetchWithAuth(`${API_BASE}/api/tarif/favoriler/${currentFavoriteId}`, {
            method: 'DELETE',
            headers: {

            }
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

// ============================================
// PAYLAŞIM FONKSİYONLARI
// ============================================

// Paylaşım modalını aç
function showShareModal(listeId) {
    currentShoppingListId = listeId;
    document.getElementById('share-email-input').value = '';
    document.getElementById('share-role-select').value = 'view';
    document.getElementById('share-modal').style.display = 'flex';
    loadShareInfo(listeId);
}

// Paylaşım modalını kapat
function closeShareModal() {
    document.getElementById('share-modal').style.display = 'none';
}

// Liste paylaş
async function shareList() {
    const email = document.getElementById('share-email-input').value.trim();
    const rol = document.getElementById('share-role-select').value;

    if (!email) {
        alert('Lütfen bir email adresi girin');
        return;
    }

    if (!currentShoppingListId) {
        alert('Liste seçilmedi');
        return;
    }

    showLoading(true);

    try {
        const response = await fetchWithAuth(`${API_BASE}/api/paylasim/davet-gonder`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                liste_id: currentShoppingListId,
                paylasilan_email: email,
                rol: rol
            })
        });

        const data = await response.json();

        if (response.ok && data.success) {
            showNotification('✅ Liste paylaşıldı!', 'success');
            document.getElementById('share-email-input').value = '';
            loadShareInfo(currentShoppingListId);
        } else {
            showNotification(data.detail || 'Paylaşım başarısız', 'error');
        }
    } catch (error) {
        console.error('Paylaşım hatası:', error);
        showNotification('Liste paylaşılamadı', 'error');
    } finally {
        showLoading(false);
    }
}

// Paylaşım bilgilerini yükle
async function loadShareInfo(listeId) {
    try {
        const response = await fetchWithAuth(`${API_BASE}/api/paylasim/liste/${listeId}/paylasilanlar`);
        const data = await response.json();

        if (data.success && data.paylasimlar) {
            displayShareInfo(data.paylasimlar);
        }
    } catch (error) {
        console.error('Paylaşım bilgileri yüklenemedi:', error);
    }
}

// Paylaşım bilgilerini göster
function displayShareInfo(paylasimlar) {
    const container = document.getElementById('share-info-container');

    if (!container) return;

    if (paylasimlar.length === 0) {
        container.innerHTML = '<p style="color: #718096; font-size: 0.9em; margin-top: 10px;">Bu liste henüz kimseyle paylaşılmadı</p>';
        return;
    }

    let html = '<div style="margin-top: 15px;"><h4 style="margin-bottom: 10px;">👥 Paylaşılan Kişiler:</h4>';

    paylasimlar.forEach(p => {
        const rolBadge = p.rol === 'view' ? '👁️ Görüntüleyebilir' :
                        p.rol === 'edit' ? '✏️ Düzenleyebilir' :
                        '👑 Sahip';
        const statusBadge = p.kabul_edildi ? '✅ Kabul Edildi' : '⏳ Bekliyor';

        html += `
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px; background: #F7FAFC; border-radius: 8px; margin: 8px 0;">
                <div>
                    <div style="font-weight: 600;">${p.username}</div>
                    <div style="font-size: 0.85em; color: #718096;">${p.email}</div>
                    <div style="font-size: 0.85em; margin-top: 4px;">
                        <span style="background: #E6FFFA; color: #234E52; padding: 2px 8px; border-radius: 4px; margin-right: 5px;">${rolBadge}</span>
                        <span>${statusBadge}</span>
                    </div>
                </div>
                <button class="btn" style="background: #FC8181; color: white; padding: 6px 12px; font-size: 0.85em;" onclick="cancelShare(${p.id})">
                    🗑️ İptal
                </button>
            </div>
        `;
    });

    html += '</div>';
    container.innerHTML = html;
}

// Paylaşımı iptal et
async function cancelShare(paylasimId) {
    if (!confirm('Paylaşımı iptal etmek istediğinizden emin misiniz?')) {
        return;
    }

    showLoading(true);

    try {
        const response = await fetchWithAuth(`${API_BASE}/api/paylasim/paylasim/${paylasimId}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (data.success) {
            showNotification('✅ Paylaşım iptal edildi', 'success');
            loadShareInfo(currentShoppingListId);
        } else {
            showNotification('Paylaşım iptal edilemedi', 'error');
        }
    } catch (error) {
        console.error('Hata:', error);
        showNotification('İşlem başarısız', 'error');
    } finally {
        showLoading(false);
    }
}

// Davetleri yükle
async function loadInvitations() {
    showLoading(true);

    try {
        const response = await fetchWithAuth(`${API_BASE}/api/paylasim/davetler`);
        const data = await response.json();

        const container = document.getElementById('invitations-container');

        if (!data.davetler || data.davetler.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">📭</div>
                    <p>Henüz davetiniz yok</p>
                </div>
            `;
            return;
        }

        let html = '';
        data.davetler.forEach(davet => {
            const rolBadge = davet.rol === 'view' ? '👁️ Görüntüleyebilir' :
                            davet.rol === 'edit' ? '✏️ Düzenleyebilir' :
                            '👑 Sahip';

            const tarih = new Date(davet.paylasim_tarihi).toLocaleDateString('tr-TR');

            html += `
                <div style="background: white; border-radius: 12px; padding: 15px; margin-bottom: 15px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 10px;">
                        <div style="flex: 1;">
                            <div style="font-weight: 600; font-size: 1.1em; margin-bottom: 5px;">
                                ${davet.liste_baslik}
                            </div>
                            <div style="color: #718096; font-size: 0.9em; margin-bottom: 8px;">
                                👤 ${davet.paylasan_username} • 📅 ${tarih}
                            </div>
                            <div>
                                <span style="background: #E6FFFA; color: #234E52; padding: 4px 10px; border-radius: 6px; font-size: 0.9em;">
                                    ${rolBadge}
                                </span>
                            </div>
                        </div>
                    </div>
                    <div style="display: flex; gap: 10px; margin-top: 15px;">
                        <button class="btn btn-success" onclick="acceptInvitation(${davet.id})" style="flex: 1;">
                            ✅ Kabul Et
                        </button>
                        <button class="btn" style="background: #FC8181; color: white; flex: 1;" onclick="rejectInvitation(${davet.id})">
                            ❌ Reddet
                        </button>
                    </div>
                </div>
            `;
        });

        container.innerHTML = html;
    } catch (error) {
        console.error('Davetler yüklenemedi:', error);
        showNotification('Davetler yüklenemedi', 'error');
    } finally {
        showLoading(false);
    }
}

// Daveti kabul et
async function acceptInvitation(davetId) {
    showLoading(true);

    try {
        const response = await fetchWithAuth(`${API_BASE}/api/paylasim/davet/${davetId}/kabul`, {
            method: 'POST'
        });

        const data = await response.json();

        if (data.success) {
            showNotification('✅ Davet kabul edildi!', 'success');
            loadInvitations();
        } else {
            showNotification('Davet kabul edilemedi', 'error');
        }
    } catch (error) {
        console.error('Hata:', error);
        showNotification('İşlem başarısız', 'error');
    } finally {
        showLoading(false);
    }
}

// Daveti reddet
async function rejectInvitation(davetId) {
    if (!confirm('Daveti reddetmek istediğinizden emin misiniz?')) {
        return;
    }

    showLoading(true);

    try {
        const response = await fetchWithAuth(`${API_BASE}/api/paylasim/davet/${davetId}/reddet`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (data.success) {
            showNotification('✅ Davet reddedildi', 'success');
            loadInvitations();
        } else {
            showNotification('Davet reddedilemedi', 'error');
        }
    } catch (error) {
        console.error('Hata:', error);
        showNotification('İşlem başarısız', 'error');
    } finally {
        showLoading(false);
    }
}

// Paylaşılan listeleri yükle
async function loadSharedLists() {
    showLoading(true);

    try {
        const response = await fetchWithAuth(`${API_BASE}/api/paylasim/benimle-paylasilanlar`);
        const data = await response.json();

        const container = document.getElementById('shared-lists-container');

        if (!data.listeler || data.listeler.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">👥</div>
                    <p>Sizinle paylaşılan liste yok</p>
                </div>
            `;
            return;
        }

        let html = '';
        data.listeler.forEach(liste => {
            const progress = liste.toplam_urun > 0
                ? (liste.tamamlanan_urun / liste.toplam_urun * 100).toFixed(0)
                : 0;

            const statusClass = liste.tamamlandi ? 'completed' : '';
            const statusBadge = liste.tamamlandi
                ? '<span class="shopping-list-status status-completed">✅ Tamamlandı</span>'
                : '<span class="shopping-list-status status-active">📝 Aktif</span>';

            const tarih = new Date(liste.olusturma_tarihi).toLocaleDateString('tr-TR', {
                day: 'numeric',
                month: 'long',
                year: 'numeric'
            });

            const rolBadge = liste.rol === 'view' ? '👁️' : liste.rol === 'edit' ? '✏️' : '👑';

            html += `
                <div class="shopping-list-card ${statusClass}" onclick="loadShoppingDetail(${liste.id})">
                    <div class="shopping-list-header">
                        <div>
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <span style="font-weight: 600; font-size: 1.1em;">
                                    ${liste.baslik || 'Alışveriş Listesi'}
                                </span>
                                <span style="font-size: 1.2em;" title="${liste.rol === 'view' ? 'Görüntüleyebilir' : liste.rol === 'edit' ? 'Düzenleyebilir' : 'Sahip'}">${rolBadge}</span>
                            </div>
                            <div class="shopping-list-date">
                                👤 ${liste.paylasan_username} • 📅 ${tarih}
                            </div>
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
        console.error('Paylaşılan listeler yüklenemedi:', error);
        showNotification('Listeler yüklenemedi', 'error');
    } finally {
        showLoading(false);
    }
}

// Listeden ayrıl
async function leaveSharedList(listeId) {
    if (!confirm('Bu listeden ayrılmak istediğinizden emin misiniz?')) {
        return;
    }

    showLoading(true);

    try {
        const response = await fetchWithAuth(`${API_BASE}/api/paylasim/ayril/${listeId}`, {
            method: 'POST'
        });

        const data = await response.json();

        if (data.success) {
            showNotification('✅ Listeden ayrıldınız', 'success');
            showScreen('shared-lists-screen');
            loadSharedLists();
        } else {
            showNotification('İşlem başarısız', 'error');
        }
    } catch (error) {
        console.error('Hata:', error);
        showNotification('İşlem başarısız', 'error');
    } finally {
        showLoading(false);
    }
}

console.log('✅ Paylaşım özellikleri yüklendi');

console.log('✅ Tarif-e hazır! Kullanmaya başla');