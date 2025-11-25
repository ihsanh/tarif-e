// ============================================
// TEMA YÖNETİMİ
// ============================================

// Tema yükleme - sayfa açılırken
function loadTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    console.log('💾 Kaydedilmiş tema:', savedTheme);
    
    // Tema uygula
    applyTheme(savedTheme);
    
    // Radio button'ı güncelle
    const themeRadio = document.querySelector(`input[name="theme"][value="${savedTheme}"]`);
    if (themeRadio) {
        themeRadio.checked = true;
    }
}

// Tema uygulama
function applyTheme(theme) {
    console.log('🎨 Tema uygulanıyor:', theme);
    
    // Eski tema'yı kaldır
    document.documentElement.removeAttribute('data-theme');
    
    // Yeni tema'yı ekle (light default olduğu için attribute eklemiyoruz)
    if (theme !== 'light') {
        document.documentElement.setAttribute('data-theme', theme);
    }
    
    // localStorage'a kaydet
    localStorage.setItem('theme', theme);
    
    // Notification göster
    showNotification(`${getThemeEmoji(theme)} ${getThemeName(theme)} aktif edildi!`, 'success');
}

// Tema değiştir (UI'dan çağrılır)
function changeTheme(theme) {
    console.log('🔄 Tema değiştiriliyor:', theme);
    applyTheme(theme);
}

// Tema emoji
function getThemeEmoji(theme) {
    const emojis = {
        'light': '☀️',
        'material': '🎨',
        'dark': '🌙'
    };
    return emojis[theme] || '🎨';
}

// Tema adı
function getThemeName(theme) {
    const names = {
        'light': 'Açık Tema',
        'material': 'Material Design',
        'dark': 'Koyu Tema'
    };
    return names[theme] || theme;
}

// Notification göster
function showNotification(message, type = 'info') {
    // Mevcut notification varsa kaldır
    const existing = document.querySelector('.theme-notification');
    if (existing) {
        existing.remove();
    }
    
    // Notification oluştur
    const notification = document.createElement('div');
    notification.className = `theme-notification theme-notification-${type}`;
    notification.textContent = message;
    
    // Stil
    notification.style.cssText = `
        position: fixed;
        top: 80px;
        right: 20px;
        background: ${type === 'success' ? 'var(--success-color)' : 'var(--info-color)'};
        color: white;
        padding: 15px 20px;
        border-radius: 8px;
        box-shadow: var(--shadow-lg);
        z-index: 10000;
        animation: slideIn 0.3s ease, slideOut 0.3s ease 2.7s;
        font-weight: 600;
    `;
    
    document.body.appendChild(notification);
    
    // 3 saniye sonra kaldır
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// CSS animasyon ekle
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Sayfa yüklendiğinde tema'yı yükle
// DOMContentLoaded yerine hemen çalışan IIFE kullan
(function initTheme() {
    console.log('📄 Tema sistemi başlatılıyor...');
    
    // Tema'yı hemen yükle
    const savedTheme = localStorage.getItem('theme') || 'light';
    console.log('💾 Kaydedilmiş tema:', savedTheme);
    
    // Tema'yı uygula (DOM beklemeden)
    if (savedTheme !== 'light') {
        document.documentElement.setAttribute('data-theme', savedTheme);
    }
    
    console.log('✅ Tema yüklendi:', savedTheme);
})();

// Sayfa tamamen yüklenince radio button'ları güncelle
window.addEventListener('load', function() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    
    // Radio button'ı güncelle
    const themeRadio = document.querySelector(`input[name="theme"][value="${savedTheme}"]`);
    if (themeRadio) {
        themeRadio.checked = true;
    }
    
    // Radio button değişikliklerini dinle
    const themeRadios = document.querySelectorAll('input[name="theme"]');
    themeRadios.forEach(radio => {
        radio.addEventListener('change', function() {
            if (this.checked) {
                changeTheme(this.value);
            }
        });
    });
    
    console.log('✅ Tema kontrolleri hazır');
});

// Klavye kısayolları (opsiyonel)
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + Shift + T: Tema değiştir
    if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'T') {
        e.preventDefault();
        cycleTheme();
    }
});

// Tema döngüsü (klavye kısayolu için)
function cycleTheme() {
    const themes = ['light', 'material', 'dark'];
    const currentTheme = localStorage.getItem('theme') || 'light';
    const currentIndex = themes.indexOf(currentTheme);
    const nextIndex = (currentIndex + 1) % themes.length;
    const nextTheme = themes[nextIndex];
    
    changeTheme(nextTheme);
    
    // Radio button'ı güncelle
    const themeRadio = document.querySelector(`input[name="theme"][value="${nextTheme}"]`);
    if (themeRadio) {
        themeRadio.checked = true;
    }
}

// Global export (diğer dosyalardan erişim için)
window.themeManager = {
    loadTheme,
    applyTheme,
    changeTheme,
    cycleTheme
};

console.log('✅ Tema yönetimi yüklendi');
