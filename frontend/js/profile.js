// ============================================
// PROFIL AYARLARI JAVASCRIPT
// Standalone profile.html için
// ============================================

// Global değişkenler (app.js ile çakışmayı önlemek için profilePage prefix)
let profilePageData = null;
let profileDietaryOptions = null;
let profileSelectedDislikes = [];

// ============================================
// PROFIL YÜKLEME
// ============================================

async function loadProfileSettings() {
    showLoading(true);

    try {
        // Profil bilgilerini getir
        const profileResponse = await fetchWithAuth(`${API_BASE}/api/profile/me`);
        const profileData = await profileResponse.json();

        if (profileData.success) {
            profilePageData = profileData;
            displayProfile(profileData);
        }

        // Diyet seçeneklerini getir
        const optionsResponse = await fetchWithAuth(`${API_BASE}/api/profile/dietary-options`);
        const optionsData = await optionsResponse.json();

        if (optionsData.success) {
            profileDietaryOptions = optionsData.options;
            displayDietaryOptions();
        }

    } catch (error) {
        console.error('Profil yükleme hatası:', error);
        showNotification('Profil yüklenemedi', 'error');
    } finally {
        showLoading(false);
    }
}

function displayProfile(data) {
    const { user, profile, subscription, usage } = data;

    // Kullanıcı bilgileri
    document.getElementById('profile-username').textContent = user.username;
    document.getElementById('profile-email').textContent = user.email;
    document.getElementById('full-name-input').value = user.full_name || '';
    document.getElementById('email-input').value = user.email;
    document.getElementById('bio-input').value = profile.bio || '';

    // Profil fotoğrafı
    if (profile.profile_photo_url) {
        document.getElementById('profile-photo-display').src = profile.profile_photo_url;
    }

    // Sevmediği yiyecekler
    profileSelectedDislikes = profile.dislikes || [];
    displayDislikes();

    // Tema
    if (profile.theme) {
        document.querySelector(`input[name="theme"][value="${profile.theme}"]`).checked = true;
    }

    // Abonelik bilgilerini göster
    if (subscription) {
        displaySubscription(subscription, usage);
    }
}

// ============================================
// ABONELIK GÖSTERIMI
// ============================================

function displaySubscription(subscription, usage) {
    const subscriptionSection = document.getElementById('subscription-section');
    const tierBadge = document.getElementById('subscription-tier-badge');
    const tierText = document.getElementById('subscription-tier-text');
    const subscriptionTitle = document.getElementById('subscription-title');
    const subscriptionDesc = document.getElementById('subscription-desc');
    const subscriptionStatus = document.getElementById('subscription-status');

    // Abonelik bölümünü göster
    subscriptionSection.style.display = 'block';

    // Tier bilgisini göster
    const isPro = subscription.tier === 'pro';
    tierText.textContent = isPro ? 'PRO' : 'STANDARD';
    tierBadge.className = `subscription-tier-badge ${subscription.tier}`;

    subscriptionTitle.textContent = isPro ? 'Pro Paket' : 'Standard Paket';
    subscriptionDesc.textContent = isPro
        ? 'Sınırsız tarif önerisi ve daha fazlası'
        : 'Günlük ' + usage.limit + ' tarif önerisi';

    // Durum
    const statusMap = {
        'active': 'Aktif',
        'expired': 'Süresi Dolmuş',
        'cancelled': 'İptal Edildi'
    };
    subscriptionStatus.textContent = statusMap[subscription.status] || subscription.status;
    subscriptionStatus.className = 'info-value status-' + subscription.status;

    // Kullanım istatistikleri (sadece standard için)
    const usageSection = document.getElementById('subscription-usage-section');
    if (!isPro && usage.limit > 0) {
        usageSection.style.display = 'block';

        document.getElementById('usage-used').textContent = usage.used_today;
        document.getElementById('usage-limit').textContent = usage.limit;

        const percentage = usage.percentage_used;
        document.getElementById('usage-progress-fill').style.width = percentage + '%';

        const remaining = usage.remaining;
        const remainingText = document.getElementById('usage-remaining-text');
        if (remaining > 0) {
            remainingText.textContent = `${remaining} tarif hakkınız kaldı`;
            remainingText.className = 'usage-remaining';
        } else {
            remainingText.textContent = 'Günlük limitinize ulaştınız';
            remainingText.className = 'usage-remaining limit-reached';
        }
    } else {
        usageSection.style.display = 'none';
    }

    // Bitiş tarihi
    const endDateRow = document.getElementById('subscription-end-date-row');
    if (subscription.end_date) {
        endDateRow.style.display = 'flex';
        const endDate = new Date(subscription.end_date);
        document.getElementById('subscription-end-date').textContent =
            endDate.toLocaleDateString('tr-TR', {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });
    } else {
        endDateRow.style.display = 'none';
    }

    // Faturalandırma
    const billingRow = document.getElementById('subscription-billing-row');
    if (isPro) {
        billingRow.style.display = 'flex';
        const billingMap = {
            'monthly': 'Aylık',
            'yearly': 'Yıllık'
        };
        document.getElementById('subscription-billing').textContent =
            billingMap[subscription.billing_cycle] || subscription.billing_cycle;
    } else {
        billingRow.style.display = 'none';
    }

    // Otomatik yenileme
    const autoRenewRow = document.getElementById('subscription-auto-renew-row');
    if (isPro) {
        autoRenewRow.style.display = 'flex';
        document.getElementById('subscription-auto-renew').textContent =
            subscription.auto_renew ? 'Aktif' : 'Pasif';
    } else {
        autoRenewRow.style.display = 'none';
    }

    // Yükseltme butonu (sadece standard için)
    const upgradeSection = document.getElementById('subscription-upgrade-section');
    if (!isPro) {
        upgradeSection.style.display = 'block';
    } else {
        upgradeSection.style.display = 'none';
    }
}

