// ============================================
// TARİF PAYLAŞMA SİSTEMİ
// Sosyal medya ve email ile paylaşım
// ============================================

/**
 * Tarif paylaşma modal'ını aç
 * @param {Object} recipe - Paylaşılacak tarif objesi
 */
function openShareModal(recipe) {
    if (!recipe || !recipe.baslik) {
        showNotification('Paylaşılacak tarif bulunamadı', 'error');
        return;
    }

    // Global değişkende sakla
    window.currentShareRecipe = recipe;

    // Modal oluştur
    const modal = createShareModal(recipe);
    document.body.appendChild(modal);

    // Animasyon için kısa gecikme
    setTimeout(() => {
        modal.classList.add('show');
    }, 10);

    console.log('📤 Paylaşma modal açıldı:', recipe.baslik);
}

/**
 * Paylaşma modal'ını kapat
 */
function closeShareModal() {
    const modal = document.getElementById('share-modal');
    if (modal) {
        modal.classList.remove('show');
        setTimeout(() => {
            modal.remove();
        }, 300);
    }
}

/**
 * Paylaşma modal HTML'i oluştur
 */
function createShareModal(recipe) {
    const modal = document.createElement('div');
    modal.id = 'share-modal';
    modal.className = 'share-modal';
    
    modal.innerHTML = `
        <div class="share-modal-overlay" onclick="closeShareModal()"></div>
        <div class="share-modal-content">
            <div class="share-modal-header">
                <h3>📤 Tarifi Paylaş</h3>
                <button class="share-modal-close" onclick="closeShareModal()">×</button>
            </div>
            
            <div class="share-modal-body">
                <!-- Tarif Önizleme -->
                <div class="share-recipe-preview">
                    <h4>${recipe.baslik}</h4>
                    <p class="share-recipe-meta">
                        ⏱️ ${recipe.sure || '30 dk'} • 
                        ${recipe.zorluk || 'Orta'} • 
                        ${recipe.kategori || 'Ana Yemek'}
                    </p>
                    ${recipe.aciklama ? `<p class="share-recipe-desc">${recipe.aciklama}</p>` : ''}
                </div>

                <!-- Paylaşım Seçenekleri -->
                <div class="share-options">
                    <!-- WhatsApp -->
                    <button class="share-btn whatsapp" onclick="shareViaWhatsApp()">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z"/>
                        </svg>
                        <span>WhatsApp</span>
                    </button>

                    <!-- Twitter/X -->
                    <button class="share-btn twitter" onclick="shareViaTwitter()">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
                        </svg>
                        <span>Twitter/X</span>
                    </button>

                    <!-- Facebook -->
                    <button class="share-btn facebook" onclick="shareViaFacebook()">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
                        </svg>
                        <span>Facebook</span>
                    </button>

                    <!-- Telegram -->
                    <button class="share-btn telegram" onclick="shareViaTelegram()">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/>
                        </svg>
                        <span>Telegram</span>
                    </button>

                    <!-- Email -->
                    <button class="share-btn email" onclick="shareViaEmail()">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                            <polyline points="22,6 12,13 2,6"/>
                        </svg>
                        <span>E-posta</span>
                    </button>

                    <!-- Link Kopyala -->
                    <button class="share-btn copy" onclick="copyRecipeLink()">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
                        </svg>
                        <span>Linki Kopyala</span>
                    </button>
                </div>

                <!-- Link Önizleme (gizli) -->
                <div id="share-link-preview" class="share-link-preview" style="display: none;">
                    <input type="text" id="share-link-input" readonly>
                    <button onclick="copyRecipeLink()">Kopyala</button>
                </div>
            </div>
        </div>
    `;

    return modal;
}

/**
 * WhatsApp ile paylaş
 */
function shareViaWhatsApp() {
    const recipe = window.currentShareRecipe;
    if (!recipe) return;

    const text = generateShareText(recipe);
    const url = `https://wa.me/?text=${encodeURIComponent(text)}`;
    
    window.open(url, '_blank');
    trackShare('whatsapp');
    
    console.log('📤 WhatsApp paylaşımı:', recipe.baslik);
}

/**
 * Twitter/X ile paylaş
 */
function shareViaTwitter() {
    const recipe = window.currentShareRecipe;
    if (!recipe) return;

    const text = `🍳 ${recipe.baslik}\n\n${recipe.aciklama || 'Lezzetli bir tarif!'}\n\n#TarifE #Yemek #Tarif`;
    const url = `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}`;
    
    window.open(url, '_blank', 'width=600,height=400');
    trackShare('twitter');
    
    console.log('📤 Twitter paylaşımı:', recipe.baslik);
}

/**
 * Facebook ile paylaş
 */
function shareViaFacebook() {
    const recipe = window.currentShareRecipe;
    if (!recipe) return;

    // Facebook share dialog
    const shareUrl = window.location.href;
    const url = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(shareUrl)}`;
    
    window.open(url, '_blank', 'width=600,height=400');
    trackShare('facebook');
    
    console.log('📤 Facebook paylaşımı:', recipe.baslik);
}

/**
 * Telegram ile paylaş
 */
function shareViaTelegram() {
    const recipe = window.currentShareRecipe;
    if (!recipe) return;

    const text = generateShareText(recipe);
    const url = `https://t.me/share/url?url=${encodeURIComponent(window.location.href)}&text=${encodeURIComponent(text)}`;
    
    window.open(url, '_blank');
    trackShare('telegram');
    
    console.log('📤 Telegram paylaşımı:', recipe.baslik);
}

/**
 * Email ile paylaş
 */
