// ============================================
// BESİN DEĞERLERİ VE KALORİ HESAPLAMA
// AI destekli besin analizi
// ============================================

/**
 * Tarif için besin değerlerini hesapla
 * @param {Object} recipe - Tarif objesi (malzemeler ve porsiyon sayısı)
 * @returns {Promise<Object>} - Besin değerleri
 */
async function calculateNutrition(recipe) {
    try {
        showLoading(true, 'Besin değerleri hesaplanıyor...');

        const response = await fetch(`${API_BASE}/api/tarif/nutrition`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            },
            body: JSON.stringify({
                baslik: recipe.baslik,
                malzemeler: recipe.malzemeler,
                porsiyon: recipe.porsiyon || 4
            })
        });

        if (!response.ok) {
            throw new Error('Besin değerleri hesaplanamadı');
        }

        const data = await response.json();
        
        if (data.success) {
            console.log('✅ Besin değerleri hesaplandı:', data.nutrition);
            return data.nutrition;
        } else {
            throw new Error(data.message || 'Hesaplama başarısız');
        }

    } catch (error) {
        console.error('❌ Besin değerleri hatası:', error);
        showNotification('Besin değerleri hesaplanamadı', 'error');
        return null;
    } finally {
        showLoading(false);
    }
}

/**
 * Besin değerleri modal'ını aç
 * @param {Object} recipe - Tarif objesi
 */
async function openNutritionModal(recipe) {
    if (!recipe || !recipe.malzemeler || recipe.malzemeler.length === 0) {
        showNotification('Malzeme bilgisi eksik', 'error');
        return;
    }

    // Besin değerlerini hesapla
    const nutrition = await calculateNutrition(recipe);
    
    if (!nutrition) {
        return; // Hata oldu, mesaj zaten gösterildi
    }

    // Modal oluştur ve göster
    const modal = createNutritionModal(recipe, nutrition);
    document.body.appendChild(modal);

    setTimeout(() => {
        modal.classList.add('show');
    }, 10);

    console.log('📊 Besin değerleri modal açıldı');
}

/**
 * Besin değerleri modal'ını kapat
 */
function closeNutritionModal() {
    const modal = document.getElementById('nutrition-modal');
    if (modal) {
        modal.classList.remove('show');
        setTimeout(() => {
            modal.remove();
        }, 300);
    }
}

/**
 * Besin değerleri modal HTML'i oluştur
 */
function createNutritionModal(recipe, nutrition) {
    const modal = document.createElement('div');
    modal.id = 'nutrition-modal';
    modal.className = 'nutrition-modal';

    const perServing = nutrition.per_serving || nutrition;
    const total = nutrition.total || nutrition;
    const porsiyon = recipe.porsiyon || 4;

    modal.innerHTML = `
        <div class="nutrition-modal-overlay" onclick="closeNutritionModal()"></div>
        <div class="nutrition-modal-content">
            <div class="nutrition-modal-header">
                <h3>📊 Besin Değerleri</h3>
                <button class="nutrition-modal-close" onclick="closeNutritionModal()">×</button>
            </div>

            <div class="nutrition-modal-body">
                <!-- Tarif Bilgisi -->
                <div class="nutrition-recipe-info">
                    <h4>${recipe.baslik}</h4>
                    <p class="nutrition-portions">
                        👥 ${porsiyon} Porsiyon
                    </p>
                </div>

                <!-- Tab Navigasyon -->
                <div class="nutrition-tabs">
                    <button class="nutrition-tab active" onclick="switchNutritionTab('per-serving')">
                        Porsiyon Başına
                    </button>
                    <button class="nutrition-tab" onclick="switchNutritionTab('total')">
                        Toplam
                    </button>
                </div>

                <!-- Porsiyon Başına Değerler -->
                <div id="nutrition-tab-per-serving" class="nutrition-tab-content active">
                    ${renderNutritionContent(perServing, 'porsiyon başına')}
                </div>

                <!-- Toplam Değerler -->
                <div id="nutrition-tab-total" class="nutrition-tab-content">
                    ${renderNutritionContent(total, 'toplam')}
                </div>

                <!-- Bilgi Notu -->
                <div class="nutrition-disclaimer">
                    ℹ️ Besin değerleri tahmini değerlerdir. Kullanılan malzemelerin markası ve miktarına göre değişiklik gösterebilir.
                </div>

                <!-- Aksiyon Butonları -->
                <div class="nutrition-actions">
                    <button class="btn btn-secondary" onclick="exportNutritionToPDF()">
                        📄 PDF İndir
                    </button>
                    <button class="btn btn-primary" onclick="closeNutritionModal()">
                        Kapat
                    </button>
                </div>
            </div>
        </div>
    `;

    return modal;
}

