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

// Ekran değiştirme
function showScreen(screenId) {
    // Tüm ekranları gizle
    document.querySelectorAll('.screen').forEach(screen => {
        screen.classList.remove('active');
    });
    
    // Seçilen ekranı göster
    document.getElementById(screenId).classList.add('active');
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

// Malzemelerimi yükle
async function loadMyIngredients() {
    try {
        const response = await fetch(`${API_BASE}/api/malzeme/liste`);
        const data = await response.json();
        
        const container = document.getElementById('my-ingredients-list');
        
        if (data.malzemeler.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">🗂️</div>
                    <p>Malzeme listeniz boş</p>
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
                </div>
            `;
        });
        
        container.innerHTML = html;
        
    } catch (error) {
        console.error('Error loading ingredients:', error);
    }
}

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
    if (!currentRecipe) return;
    
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE}/api/alisveris/olustur`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                tarif_ids: [1]  // TODO: Gerçek tarif ID'si
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            let message = '✅ Alışveriş listesi oluşturuldu!\n\nEksik malzemeler:\n';
            data.eksik_malzemeler.forEach(item => {
                message += `• ${item.name} - ${item.miktar} ${item.birim}\n`;
            });
            alert(message);
        }
        
    } catch (error) {
        console.error('Error:', error);
        alert('Alışveriş listesi oluşturulamadı');
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

console.log('✅ Tarif-e hazır!');
