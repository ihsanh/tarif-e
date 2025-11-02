# 🍳 Tarif-e Kurulum Kılavuzu

## 📋 Gereksinimler

- Python 3.10 veya üzeri
- pip (Python paket yöneticisi)
- Google Gemini API Key (ücretsiz)
- Modern web tarayıcısı

## 🚀 Hızlı Başlangıç (Linux/Mac)

```bash
# 1. Projeyi indirin
cd tarif-e

# 2. Başlatma scriptini çalıştırın
./start.sh
```

Script otomatik olarak:
- Virtual environment oluşturur
- Paketleri yükler
- Veritabanını oluşturur
- Uygulamayı başlatır

## 🪟 Windows Kurulumu

### 1. Virtual Environment Oluşturun

```cmd
cd tarif-e\backend
python -m venv venv
venv\Scripts\activate
```

### 2. Paketleri Yükleyin

```cmd
pip install -r requirements.txt
```

### 3. Çevre Değişkenlerini Ayarlayın

`.env.example` dosyasını kopyalayın ve `.env` olarak kaydedin:

```cmd
copy .env.example .env
```

`.env` dosyasını düzenleyin ve API keyinizi ekleyin.

### 4. Veritabanını Oluşturun

```cmd
mkdir ..\data
python -m app.database
```

### 5. Uygulamayı Başlatın

```cmd
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 🔑 Google Gemini API Key Alma

### Adım 1: Google AI Studio'ya Gidin

1. [https://makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey) adresine gidin
2. Google hesabınızla giriş yapın

### Adım 2: API Key Oluşturun

1. **"Create API Key"** butonuna tıklayın
2. Projenizi seçin veya yeni proje oluşturun
3. API keyinizi kopyalayın (tekrar göremezsiniz!)

### Adım 3: .env Dosyasına Ekleyin

```bash
GEMINI_API_KEY=AIzaSy...your_key_here
```

## 📱 Kullanım

### Bilgisayardan Erişim

```
http://localhost:8000
```

### Mobil Telefondan Erişim

Aynı WiFi ağına bağlıyken:

```
http://[BİLGİSAYAR_IP]:8000
```

IP adresinizi öğrenmek için:

**Linux/Mac:**
```bash
hostname -I
```

**Windows:**
```cmd
ipconfig
```

## 🗂️ Proje Yapısı

```
tarif-e/
├── backend/
│   ├── app/
│   │   ├── main.py              # Ana uygulama
│   │   ├── config.py            # Ayarlar
│   │   ├── database.py          # Veritabanı
│   │   └── services/
│   │       └── ai_service.py    # AI servisi
│   ├── .env                     # Çevre değişkenleri (oluşturulacak)
│   └── requirements.txt         # Python paketleri
├── frontend/
│   ├── index.html               # Ana sayfa
│   ├── css/style.css            # Stiller
│   └── js/app.js                # JavaScript
├── data/
│   └── tarif_e.db              # SQLite veritabanı
└── start.sh                     # Başlatma scripti
```

## 🔧 Sorun Giderme

### Problem: ModuleNotFoundError

**Çözüm:** Virtual environment aktif mi kontrol edin

```bash
# Aktif etmek için
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### Problem: Port 8000 kullanımda

**Çözüm:** Farklı port kullanın

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

### Problem: AI servisi çalışmıyor

**Çözüm:** 
1. GEMINI_API_KEY doğru mu kontrol edin
2. İnternet bağlantınızı kontrol edin
3. API limitlerini kontrol edin

### Problem: Fotoğraf yüklenmiyor

**Çözüm:**
1. Tarayıcı kamera iznini kontrol edin
2. HTTPS kullanıyor musunuz? (Geliştirmede HTTP ok)
3. Dosya boyutu çok büyük olabilir (max 10MB)

## 📊 API Endpointleri

### Sağlık Kontrolü
```
GET /api/health
```

### Malzeme Tanıma
```
POST /api/malzeme/tani
Content-Type: multipart/form-data
Body: file (image)
```

### Tarif Önerisi
```
POST /api/tarif/oner
Content-Type: application/json
Body: {
  "malzemeler": ["domates", "biber"],
  "sure": 30,
  "zorluk": "kolay"
}
```

### Ayarlar
```
GET /api/ayarlar
POST /api/ayarlar
```

Daha fazla bilgi için: http://localhost:8000/docs (Swagger UI)

## 🔄 Güncelleme

```bash
# Paketleri güncelle
pip install --upgrade -r requirements.txt

# Veritabanını sıfırla (dikkat: tüm veri silinir!)
rm data/tarif_e.db
python -m app.database
```

## 🛡️ Güvenlik Notları

**Geliştirme Ortamı:**
- DEBUG=True (production'da False yapın)
- SECRET_KEY değiştirin
- CORS ayarlarını sıkılaştırın

**Production:**
```env
DEBUG=False
SECRET_KEY=güçlü-rastgele-anahtar
ALLOWED_HOSTS=yourdomain.com
```

## 📞 Yardım

Sorun mu yaşıyorsunuz?

1. Önce [README.md](README.md) dosyasını okuyun
2. Logları kontrol edin
3. GitHub issues açın (eğer public repo ise)

## 🎉 Başarılı Kurulum!

Artık Tarif-e'yi kullanmaya hazırsınız!

1. Fotoğraf çekin veya malzeme ekleyin
2. AI size tarif önersin
3. Alışveriş listesi oluşturun

**Afiyet olsun! 🍽️**