/**
 * Besin değerleri içeriğini render et
 */
function renderNutritionContent(nutrition, label) {
    return `
        <!-- Ana Kalori Kartı -->
        <div class="nutrition-calories-card">
            <div class="calories-main">
                <div class="calories-number">${Math.round(nutrition.calories || 0)}</div>
                <div class="calories-label">Kalori</div>
            </div>
            <div class="calories-meta">
                <small>${label}</small>
            </div>
        </div>

        <!-- Makro Besinler -->
        <div class="nutrition-macros">
            <div class="macro-item protein">
                <div class="macro-icon">🥩</div>
                <div class="macro-info">
                    <div class="macro-value">${nutrition.protein || 0}g</div>
                    <div class="macro-label">Protein</div>
                    <div class="macro-percent">${calculateMacroPercent(nutrition.protein, nutrition.calories, 4)}%</div>
                </div>
                <div class="macro-bar">
                    <div class="macro-bar-fill protein" style="width: ${calculateMacroPercent(nutrition.protein, nutrition.calories, 4)}%"></div>
                </div>
            </div>

            <div class="macro-item carbs">
                <div class="macro-icon">🍞</div>
                <div class="macro-info">
                    <div class="macro-value">${nutrition.carbs || 0}g</div>
                    <div class="macro-label">Karbonhidrat</div>
                    <div class="macro-percent">${calculateMacroPercent(nutrition.carbs, nutrition.calories, 4)}%</div>
                </div>
                <div class="macro-bar">
                    <div class="macro-bar-fill carbs" style="width: ${calculateMacroPercent(nutrition.carbs, nutrition.calories, 4)}%"></div>
                </div>
            </div>

            <div class="macro-item fat">
                <div class="macro-icon">🥑</div>
                <div class="macro-info">
                    <div class="macro-value">${nutrition.fat || 0}g</div>
                    <div class="macro-label">Yağ</div>
                    <div class="macro-percent">${calculateMacroPercent(nutrition.fat, nutrition.calories, 9)}%</div>
                </div>
                <div class="macro-bar">
                    <div class="macro-bar-fill fat" style="width: ${calculateMacroPercent(nutrition.fat, nutrition.calories, 9)}%"></div>
                </div>
            </div>
        </div>

        <!-- Detaylı Besin Değerleri -->
        <div class="nutrition-details">
            <h4>Detaylı Bilgi</h4>
            
            <div class="nutrition-detail-grid">
                ${nutrition.fiber ? `
                <div class="nutrition-detail-item">
                    <span class="detail-label">Lif</span>
                    <span class="detail-value">${nutrition.fiber}g</span>
                </div>
                ` : ''}

                ${nutrition.sugar ? `
                <div class="nutrition-detail-item">
                    <span class="detail-label">Şeker</span>
                    <span class="detail-value">${nutrition.sugar}g</span>
                </div>
                ` : ''}

                ${nutrition.sodium ? `
                <div class="nutrition-detail-item">
                    <span class="detail-label">Sodyum</span>
                    <span class="detail-value">${nutrition.sodium}mg</span>
                </div>
                ` : ''}

                ${nutrition.cholesterol ? `
                <div class="nutrition-detail-item">
                    <span class="detail-label">Kolesterol</span>
                    <span class="detail-value">${nutrition.cholesterol}mg</span>
                </div>
                ` : ''}

                ${nutrition.saturated_fat ? `
                <div class="nutrition-detail-item">
                    <span class="detail-label">Doymuş Yağ</span>
                    <span class="detail-value">${nutrition.saturated_fat}g</span>
                </div>
                ` : ''}

                ${nutrition.trans_fat ? `
                <div class="nutrition-detail-item">
                    <span class="detail-label">Trans Yağ</span>
                    <span class="detail-value">${nutrition.trans_fat}g</span>
                </div>
                ` : ''}
            </div>
        </div>

        <!-- Günlük Değer Yüzdeleri -->
        ${renderDailyValues(nutrition)}
    `;
}

/**
 * Makro besin yüzdesini hesapla
 */
function calculateMacroPercent(grams, totalCalories, caloriesPerGram) {
    if (!grams || !totalCalories) return 0;
    const macroCalories = grams * caloriesPerGram;
    return Math.round((macroCalories / totalCalories) * 100);
}

/**
 * Günlük değer yüzdelerini render et
 */
