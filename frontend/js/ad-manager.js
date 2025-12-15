/**
 * Ad Manager - Google AdSense entegrasyonu
 * Pro kullanıcılara reklam göstermez, Standard kullanıcılara gösterir
 */

const API_BASE = window.location.origin;

class AdManager {
    constructor() {
        this.isProUser = false;
        this.adsEnabled = false;
        this.adSenseLoaded = false;

        // AdSense Publisher ID (bu değeri gerçek ID'niz ile değiştirin)
        this.adClient = 'ca-pub-5031698187492956'; // TODO: Gerçek AdSense ID'nizi buraya ekleyin
    }

    /**
     * Kullanıcının abonelik durumunu kontrol et
     */
    async checkUserSubscription() {
        try {
            const token = localStorage.getItem('access_token');
            if (!token) {
                console.log('[AdManager] No token, assuming standard user');
                this.isProUser = false;
                this.adsEnabled = true;
                return;
            }

            const response = await fetch(`${API_BASE}/api/subscription/status`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) {
                console.warn('[AdManager] Subscription check failed, showing ads');
                this.adsEnabled = true;
                return;
            }

            const subscription = await response.json();
            this.isProUser = subscription.tier === 'pro' && subscription.status === 'active';
            this.adsEnabled = !this.isProUser;

            console.log(`[AdManager] User tier: ${subscription.tier}, Ads enabled: ${this.adsEnabled}`);
        } catch (error) {
            console.error('[AdManager] Error checking subscription:', error);
            // Hata durumunda reklam göster (güvenli taraf)
            this.adsEnabled = true;
        }
    }

    /**
     * AdSense script'ini yükle
     */
    loadAdSenseScript() {
        if (this.adSenseLoaded || !this.adsEnabled) {
            return;
        }

        // AdSense script'i ekle
        const script = document.createElement('script');
        script.async = true;
        script.src = `https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=${this.adClient}`;
        script.crossOrigin = 'anonymous';

        script.onerror = () => {
            console.error('[AdManager] AdSense script failed to load');
        };

        document.head.appendChild(script);
        this.adSenseLoaded = true;

        console.log('[AdManager] AdSense script loaded');
    }

    /**
     * Belirli bir konuma reklam ekle
     * @param {string} containerId - Reklam container'ının ID'si
     * @param {string} adSlot - AdSense ad slot ID
     * @param {string} adFormat - Reklam formatı (auto, rectangle, horizontal, vertical)
     * @param {boolean} fullWidth - Tam genişlik responsive olsun mu?
     */
    showAd(containerId, adSlot, adFormat = 'auto', fullWidth = true) {
        if (!this.adsEnabled) {
            console.log(`[AdManager] Pro user - hiding ad container: ${containerId}`);
            const container = document.getElementById(containerId);
            if (container) {
                container.style.display = 'none';
            }
            return;
        }

        const container = document.getElementById(containerId);
        if (!container) {
            console.warn(`[AdManager] Container not found: ${containerId}`);
            return;
        }

        // Container'ı göster
        container.style.display = 'block';

        // AdSense ins elementi oluştur
        const ins = document.createElement('ins');
        ins.className = 'adsbygoogle';
        ins.style.display = 'block';
        ins.setAttribute('data-ad-client', this.adClient);
        ins.setAttribute('data-ad-slot', adSlot);
        ins.setAttribute('data-ad-format', adFormat);

        if (fullWidth) {
            ins.setAttribute('data-full-width-responsive', 'true');
        }

        // Container'a ekle
        container.innerHTML = ''; // Önceki içeriği temizle
        container.appendChild(ins);

        // AdSense'i başlat
        try {
            (window.adsbygoogle = window.adsbygoogle || []).push({});
            console.log(`[AdManager] Ad loaded in: ${containerId}`);
        } catch (error) {
            console.error(`[AdManager] Error loading ad in ${containerId}:`, error);
        }
    }

    /**
     * Tüm reklamları yükle
     */
    async initializeAds() {
        await this.checkUserSubscription();

        if (!this.adsEnabled) {
            console.log('[AdManager] Ads disabled for Pro user');
            // Tüm reklam container'larını gizle
            this.hideAllAdContainers();
            return;
        }

        // AdSense script'ini yükle
        this.loadAdSenseScript();

        console.log('[AdManager] Ads initialized for Standard user');
    }

    /**
     * Tüm reklam container'larını gizle
     */
    hideAllAdContainers() {
        const adContainers = document.querySelectorAll('[data-ad-container]');
        adContainers.forEach(container => {
            container.style.display = 'none';
        });
    }

    /**
     * Placeholder reklam göster (test için)
     */
    showPlaceholderAd(containerId, message = 'Reklam Alanı') {
        if (!this.adsEnabled) return;

        const container = document.getElementById(containerId);
        if (!container) return;

        container.style.display = 'block';
        container.innerHTML = `
            <div style="
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                border: 2px dashed #999;
                padding: 40px 20px;
                text-align: center;
                border-radius: 8px;
                color: #666;
                font-size: 14px;
            ">
                <div style="font-weight: 600; margin-bottom: 5px;">${message}</div>
                <div style="font-size: 12px; opacity: 0.7;">AdSense reklamı buraya gelecek</div>
            </div>
        `;
    }

    /**
     * Pro upgrade mesajı göster (reklam yerine)
     */
    showUpgradePrompt(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;

        container.style.display = 'block';
        container.innerHTML = `
            <div style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 30px 20px;
                text-align: center;
                border-radius: 12px;
                color: white;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
            ">
                <div style="font-size: 20px; font-weight: 700; margin-bottom: 10px;">✨ Pro'ya Geçin</div>
                <div style="font-size: 14px; margin-bottom: 15px; opacity: 0.9;">
                    Reklamsız deneyim, sınırsız tarif önerisi ve daha fazlası
                </div>
                <button onclick="window.location.href='/profile.html'" style="
                    background: white;
                    color: #667eea;
                    border: none;
                    padding: 12px 30px;
                    border-radius: 25px;
                    font-weight: 600;
                    cursor: pointer;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.2);
                    transition: transform 0.2s;
                " onmouseover="this.style.transform='translateY(-2px)'"
                   onmouseout="this.style.transform='translateY(0)'">
                    Şimdi Yükselt
                </button>
            </div>
        `;
    }
}

// Global instance oluştur
window.adManager = new AdManager();

// Sayfa yüklendiğinde reklamları başlat
document.addEventListener('DOMContentLoaded', () => {
    console.log('[AdManager] Initializing...');
    window.adManager.initializeAds();
});