function showUpgradeModal() {
    // İleride modal ile yükseltme ekranı gösterilebilir
    if (confirm('Pro pakete yükseltmek ister misiniz?\n\n✓ Sınırsız tarif önerisi\n✓ Reklamsız deneyim\n✓ Öncelikli destek')) {
        upgradeToPro();
    }
}

async function upgradeToPro() {
    try {
        const response = await fetchWithAuth(`${API_BASE}/api/subscription/upgrade`, {
            method: 'POST'
        });

        const data = await response.json();

        if (data.success) {
            showNotification('Pro pakete başarıyla yükseltildiniz!', 'success');
            // Profili yeniden yükle
            loadProfileSettings();
        } else {
            showNotification('Yükseltme başarısız oldu', 'error');
        }
    } catch (error) {
        console.error('Upgrade error:', error);
        showNotification('Bir hata oluştu', 'error');
    }
}

// ============================================
// TAB YÖNETİMİ
// ============================================

function showSettingsTab(tabName) {
    // Tüm tab butonlarını pasifleştir
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    // Tüm tab içeriklerini gizle
    document.querySelectorAll('.settings-tab-content').forEach(content => {
        content.classList.remove('active');
    });

    // Seçili tab'ı aktifleştir
    event.target.classList.add('active');
    document.getElementById(`settings-tab-${tabName}`).classList.add('active');
}

// ============================================
// DİYET TERCİHLERİ
// ============================================

function displayDietaryOptions() {
    if (!profileDietaryOptions) return;

    // Diyet tercihleri
    const dietaryContainer = document.getElementById('dietary-preferences-container');
    dietaryContainer.innerHTML = '';

    profileDietaryOptions.dietary_preferences.forEach(option => {
        const isSelected = profilePageData.profile.dietary_preferences.includes(option.value);
        const item = createPreferenceItem(option, isSelected, 'dietary');
        dietaryContainer.appendChild(item);
    });

    // Alerjiler
    const allergiesContainer = document.getElementById('allergies-container');
    allergiesContainer.innerHTML = '';

    profileDietaryOptions.common_allergies.forEach(option => {
        const isSelected = profilePageData.profile.allergies.includes(option.value);
        const item = createPreferenceItem(option, isSelected, 'allergy');
        allergiesContainer.appendChild(item);
    });
}

function createPreferenceItem(option, isSelected, type) {
    const div = document.createElement('div');
    div.className = `preference-item ${isSelected ? 'selected' : ''}`;
    div.onclick = () => togglePreference(div, option.value, type);

    div.innerHTML = `
        <input type="checkbox" ${isSelected ? 'checked' : ''} onclick="event.stopPropagation()">
        <span class="icon">${option.icon}</span>
        <span class="label">${option.label}</span>
    `;

    return div;
}

function togglePreference(element, value, type) {
    const checkbox = element.querySelector('input[type="checkbox"]');
    checkbox.checked = !checkbox.checked;
    element.classList.toggle('selected');
}

