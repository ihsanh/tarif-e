/**
 * Gelişmiş Tarif Filtre Sistemi
 * frontend/js/filters.js
 */

// ============================================
// FİLTRE STATE YÖNETİMİ
// ============================================

const filterState = {
    malzemeler: [],
    sure: { min: 0, max: 120 },
    zorluk: [],
    porsiyon: { min: 1, max: 10 },
    kalori: { min: 0, max: 1000 }
};

// ============================================
// FİLTRE MODAL AÇMA/KAPAMA
// ============================================

function openFilterModal() {
    const modal = document.getElementById('filter-modal');
    if (!modal) {
        createFilterModal();
    }
    
    // Mevcut filtreleri yükle
    loadCurrentFilters();
    
    document.getElementById('filter-modal').style.display = 'flex';
    document.body.style.overflow = 'hidden';
}

function closeFilterModal() {
    document.getElementById('filter-modal').style.display = 'none';
    document.body.style.overflow = 'auto';
}

// ============================================
// FİLTRE MODAL OLUŞTURMA
// ============================================

function createFilterModal() {
    const modalHTML = `
        <div id="filter-modal" class="filter-modal">
            <div class="filter-modal-content">
                <!-- Header -->
                <div class="filter-header">
                    <h2>🔍 Gelişmiş Filtre</h2>
                    <button onclick="closeFilterModal()" class="close-btn">✕</button>
                </div>
                
                <!-- Filter Body -->
                <div class="filter-body">
                    <!-- Malzemeler -->
                    <div class="filter-section">
                        <label class="filter-label">
                            🥘 İçerdiği Malzemeler
                            <span class="filter-hint">Birden fazla seçebilirsiniz</span>
                        </label>
                        <div class="ingredient-tags" id="ingredient-tags"></div>
                        <div class="ingredient-input-wrapper">
                            <input 
                                type="text" 
                                id="ingredient-input" 
                                placeholder="Malzeme ekle... (örn: domates)"
                                onkeypress="handleIngredientEnter(event)"
                            >
                            <button onclick="addIngredientFilter()" class="add-btn">Ekle</button>
                        </div>
                    </div>
                    
                    <!-- Süre -->
                    <div class="filter-section">
                        <label class="filter-label">
                            ⏱️ Hazırlama Süresi
                            <span class="filter-value" id="sure-value">0 - 120 dk</span>
                        </label>
                        <div class="range-slider-wrapper">
                            <input 
                                type="range" 
                                id="sure-min" 
                                min="0" 
                                max="120" 
                                value="0" 
                                step="5"
                                oninput="updateSureRange()"
                                class="range-slider"
                            >
                            <input 
                                type="range" 
                                id="sure-max" 
                                min="0" 
                                max="120" 
                                value="120" 
                                step="5"
                                oninput="updateSureRange()"
                                class="range-slider"
                            >
                        </div>
                        <div class="range-labels">
                            <span>0 dk</span>
                            <span>30 dk</span>
                            <span>60 dk</span>
                            <span>90 dk</span>
                            <span>120+ dk</span>
                        </div>
                    </div>
                    
                    <!-- Zorluk -->
                    <div class="filter-section">
                        <label class="filter-label">⭐ Zorluk Seviyesi</label>
                        <div class="checkbox-group">
                            <label class="checkbox-label">
                                <input 
                                    type="checkbox" 
                                    value="kolay" 
                                    onchange="updateZorlukFilter()"
                                >
                                <span class="checkbox-custom"></span>
                                <span class="difficulty easy">🟢 Kolay</span>
                            </label>
                            <label class="checkbox-label">
                                <input 
                                    type="checkbox" 
                                    value="orta" 
                                    onchange="updateZorlukFilter()"
                                >
                                <span class="checkbox-custom"></span>
                                <span class="difficulty medium">🟡 Orta</span>
                            </label>
                            <label class="checkbox-label">
                                <input 
                                    type="checkbox" 
                                    value="zor" 
                                    onchange="updateZorlukFilter()"
                                >
                                <span class="checkbox-custom"></span>
                                <span class="difficulty hard">🔴 Zor</span>
                            </label>
                        </div>
                    </div>
                    
                    <!-- Porsiyon -->
                    <div class="filter-section">
                        <label class="filter-label">
                            👥 Porsiyon Sayısı
                            <span class="filter-value" id="porsiyon-value">1 - 10 kişi</span>
                        </label>
                        <div class="range-slider-wrapper">
                            <input 
                                type="range" 
                                id="porsiyon-min" 
                                min="1" 
                                max="10" 
                                value="1" 
                                oninput="updatePorsiyonRange()"
                                class="range-slider"
                            >
                            <input 
                                type="range" 
                                id="porsiyon-max" 
                                min="1" 
                                max="10" 
                                value="10" 
                                oninput="updatePorsiyonRange()"
                                class="range-slider"
                            >
                        </div>
                        <div class="range-labels">
                            <span>1</span>
                            <span>3</span>
                            <span>5</span>
                            <span>7</span>
                            <span>10+</span>
                        </div>
                    </div>
                    
                    <!-- Kalori -->
                    <div class="filter-section">
                        <label class="filter-label">
                            🔥 Porsiyon Kalorisi
                            <span class="filter-value" id="kalori-value">0 - 1000+ kcal</span>
                        </label>
                        <div class="range-slider-wrapper">
                            <input 
                                type="range" 
                                id="kalori-min" 
                                min="0" 
                                max="1000" 
                                value="0" 
                                step="50"
                                oninput="updateKaloriRange()"
                                class="range-slider"
                            >
                            <input 
                                type="range" 
                                id="kalori-max" 
                                min="0" 
                                max="1000" 
                                value="1000" 
                                step="50"
                                oninput="updateKaloriRange()"
                                class="range-slider"
                            >
                        </div>
                        <div class="range-labels">
                            <span>0</span>
                            <span>250</span>
                            <span>500</span>
                            <span>750</span>
                            <span>1000+</span>
                        </div>
                    </div>
                </div>
                
                <!-- Footer -->
                <div class="filter-footer">
                    <button onclick="clearFilters()" class="btn-secondary">
                        🗑️ Temizle
                    </button>
                    <button onclick="applyFilters()" class="btn-primary">
                        ✅ Uygula
                    </button>
                </div>
                
                <!-- Active Filters Display -->
                <div class="active-filters" id="active-filters" style="display: none;">
                    <span class="active-filters-label">Aktif Filtreler:</span>
                    <div id="active-filters-list"></div>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHTML);
}

// ============================================
// MALZEME FİLTRESİ
// ============================================

function addIngredientFilter() {
    const input = document.getElementById('ingredient-input');
    const ingredient = input.value.trim().toLowerCase();
    
    if (!ingredient) {
        alert('Lütfen bir malzeme girin');
        return;
    }
    
    if (filterState.malzemeler.includes(ingredient)) {
        alert('Bu malzeme zaten ekli');
        return;
    }
    
    filterState.malzemeler.push(ingredient);
    renderIngredientTags();
    input.value = '';
}

function handleIngredientEnter(event) {
    if (event.key === 'Enter') {
        event.preventDefault();
        addIngredientFilter();
    }
}

function removeIngredientFilter(ingredient) {
    filterState.malzemeler = filterState.malzemeler.filter(i => i !== ingredient);
    renderIngredientTags();
}

function renderIngredientTags() {
    const container = document.getElementById('ingredient-tags');
    
    if (filterState.malzemeler.length === 0) {
        container.innerHTML = '<span class="no-ingredients">Henüz malzeme eklenmedi</span>';
        return;
    }
    
    container.innerHTML = filterState.malzemeler.map(ingredient => `
        <span class="ingredient-tag">
            ${ingredient}
            <button onclick="removeIngredientFilter('${ingredient}')" class="tag-remove">✕</button>
        </span>
    `).join('');
}

// ============================================
// RANGE SLIDER GÜNCELLEMELERI
// ============================================

function updateSureRange() {
    const min = parseInt(document.getElementById('sure-min').value);
    const max = parseInt(document.getElementById('sure-max').value);
    
    // Min max'dan büyük olamaz
    if (min > max) {
        document.getElementById('sure-min').value = max;
        filterState.sure.min = max;
    } else {
        filterState.sure.min = min;
    }
    
    filterState.sure.max = max;
    
    const label = max >= 120 ? `${min} - 120+ dk` : `${min} - ${max} dk`;
    document.getElementById('sure-value').textContent = label;
}

function updatePorsiyonRange() {
    const min = parseInt(document.getElementById('porsiyon-min').value);
    const max = parseInt(document.getElementById('porsiyon-max').value);
    
    if (min > max) {
        document.getElementById('porsiyon-min').value = max;
        filterState.porsiyon.min = max;
    } else {
        filterState.porsiyon.min = min;
    }
    
    filterState.porsiyon.max = max;
    
    const label = max >= 10 ? `${min} - 10+ kişi` : `${min} - ${max} kişi`;
    document.getElementById('porsiyon-value').textContent = label;
}

function updateKaloriRange() {
    const min = parseInt(document.getElementById('kalori-min').value);
    const max = parseInt(document.getElementById('kalori-max').value);
    
    if (min > max) {
        document.getElementById('kalori-min').value = max;
        filterState.kalori.min = max;
    } else {
        filterState.kalori.min = min;
    }
    
    filterState.kalori.max = max;
    
    const label = max >= 1000 ? `${min} - 1000+ kcal` : `${min} - ${max} kcal`;
    document.getElementById('kalori-value').textContent = label;
}

// ============================================
// ZORLUK FİLTRESİ
// ============================================

function updateZorlukFilter() {
    const checkboxes = document.querySelectorAll('.checkbox-group input[type="checkbox"]');
    filterState.zorluk = Array.from(checkboxes)
        .filter(cb => cb.checked)
        .map(cb => cb.value);
}

// ============================================
// FİLTRE UYGULAMA
// ============================================

async function applyFilters() {
    console.log('📊 Filtreler uygulanıyor:', filterState);
    
    try {
        // Backend'e filtre isteği gönder
        const response = await fetch(`${API_BASE}/api/tarif/favoriler/filtrele`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${getToken()}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(filterState)
        });
        
        if (!response.ok) {
            throw new Error('Filtreleme başarısız');
        }
        
        const data = await response.json();
        
        // Sonuçları göster
        displayFilteredResults(data.favoriler);
        
        // Aktif filtreleri göster
        displayActiveFilters();
        
        // Modal'ı kapat
        closeFilterModal();
        
        console.log(`✅ ${data.favoriler.length} tarif bulundu`);
        
    } catch (error) {
        console.error('❌ Filtre hatası:', error);
        alert('Filtreleme sırasında bir hata oluştu');
    }
}

// ============================================
// FİLTRELENMİŞ SONUÇLARI GÖSTERME
// ============================================

function displayFilteredResults(favoriler) {
    // Güvenli container bulma
    let container = document.getElementById('favoriler-container') ||
                   document.getElementById('favorilerListesi') ||
                   document.querySelector('.favoriler-list');

    if (!container) {
        console.error('❌ Container bulunamadı!');
        alert('Favoriler gösterilemedi. Sayfa yapısı kontrol edilecek.');
        return;  // ← Hata yerine çık
    }

    // Rest of the code...
    if (favoriler.length === 0) {
        container.innerHTML = `<div>Filtreye uygun tarif yok</div>`;
        return;
    }

    container.innerHTML = favoriler.map(f => createFilterFavoriCard(f)).join('');
}

// ============================================
// AKTİF FİLTRELERİ GÖSTERME
// ============================================

function displayActiveFilters() {
    const container = document.getElementById('active-filters-list');
    const activeFiltersDiv = document.getElementById('active-filters');
    
    const filters = [];
    
    // Malzemeler
    if (filterState.malzemeler.length > 0) {
        filters.push(`🥘 ${filterState.malzemeler.join(', ')}`);
    }
    
    // Süre
    if (filterState.sure.min > 0 || filterState.sure.max < 120) {
        filters.push(`⏱️ ${filterState.sure.min}-${filterState.sure.max} dk`);
    }
    
    // Zorluk
    if (filterState.zorluk.length > 0) {
        filters.push(`⭐ ${filterState.zorluk.join(', ')}`);
    }
    
    // Porsiyon
    if (filterState.porsiyon.min > 1 || filterState.porsiyon.max < 10) {
        filters.push(`👥 ${filterState.porsiyon.min}-${filterState.porsiyon.max} kişi`);
    }
    
    // Kalori
    if (filterState.kalori.min > 0 || filterState.kalori.max < 1000) {
        filters.push(`🔥 ${filterState.kalori.min}-${filterState.kalori.max} kcal`);
    }
    
    if (filters.length > 0) {
        container.innerHTML = filters.map(f => `<span class="active-filter-tag">${f}</span>`).join('');
        activeFiltersDiv.style.display = 'flex';
    } else {
        activeFiltersDiv.style.display = 'none';
    }
}

// ============================================
// FİLTRELERİ TEMİZLEME
// ============================================

function clearFilters() {
    // State'i sıfırla
    filterState.malzemeler = [];
    filterState.sure = { min: 0, max: 120 };
    filterState.zorluk = [];
    filterState.porsiyon = { min: 1, max: 10 };
    filterState.kalori = { min: 0, max: 1000 };
    
    // UI'ı güncelle
    document.getElementById('ingredient-tags').innerHTML = '<span class="no-ingredients">Henüz malzeme eklenmedi</span>';
    document.getElementById('sure-min').value = 0;
    document.getElementById('sure-max').value = 120;
    document.getElementById('porsiyon-min').value = 1;
    document.getElementById('porsiyon-max').value = 10;
    document.getElementById('kalori-min').value = 0;
    document.getElementById('kalori-max').value = 1000;
    
    document.querySelectorAll('.checkbox-group input[type="checkbox"]').forEach(cb => {
        cb.checked = false;
    });
    
    updateSureRange();
    updatePorsiyonRange();
    updateKaloriRange();
    
    document.getElementById('active-filters').style.display = 'none';
    
    console.log('🗑️ Filtreler temizlendi');
}

function loadCurrentFilters() {
    // Malzemeler
    renderIngredientTags();
    
    // Süre
    document.getElementById('sure-min').value = filterState.sure.min;
    document.getElementById('sure-max').value = filterState.sure.max;
    updateSureRange();
    
    // Porsiyon
    document.getElementById('porsiyon-min').value = filterState.porsiyon.min;
    document.getElementById('porsiyon-max').value = filterState.porsiyon.max;
    updatePorsiyonRange();
    
    // Kalori
    document.getElementById('kalori-min').value = filterState.kalori.min;
    document.getElementById('kalori-max').value = filterState.kalori.max;
    updateKaloriRange();
    
    // Zorluk
    document.querySelectorAll('.checkbox-group input[type="checkbox"]').forEach(cb => {
        cb.checked = filterState.zorluk.includes(cb.value);
    });
}

function createFilterFavoriCard(favori) {
    return `
        <div class="favori-card" style="background: white; border: 2px solid #e5e7eb;
                                       padding: 24px; margin-bottom: 20px; border-radius: 12px;
                                       box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <h3 style="margin: 0 0 12px 0; color: #1f2937;">${favori.baslik}</h3>

            ${favori.aciklama ? `<p style="color: #6b7280; margin-bottom: 16px;">${favori.aciklama}</p>` : ''}

            <div style="display: flex; gap: 16px; margin-bottom: 16px; padding: 12px;
                       background: #f9fafb; border-radius: 8px;">
                ${favori.sure ? `<span>⏱️ ${favori.sure}</span>` : ''}
                ${favori.zorluk ? `<span>⭐ ${favori.zorluk}</span>` : ''}
                ${favori.kategori ? `<span>🍽️ ${favori.kategori}</span>` : ''}
            </div>

            <details style="margin-bottom: 12px;">
                <summary style="cursor: pointer; font-weight: 600;">🥘 Malzemeler</summary>
                <ul style="margin-top: 8px;">
                    ${favori.malzemeler.map(m => `<li>${m}</li>`).join('')}
                </ul>
            </details>

            <details>
                <summary style="cursor: pointer; font-weight: 600;">📝 Hazırlanışı</summary>
                <ol style="margin-top: 8px;">
                    ${favori.adimlar.map(a => `<li style="margin: 8px 0;">${a}</li>`).join('')}
                </ol>
            </details>
        </div>
    `;
}

// ============================================
// GLOBAL EXPORTS
// ============================================

window.openFilterModal = openFilterModal;
window.closeFilterModal = closeFilterModal;
window.addIngredientFilter = addIngredientFilter;
window.handleIngredientEnter = handleIngredientEnter;
window.removeIngredientFilter = removeIngredientFilter;
window.updateSureRange = updateSureRange;
window.updatePorsiyonRange = updatePorsiyonRange;
window.updateKaloriRange = updateKaloriRange;
window.updateZorlukFilter = updateZorlukFilter;
window.applyFilters = applyFilters;
window.clearFilters = clearFilters;