function shareViaEmail() {
    const recipe = window.currentShareRecipe;
    if (!recipe) return;

    const subject = `Tarif: ${recipe.baslik}`;
    const body = generateEmailBody(recipe);
    
    const url = `mailto:?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
    window.location.href = url;
    
    trackShare('email');
    
    console.log('📤 Email paylaşımı:', recipe.baslik);
}

/**
 * Link kopyala
 */
function copyRecipeLink() {
    const recipe = window.currentShareRecipe;
    if (!recipe) return;

    // Tarif için unique link oluştur (favorilerdeyse ID kullan)
    const recipeLink = recipe.id 
        ? `${window.location.origin}/#recipe-${recipe.id}`
        : window.location.href;

    // Clipboard'a kopyala
    if (navigator.clipboard) {
        navigator.clipboard.writeText(recipeLink).then(() => {
            showNotification('✅ Link kopyalandı!', 'success');
            
            // Link önizleme göster
            const preview = document.getElementById('share-link-preview');
            const input = document.getElementById('share-link-input');
            if (preview && input) {
                input.value = recipeLink;
                preview.style.display = 'block';
                input.select();
            }
            
            trackShare('copy-link');
        }).catch(err => {
            console.error('Link kopyalama hatası:', err);
            fallbackCopyLink(recipeLink);
        });
    } else {
        fallbackCopyLink(recipeLink);
    }
    
    console.log('📤 Link kopyalandı:', recipeLink);
}

/**
 * Fallback link kopyalama (eski tarayıcılar için)
 */
function fallbackCopyLink(text) {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    textarea.select();
    
    try {
        document.execCommand('copy');
        showNotification('✅ Link kopyalandı!', 'success');
    } catch (err) {
        console.error('Copy fallback hatası:', err);
        showNotification('❌ Link kopyalanamadı', 'error');
    }
    
    document.body.removeChild(textarea);
}

/**
 * Paylaşım metni oluştur
 */
function generateShareText(recipe) {
    let text = `🍳 ${recipe.baslik}\n\n`;
    
    if (recipe.aciklama) {
        text += `${recipe.aciklama}\n\n`;
    }
    
    text += `⏱️ Hazırlık: ${recipe.sure || '30 dk'}\n`;
    text += `👨‍🍳 Zorluk: ${recipe.zorluk || 'Orta'}\n`;
    text += `🍽️ Kategori: ${recipe.kategori || 'Ana Yemek'}\n\n`;
    
    if (recipe.malzemeler && recipe.malzemeler.length > 0) {
        text += `📝 Malzemeler:\n`;
        recipe.malzemeler.slice(0, 5).forEach(m => {
            text += `• ${m}\n`;
        });
        if (recipe.malzemeler.length > 5) {
            text += `... ve daha fazlası\n`;
        }
        text += `\n`;
    }
    
    text += `Tarif-e ile hazırlandı 🎉`;
    
    return text;
}

/**
 * Email body oluştur
 */
function generateEmailBody(recipe) {
    let body = `Merhaba,\n\n`;
    body += `"${recipe.baslik}" tarifini seninle paylaşmak istedim!\n\n`;
    
    if (recipe.aciklama) {
        body += `${recipe.aciklama}\n\n`;
    }
    
    body += `📊 Tarif Detayları:\n`;
    body += `⏱️ Hazırlık Süresi: ${recipe.sure || '30 dk'}\n`;
    body += `👨‍🍳 Zorluk: ${recipe.zorluk || 'Orta'}\n`;
    body += `🍽️ Kategori: ${recipe.kategori || 'Ana Yemek'}\n\n`;
    
    if (recipe.malzemeler && recipe.malzemeler.length > 0) {
        body += `🛒 Malzemeler:\n`;
        recipe.malzemeler.forEach((m, i) => {
            body += `${i + 1}. ${m}\n`;
        });
        body += `\n`;
    }
    
    if (recipe.adimlar && recipe.adimlar.length > 0) {
        body += `👨‍🍳 Hazırlanışı:\n`;
        recipe.adimlar.forEach((a, i) => {
            body += `${i + 1}. ${a}\n`;
        });
        body += `\n`;
    }
    
    body += `Afiyet olsun! 🍽️\n\n`;
    body += `---\n`;
    body += `Bu tarif Tarif-e ile hazırlandı.\n`;
    body += `${window.location.href}`;
    
    return body;
}

/**
 * Paylaşım istatistiği kaydet (opsiyonel)
 */
async function trackShare(platform) {
    try {
        const recipe = window.currentShareRecipe;
        if (!recipe || !recipe.id) return;

        // Backend'e paylaşım kaydı gönder
        await fetch(`${API_BASE}/api/tarif/${recipe.id}/share`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            },
            body: JSON.stringify({ platform })
        });

        console.log(`📊 Paylaşım kaydedildi: ${platform}`);
    } catch (error) {
        console.error('Paylaşım tracking hatası:', error);
        // Hata olsa da devam et, kullanıcıyı etkilemesin
    }
}

/**
 * Web Share API kullan (mobil cihazlar için)
 */
async function shareViaWebAPI(recipe) {
    if (!navigator.share) {
        // Web Share API desteklenmiyorsa modal aç
        openShareModal(recipe);
        return;
    }

    try {
        await navigator.share({
            title: recipe.baslik,
            text: recipe.aciklama || 'Harika bir tarif!',
            url: window.location.href
        });

        showNotification('✅ Tarif paylaşıldı!', 'success');
        trackShare('web-api');
        
        console.log('📤 Web Share API ile paylaşıldı');
    } catch (error) {
        if (error.name !== 'AbortError') {
            console.error('Web Share API hatası:', error);
            // Hata olursa modal'ı aç
            openShareModal(recipe);
        }
    }
}

// ESC tuşu ile modal'ı kapat
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closeShareModal();
    }
});

console.log('✅ Tarif paylaşma modülü yüklendi');