function getSelectedPreferences(type) {
    const containerId = type === 'dietary' ? 'dietary-preferences-container' : 'allergies-container';
    const container = document.getElementById(containerId);
    const selected = [];

    container.querySelectorAll('.preference-item.selected').forEach(item => {
        const label = item.querySelector('.label').textContent;
        const option = profileDietaryOptions[type === 'dietary' ? 'dietary_preferences' : 'common_allergies']
            .find(opt => opt.label === label);
        if (option) {
            selected.push(option.value);
        }
    });

    return selected;
}

async function savePreferences() {
    showLoading(true);

    const dietary_preferences = getSelectedPreferences('dietary');
    const allergies = getSelectedPreferences('allergy');

    try {
        const response = await fetchWithAuth(`${API_BASE}/api/profile/update`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                dietary_preferences,
                allergies,
                dislikes: profileSelectedDislikes
            })
        });

        const data = await response.json();

        if (data.success) {
            showNotification('✅ Tercihler kaydedildi!', 'success');
            profilePageData.profile.dietary_preferences = dietary_preferences;
            profilePageData.profile.allergies = allergies;
            profilePageData.profile.dislikes = profileSelectedDislikes;
        } else {
            showNotification('Tercihler kaydedilemedi', 'error');
        }
    } catch (error) {
        console.error('Hata:', error);
        showNotification('İşlem başarısız', 'error');
    } finally {
        showLoading(false);
    }
}

// ============================================
// SEVMEDİĞİM YİYECEKLER
// ============================================

function addDislike() {
    const input = document.getElementById('dislike-input');
    const value = input.value.trim();

    if (!value) return;

    if (profileSelectedDislikes.includes(value)) {
        showNotification('Bu zaten listede var', 'error');
        return;
    }

    profileSelectedDislikes.push(value);
    displayDislikes();
    input.value = '';
}

function removeDislike(value) {
    profileSelectedDislikes = profileSelectedDislikes.filter(item => item !== value);
    displayDislikes();
}

function displayDislikes() {
    const container = document.getElementById('dislikes-list');
    container.innerHTML = '';

    profileSelectedDislikes.forEach(item => {
        const tag = document.createElement('div');
        tag.className = 'tag';
        tag.innerHTML = `
            ${item}
            <span class="tag-remove" onclick="removeDislike('${item}')">×</span>
        `;
        container.appendChild(tag);
    });
}

// ============================================
// KULLANICI BİLGİLERİ GÜNCELLEME
// ============================================

async function updateUserInfo() {
    const full_name = document.getElementById('full-name-input').value.trim();
    const email = document.getElementById('email-input').value.trim();
    const bio = document.getElementById('bio-input').value.trim();

    if (!email) {
        showNotification('Email boş olamaz', 'error');
        return;
    }

    showLoading(true);

    try {
        // Kullanıcı bilgilerini güncelle
        const userResponse = await fetchWithAuth(`${API_BASE}/api/profile/user-info`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ full_name, email })
        });

        const userData = await userResponse.json();

        // Profil bilgilerini güncelle
        const profileResponse = await fetchWithAuth(`${API_BASE}/api/profile/update`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ bio })
        });

        const profileData = await profileResponse.json();

        if (userData.success && profileData.success) {
            showNotification('✅ Bilgiler güncellendi!', 'success');
            profilePageData.user.full_name = full_name;
            profilePageData.user.email = email;
            profilePageData.profile.bio = bio;
            document.getElementById('profile-email').textContent = email;
        } else {
            showNotification('Bilgiler güncellenemedi', 'error');
        }
    } catch (error) {
        console.error('Hata:', error);
        showNotification('İşlem başarısız', 'error');
    } finally {
        showLoading(false);
    }
}

// ============================================
// ŞİFRE DEĞİŞTİRME
// ============================================

async function changePassword() {
    const currentPassword = document.getElementById('current-password').value;
    const newPassword = document.getElementById('new-password').value;
    const confirmPassword = document.getElementById('confirm-password').value;

    // Validasyon
    if (!currentPassword || !newPassword || !confirmPassword) {
        showNotification('Tüm alanları doldurun', 'error');
        return;
    }

    if (newPassword.length < 6) {
        showNotification('Yeni şifre en az 6 karakter olmalı', 'error');
        return;
    }

    if (newPassword !== confirmPassword) {
        showNotification('Yeni şifreler eşleşmiyor', 'error');
        return;
    }

    showLoading(true);

    try {
        const response = await fetchWithAuth(`${API_BASE}/api/profile/change-password`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                current_password: currentPassword,
                new_password: newPassword
            })
        });

        const data = await response.json();

        if (data.success) {
            showNotification('✅ Şifre değiştirildi!', 'success');
            // Alanları temizle
            document.getElementById('current-password').value = '';
            document.getElementById('new-password').value = '';
            document.getElementById('confirm-password').value = '';
        } else {
            showNotification(data.detail || 'Şifre değiştirilemedi', 'error');
        }
    } catch (error) {
        console.error('Hata:', error);
        showNotification('İşlem başarısız', 'error');
    } finally {
        showLoading(false);
    }
}