function renderDailyValues(nutrition) {
    // 2000 kalorilik diyet referans alınır
    const dailyValues = {
        calories: 2000,
        protein: 50,
        carbs: 300,
        fat: 70,
        fiber: 25,
        sodium: 2400
    };

    return `
        <div class="daily-values">
            <h4>Günlük Değer Yüzdeleri</h4>
            <p class="daily-values-note">2000 kalorilik diyete göre</p>
            
            <div class="daily-values-grid">
                <div class="daily-value-item">
                    <span class="dv-label">Kalori</span>
                    <span class="dv-percent">${Math.round((nutrition.calories / dailyValues.calories) * 100)}%</span>
                    <div class="dv-bar">
                        <div class="dv-bar-fill" style="width: ${Math.min((nutrition.calories / dailyValues.calories) * 100, 100)}%"></div>
                    </div>
                </div>

                <div class="daily-value-item">
                    <span class="dv-label">Protein</span>
                    <span class="dv-percent">${Math.round((nutrition.protein / dailyValues.protein) * 100)}%</span>
                    <div class="dv-bar">
                        <div class="dv-bar-fill" style="width: ${Math.min((nutrition.protein / dailyValues.protein) * 100, 100)}%"></div>
                    </div>
                </div>

                <div class="daily-value-item">
                    <span class="dv-label">Karbonhidrat</span>
                    <span class="dv-percent">${Math.round((nutrition.carbs / dailyValues.carbs) * 100)}%</span>
                    <div class="dv-bar">
                        <div class="dv-bar-fill" style="width: ${Math.min((nutrition.carbs / dailyValues.carbs) * 100, 100)}%"></div>
                    </div>
                </div>

                <div class="daily-value-item">
                    <span class="dv-label">Yağ</span>
                    <span class="dv-percent">${Math.round((nutrition.fat / dailyValues.fat) * 100)}%</span>
                    <div class="dv-bar">
                        <div class="dv-bar-fill" style="width: ${Math.min((nutrition.fat / dailyValues.fat) * 100, 100)}%"></div>
                    </div>
                </div>

                ${nutrition.fiber ? `
                <div class="daily-value-item">
                    <span class="dv-label">Lif</span>
                    <span class="dv-percent">${Math.round((nutrition.fiber / dailyValues.fiber) * 100)}%</span>
                    <div class="dv-bar">
                        <div class="dv-bar-fill" style="width: ${Math.min((nutrition.fiber / dailyValues.fiber) * 100, 100)}%"></div>
                    </div>
                </div>
                ` : ''}

                ${nutrition.sodium ? `
                <div class="daily-value-item">
                    <span class="dv-label">Sodyum</span>
                    <span class="dv-percent">${Math.round((nutrition.sodium / dailyValues.sodium) * 100)}%</span>
                    <div class="dv-bar">
                        <div class="dv-bar-fill" style="width: ${Math.min((nutrition.sodium / dailyValues.sodium) * 100, 100)}%"></div>
                    </div>
                </div>
                ` : ''}
            </div>
        </div>
    `;
}

/**
 * Besin değerleri tab'larını değiştir
 */
function switchNutritionTab(tabName) {
    // Tab butonlarını güncelle
    document.querySelectorAll('.nutrition-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    event.target.classList.add('active');

    // Tab içeriklerini güncelle
    document.querySelectorAll('.nutrition-tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`nutrition-tab-${tabName}`).classList.add('active');
}

/**
 * Besin değerlerini PDF olarak indir
 */
function exportNutritionToPDF() {
    showNotification('PDF indirme özelliği yakında...', 'info');
    // TODO: PDF export implementasyonu
}

/**
 * Besin değerlerini tarif kartına ekle (inline gösterim)
 */
function addNutritionBadge(element, nutrition) {
    const badge = document.createElement('div');
    badge.className = 'nutrition-badge';
    badge.innerHTML = `
        <span class="nutrition-badge-calories">
            ${Math.round(nutrition.calories)} kcal
        </span>
        <span class="nutrition-badge-macros">
            P: ${nutrition.protein}g | C: ${nutrition.carbs}g | F: ${nutrition.fat}g
        </span>
    `;
    element.appendChild(badge);
}

/**
 * Hızlı kalori gösterimi (card üzerinde)
 */
function showQuickNutrition(recipe, targetElement) {
    const quickInfo = `
        <div class="quick-nutrition">
            <button class="quick-nutrition-btn" onclick="openNutritionModal(currentRecipe)">
                📊 Besin Değerleri
            </button>
        </div>
    `;
    targetElement.insertAdjacentHTML('beforeend', quickInfo);
}

// ESC tuşu ile modal'ı kapat
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closeNutritionModal();
    }
});

console.log('✅ Besin değerleri modülü yüklendi');
