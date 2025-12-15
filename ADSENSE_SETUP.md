# Google AdSense Kurulum Rehberi

Bu dosya, Tarif-e uygulamasına Google AdSense reklamlarının nasıl entegre edileceğini açıklar.

## 📋 Gereksinimler

1. **Google AdSense Hesabı**: https://www.google.com/adsense adresinden ücretsiz hesap açın
2. **Onaylanmış Domain**: AdSense hesabınızın siteniz için onaylanmış olması gerekir
3. **Publisher ID**: AdSense'ten `ca-pub-XXXXXXXXXXXXXXXX` formatında ID alacaksınız

## 🚀 Kurulum Adımları

### 1. Google AdSense Hesabı Oluşturma

1. https://www.google.com/adsense adresine gidin
2. Google hesabınızla giriş yapın
3. Web sitenizin URL'sini ekleyin
4. Ödeme bilgilerinizi girin
5. AdSense verification kodunu sitenize ekleyin (gerekirse)

### 2. Publisher ID'yi Alın

AdSense hesabınızda "Settings" > "Account" > "Account Information" bölümünden Publisher ID'nizi bulun.
Format: `ca-pub-XXXXXXXXXXXXXXXX`

### 3. Kodu Güncelleyin

#### 3.1 Ad Manager'da Publisher ID'yi Güncelleyin

**Dosya**: `frontend/js/ad-manager.js`

```javascript
// Bu satırı bulun (satır 12):
this.adClient = 'ca-pub-XXXXXXXXXXXXXXXX'; // TODO: Gerçek AdSense ID'nizi buraya ekleyin

// Kendi ID'nizle değiştirin:
this.adClient = 'ca-pub-1234567890123456'; // ÖRNEKleri gerçek ID ile değiştirin
```

#### 3.2 Config Dosyasını Güncelleyin (Opsiyonel)

**Dosya**: `backend/app/config.py`

```python
# Ads settings
ADS_ENABLED: bool = True
GOOGLE_ADSENSE_CLIENT_ID: Optional[str] = "ca-pub-1234567890123456"
```

### 4. Ad Slot ID'leri Oluşturun

AdSense dashboard'unda her reklam yeri için "Ad Unit" oluşturun:

1. AdSense > Ads > By site > New ad unit
2. Ad unit type seçin:
   - **Display ads** (responsive, otomatik boyut)
   - **In-article ads** (içerik arası)
   - **In-feed ads** (liste içi)

3. Her ad unit için bir Slot ID alacaksınız: `1234567890`

### 5. Placeholder'ları Gerçek Reklamlarla Değiştirin

**Dosya**: `frontend/js/app.js`

```javascript
// Bu satırları bulun (satır 325):
window.adManager.showPlaceholderAd('ad-top-banner', 'Top Banner - 728x90 Leaderboard');

// Gerçek AdSense ile değiştirin:
window.adManager.showAd('ad-top-banner', '1234567890', 'auto', true);
//                       ^container ID  ^ad slot ID  ^format ^fullwidth
```

## 📍 Reklam Yerleşimi Konumları

Şu anda uygulamada tanımlı reklam konumları:

### Ana Sayfa
- **ID**: `ad-top-banner`
- **Konum**: Ana menü butonlarından sonra
- **Önerilen Format**: Horizontal banner (728x90 veya responsive)

### İlave Konumlar (Kendiniz Ekleyebilirsiniz)

**Tarif Sonuç Sayfası**:
```html
<div id="ad-recipe-result" class="ad-container ad-inline" data-ad-container>
    <!-- AdSense -->
</div>
```

**Profil Sayfası**:
```html
<div id="ad-profile-sidebar" class="ad-container ad-sidebar" data-ad-container>
    <!-- AdSense -->
</div>
```

## 🎨 Reklam Formatları

AdSense'te mevcut format seçenekleri:

| Format | Açıklama | Kullanım Yeri |
|--------|----------|---------------|
| `auto` | Otomatik boyut (responsive) | Çoğu yer için önerilir |
| `horizontal` | Yatay banner | Sayfa üst/alt |
| `vertical` | Dikey banner | Sidebar |
| `rectangle` | Kare/dikdörtgen | İçerik arası |

## 💡 Pro Kullanıcılar İçin Reklamsız Deneyim

Sistem otomatik olarak Pro kullanıcılara reklam göstermez:

1. `AdManager` subscription status'u kontrol eder
2. Pro kullanıcılar için `adsEnabled = false` olur
3. Tüm `.ad-container` elementleri gizlenir

## 🧪 Test Etme

### Placeholder Reklamlarla Test

Placeholder reklamlar şu anda aktif (development için):

```javascript
// app.js içinde
window.adManager.showPlaceholderAd('ad-top-banner', 'Test Reklam');
```

### Gerçek Reklamlarla Test

1. Publisher ID ve Ad Slot ID'leri ekleyin
2. `showPlaceholderAd()` yerine `showAd()` kullanın
3. **ÖNEMLİ**: Test modunda kendi reklamlarınıza TIKLAMA yapmayın! (AdSense policy ihlali)

### Test Kullanıcıları

- **Standard User**: Reklamları görmeli
- **Pro User**: Reklam görmemeli, `display: none` olmalı

## 📊 Performans İzleme

AdSense dashboard'unda görebilecekleriniz:

- **Impressions**: Reklam görüntülenme sayısı
- **Clicks**: Tıklama sayısı
- **CTR**: Click-through rate (%)
- **Revenue**: Kazanç (USD/TL)
- **Page RPM**: Sayfa başına ortalama gelir

## 🛡️ AdSense Politikaları

**ÖNEMLİ Kurallar**:

1. ❌ Kendi reklamlarınıza TIKLAMA yapmayın
2. ❌ Kullanıcıları reklama tıklamaya ZORLAMA/TEŞVİK etmeyin
3. ❌ "Reklama tıklayın" gibi ifadeler KULLANMAYIN
4. ✅ Reklamlar "Reklam" veya "Advertisement" olarak ETİKETLENMELİ
5. ✅ Sayfada maksimum 3 display ad önerilir
6. ✅ İçerik kaliteli ve orijinal olmalı

## 🔧 Sorun Giderme

### Reklamlar Görünmüyor

1. **Console'u kontrol edin**:
   ```
   [AdManager] User tier: standard, Ads enabled: true
   [AdManager] AdSense script loaded
   ```

2. **Publisher ID doğru mu?**
   - `ad-manager.js` içindeki `this.adClient` değeri

3. **Ad blocker aktif mi?**
   - uBlock Origin, AdBlock vb. kapalı olmalı

4. **Subscription tier kontrol edin**:
   ```javascript
   // Console'da test edin
   window.adManager.isProUser  // false olmalı
   window.adManager.adsEnabled // true olmalı
   ```

### AdSense Onay Süreci

- İlk başvuruda 1-2 hafta sürebilir
- Site trafiği ve içerik kalitesi önemli
- AdSense politikalarına uyum zorunlu

## 📞 Destek

- **AdSense Yardım**: https://support.google.com/adsense
- **AdSense Topluluk**: https://support.google.com/adsense/community
- **AdSense Politikaları**: https://support.google.com/adsense/answer/48182

## 🎯 Sonraki Adımlar

1. ✅ AdSense hesabı oluştur
2. ✅ Publisher ID al
3. ✅ Ad units oluştur (2-3 tane)
4. ✅ Kodu güncelle (`ad-manager.js` ve `app.js`)
5. ✅ Test et (Standard ve Pro kullanıcılar)
6. ✅ Production'a deploy et
7. ✅ Performansı izle

---

**Not**: Bu entegrasyon Pro/Standard tier ayrımı ile tam entegre çalışacak şekilde hazırlanmıştır. Pro kullanıcılar otomatik olarak reklam görmeyecektir.