// ============================================
// PROFİL FOTOĞRAFI
// ============================================

async function uploadProfilePhoto() {
    const input = document.getElementById('profile-photo-input');
    const file = input.files[0];

    if (!file) return;

    // Dosya tipi kontrolü
    if (!file.type.startsWith('image/')) {
        showNotification('Sadece resim dosyaları yüklenebilir', 'error');
        return;
    }

    // Dosya boyutu kontrolü (5MB)
    if (file.size > 5 * 1024 * 1024) {
        showNotification('Dosya boyutu 5MB\'dan küçük olmalı', 'error');
        return;
    }

    showLoading(true);

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetchWithAuth(`${API_BASE}/api/profile/upload-photo`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            showNotification('✅ Fotoğraf yüklendi!', 'success');
            document.getElementById('profile-photo-display').src = data.photo_url;
            profilePageData.profile.profile_photo_url = data.photo_url;
        } else {
            showNotification('Fotoğraf yüklenemedi', 'error');
        }
    } catch (error) {
        console.error('Hata:', error);
        showNotification('İşlem başarısız', 'error');
    } finally {
        showLoading(false);
    }
}

async function deleteProfilePhoto() {
    if (!confirm('Profil fotoğrafını silmek istediğinizden emin misiniz?')) {
        return;
    }

    showLoading(true);

    try {
        const response = await fetchWithAuth(`${API_BASE}/api/profile/delete-photo`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (data.success) {
            showNotification('✅ Fotoğraf silindi', 'success');
            document.getElementById('profile-photo-display').src = '/static/default-avatar.png';
            profilePageData.profile.profile_photo_url = null;
        } else {
            showNotification(data.detail || 'Fotoğraf silinemedi', 'error');
        }
    } catch (error) {
        console.error('Hata:', error);
        showNotification('İşlem başarısız', 'error');
    } finally {
        showLoading(false);
    }
}

// ============================================
// GÖRÜNÜM AYARLARI
// ============================================

async function saveAppearance() {
    const theme = document.querySelector('input[name="theme"]:checked')?.value;

    if (!theme) {
        showNotification('Bir tema seçin', 'error');
        return;
    }

    showLoading(true);

    try {
        const response = await fetchWithAuth(`${API_BASE}/api/profile/update`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ theme })
        });

        const data = await response.json();

        if (data.success) {
            showNotification('✅ Tema kaydedildi!', 'success');
            profilePageData.profile.theme = theme;
            // Tema uygulaması (gelecekte)
            // applyTheme(theme);
        } else {
            showNotification('Tema kaydedilemedi', 'error');
        }
    } catch (error) {
        console.error('Hata:', error);
        showNotification('İşlem başarısız', 'error');
    } finally {
        showLoading(false);
    }
}

// ============================================
// YARDIMCI FONKSİYONLAR
// ============================================

// Profil tercihlerini tarif önerisi için al
function getUserPreferences() {
    if (!profilePageData) return null;

    return {
        dietary_preferences: profilePageData.profile.dietary_preferences || [],
        allergies: profilePageData.profile.allergies || [],
        dislikes: profilePageData.profile.dislikes || []
    };
}

// Tarif önerisi için prompt oluştur
function buildRecipePromptWithPreferences(malzemeler) {
    const preferences = getUserPreferences();
    if (!preferences) return buildRecipePrompt(malzemeler);

    let prompt = `Bu malzemelerle tarif öner: ${malzemeler.join(', ')}\n\n`;

    if (preferences.dietary_preferences.length > 0) {
        prompt += `Diyet tercihleri: ${preferences.dietary_preferences.join(', ')}\n`;
    }

    if (preferences.allergies.length > 0) {
        prompt += `Alerjiler (kullanma): ${preferences.allergies.join(', ')}\n`;
    }

    if (preferences.dislikes.length > 0) {
        prompt += `Sevmediği yiyecekler (mümkünse kullanma): ${preferences.dislikes.join(', ')}\n`;
    }

    prompt += '\nBu tercihlere uygun, detaylı bir tarif hazırla.';

    return prompt;
}

console.log('✅ Profil ayarları modülü yüklendi');