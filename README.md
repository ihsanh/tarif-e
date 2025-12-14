# 🍳 Tarif-e - Akıllı Mutfak Asistanı

Evdeki malzemelerden tarif bulan, favori tariflerinizi saklayan ve akıllı alışveriş planlaması yapan modern web uygulaması.

## 🚀 Özellikler

### 🎯 Ana Özellikler
- 📸 **Fotoğraf ile malzeme tanıma** (Google Gemini AI)
- ✍️ **Manuel malzeme girişi**
- ✅ **Seçimli malzeme sistemi** (İstediğiniz malzemelerle tarif önerisi)
- 🍽️ **Akıllı tarif önerileri** (Diyet tercihlerine uygun)
- ❤️ **Favori tarifler** (Kaydet, düzenle, sil)
- 🔍 **Gelişmiş filtre sistemi** (Malzeme, süre, zorluk, porsiyon, kalori)
- 📊 **Besin değerleri hesaplama** (AI destekli, 10+ besin değeri)
- 🔗 **Tarif paylaşma** (WhatsApp, Twitter, Facebook, Telegram, Email, Link)
- 🛒 **Otomatik alışveriş listesi** (Paylaşılabilir, takım işbirliği)
- 📅 **Haftalık menü planlayıcı** (Öğün bazlı planlama, otomatik alışveriş listesi)
- 👤 **Kullanıcı profili** (Diyet tercihleri, alerjiler, tema)
- ⚙️ **Kullanıcı kontrollü AI kullanımı**

### 🎨 Kullanıcı Deneyimi
- 📱 **Mobil-first responsive tasarım**
- 🌓 **Dark mode desteği**
- ⚡ **Hızlı ve akıcı arayüz**
- 🔒 **Güvenli kimlik doğrulama** (JWT token)
- 💾 **Offline çalışma desteği** (PWA hazır)

## 🛠️ Teknolojiler

### Backend
- **Framework:** Python 3.10+, FastAPI
- **Database:** SQLite (SQLAlchemy ORM)
- **AI:** Google Gemini 2.5 Flash API
- **Authentication:** JWT token, bcrypt
- **Testing:** pytest (unit, integration, regression)

### Frontend
- **Core:** HTML5, CSS3, Vanilla JavaScript
- **Architecture:** Modular JavaScript (filters.js, nutrition.js, share.js)
- **Styling:** Responsive CSS, CSS Grid, Flexbox
- **Icons:** Emoji-based (no external dependencies)

### DevOps
- **Environment:** Virtual environment (venv)
- **Package Management:** pip (requirements.txt)
- **Version Control:** Git (.gitignore included)
- **Documentation:** Markdown

## 📦 Kurulum

### Hızlı Başlangıç

```bash
# 1. Projeyi klonlayın
git clone <repository-url>
cd tarif-e

# 2. Backend kurulumu
cd backend
python -m venv venv

# Aktivasyon (Linux/Mac)
source venv/bin/activate

# Aktivasyon (Windows)
venv\Scripts\activate

# 3. Bağımlılıkları yükleyin
pip install -r requirements.txt

# 4. Çevre değişkenlerini ayarlayın
cp .env.example .env
nano .env  # API key'inizi ekleyin

# 5. Veritabanını oluşturun
python -c "from app.database import engine, Base; from app.models import *; Base.metadata.create_all(engine)"

# 6. Uygulamayı başlatın
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Çevre Değişkenleri (.env)

```env
# AI API Key
GEMINI_API_KEY=your_gemini_api_key_here

# Database
DATABASE_URL=sqlite:///./data/tarif_e.db

# Security
SECRET_KEY=your_secret_key_here_minimum_32_characters
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application
DEBUG=True
HOST=0.0.0.0
PORT=8000
```

### Tarayıcıda Açın

**Lokal:**
```
http://localhost:8000
```

**Mobil (aynı WiFi'de):**
```
http://[BILGISAYAR_IP]:8000
```

**API Dokümantasyonu:**
```
http://localhost:8000/docs
```

## 📱 Kullanım

### 1️⃣ Kayıt ve Giriş
1. Ana sayfada "Kayıt Ol" veya "Giriş Yap"
2. Email ve şifre ile kayıt olun
3. Profil bilgilerinizi tamamlayın (opsiyonel)

### 2️⃣ Malzeme Tanıma
1. Kamera ile fotoğraf çekin veya galeriden seçin
2. AI malzemeleri otomatik tanır
3. Manuel düzenleme yapabilirsiniz

### 3️⃣ Tarif Önerisi
1. Malzemelerinizden istediğinizi seçin (✓ Tümünü Seç / ✗ Tümünü Kaldır)
2. "Seçili Malzemelerden Tarif Öner" butonuna basın
3. AI diyet tercihlerinize uygun tarif önerir
4. Besin değerlerini görüntüleyin

### 4️⃣ Favori Yönetimi
1. Beğendiğiniz tarifi favorilere ekleyin
2. Gelişmiş filtre ile tariflerinizi arayın
3. Paylaş butonuyla sosyal medyada paylaşın

### 5️⃣ Haftalık Menü Planlama
1. "📅 Menü Planlayıcı" sayfasına gidin
2. Her gün için öğün ekleyin (Kahvaltı, Öğle, Akşam)
3. Favori tariflerinizden seçin veya arama yapın
4. Otomatik alışveriş listesi oluşturun
5. Haftanın tüm ihtiyacını bir kerede planlayın

### 6️⃣ Alışveriş Listesi
1. Eksik malzemeler için liste oluşturun
2. Arkadaşlarınızla paylaşın
3. Birlikte düzenleyin

## 🗂️ Proje Yapısı

```
tarif-e/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI ana uygulama
│   │   ├── config.py               # Konfigürasyon
│   │   ├── database.py             # Database bağlantısı
│   │   │
│   │   ├── models/                 # SQLAlchemy modelleri
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── user.py             # Kullanıcı modeli
│   │   │   ├── user_profile.py     # Profil tercihleri
│   │   │   ├── tarif.py            # FavoriTarif modeli
│   │   │   ├── nutrition.py        # Besin değerleri (opsiyonel)
│   │   │   ├── malzeme.py          # Malzeme modeli
│   │   │   ├── alisveris.py        # Alışveriş listesi
│   │   │   └── menu_plan.py        # Haftalık menü planı
│   │   │
│   │   ├── routes/                 # API endpoints
│   │   │   ├── __init__.py
│   │   │   ├── auth.py             # Kimlik doğrulama
│   │   │   ├── tarif.py            # Tarif işlemleri
│   │   │   ├── malzeme.py          # Malzeme yönetimi
│   │   │   ├── alisveris.py        # Alışveriş listesi
│   │   │   ├── profile.py          # Profil yönetimi
│   │   │   └── menu_plans.py       # Menü planlama
│   │   │
│   │   ├── schemas/                # Pydantic modelleri
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── tarif.py
│   │   │   └── ...
│   │   │
│   │   ├── services/               # İş mantığı
│   │   │   ├── __init__.py
│   │   │   └── ai_service.py       # Gemini AI entegrasyonu
│   │   │
│   │   └── utils/                  # Yardımcı fonksiyonlar
│   │       ├── __init__.py
│   │       ├── auth.py             # JWT, password hashing
│   │       └── validators.py       # Veri doğrulama
│   │
│   ├── tests/                      # Test dosyaları
│   │   ├── unit/
│   │   ├── integration/
│   │   └── regression/
│   │
│   ├── data/                       # Database dosyaları
│   │   └── tarif_e.db
│   │
│   ├── requirements.txt            # Python bağımlılıkları
│   ├── .env.example                # Örnek çevre değişkenleri
│   └── .env                        # Gerçek çevre değişkenleri
│
├── frontend/
│   ├── index.html                  # Ana sayfa
│   ├── menu-planner.html           # Haftalık menü planlayıcı
│   │
│   ├── css/
│   │   ├── style.css               # Ana stiller
│   │   ├── filters.css             # Filtre modal stilleri
│   │   ├── nutrition.css           # Besin değerleri stilleri
│   │   ├── share.css               # Paylaşma stilleri
│   │   └── menu-planner.css        # Menü planlayıcı stilleri
│   │
│   ├── js/
│   │   ├── app.js                  # Ana JavaScript
│   │   ├── filters.js              # Gelişmiş filtre sistemi
│   │   ├── nutrition.js            # Besin değerleri
│   │   ├── share.js                # Paylaşma fonksiyonları
│   │   └── menu-planner.js         # Menü planlayıcı fonksiyonları
│   │
│   └── assets/
│       ├── images/
│       ├── icons/
│       └── favicon.ico
│
├── docs/                           # Dokümantasyon
│   ├── KURULUM.md                  # Detaylı kurulum
│   ├── API.md                      # API dokümantasyonu
│   └── GELISTIRME.md               # Geliştirici kılavuzu
│
├── README.md                       # Bu dosya
├── PROJE_OZETI.md                  # Proje özeti
├── PROJE_YAPISI.txt                # Yapı şeması
├── .gitignore                      # Git ignore
└── start.sh                        # Başlatma scripti (Linux/Mac)
```

## 🔑 API Endpoints

### Authentication
| Method | Endpoint | Açıklama |
|--------|----------|----------|
| POST | `/api/auth/register` | Yeni kullanıcı kaydı |
| POST | `/api/auth/login` | Giriş yap (JWT token) |
| GET | `/api/auth/me` | Kullanıcı bilgileri |

### Tarif İşlemleri
| Method | Endpoint | Açıklama |
|--------|----------|----------|
| POST | `/api/tarif/oner` | AI ile tarif öner |
| POST | `/api/tarif/favoriler/ekle` | Favorilere ekle |
| GET | `/api/tarif/favoriler/liste` | Favori listesi |
| GET | `/api/tarif/favoriler/{id}` | Favori detay |
| DELETE | `/api/tarif/favoriler/{id}` | Favori sil |
| POST | `/api/tarif/favoriler/filtrele` | Gelişmiş filtre |
| POST | `/api/tarif/nutrition` | Besin değerleri hesapla |

### Malzeme Yönetimi
| Method | Endpoint | Açıklama |
|--------|----------|----------|
| POST | `/api/malzeme/tani` | Fotoğraftan malzeme tanı |
| POST | `/api/malzeme/ekle` | Manuel malzeme ekle |
| GET | `/api/malzeme/liste` | Malzeme listesi |
| DELETE | `/api/malzeme/{id}` | Malzeme sil |

### Alışveriş Listesi
| Method | Endpoint | Açıklama |
|--------|----------|----------|
| POST | `/api/alisveris/olustur` | Yeni liste oluştur |
| GET | `/api/alisveris/listeler` | Kullanıcının listeleri |
| POST | `/api/alisveris/{id}/paylasim` | Liste paylaş |
| GET | `/api/alisveris/paylasilan/{token}` | Paylaşılan listeyi aç |

### Profil Yönetimi
| Method | Endpoint | Açıklama |
|--------|----------|----------|
| GET | `/api/profile` | Profil bilgileri |
| PUT | `/api/profile` | Profil güncelle |
| POST | `/api/profile/password` | Şifre değiştir |
| POST | `/api/profile/photo` | Profil fotoğrafı |

### Menü Planlama
| Method | Endpoint | Açıklama |
|--------|----------|----------|
| POST | `/api/menu-plans` | Yeni menü planı oluştur |
| GET | `/api/menu-plans/weekly` | Haftalık menü planı |
| PUT | `/api/menu-plans/{id}` | Plan güncelle |
| DELETE | `/api/menu-plans/{id}` | Plan sil |
| POST | `/api/menu-plans/{id}/meal` | Öğün ekle |
| POST | `/api/menu-plans/{id}/shopping-list` | Alışveriş listesi oluştur |

## 🎨 Özellik Detayları

### ✅ Seçimli Malzeme Sistemi
- **Checkbox ile seçim:** Her malzeme için ayrı checkbox
- **Toplu işlemler:** "Tümünü Seç" ve "Tümünü Kaldır" butonları
- **Seçim sayacı:** Kaç malzeme seçildiğini görüntüleme
- **Akıllı öneriler:** Sadece seçili malzemelerle tarif önerisi
- **Kullanıcı dostu:** Çok malzeme olsa bile kontrol sizde

### 📅 Haftalık Menü Planlayıcı
- **7 günlük planlama:** Pazartesi-Pazar arası
- **3 öğün:** Kahvaltı, Öğle Yemeği, Akşam Yemeği
- **Favori tarifler:** Doğrudan favorilerinizden seçin
- **Arama özelliği:** Tarif ismiyle hızlı arama
- **Otomatik alışveriş:** Haftanın tüm malzemeleri tek listede
- **Görsel planlama:** Drag & drop destekli (gelecek)

### 🔍 Gelişmiş Filtre Sistemi
- **Malzemeler:** Çoklu malzeme arama (fuzzy matching)
- **Süre:** Range slider (0-120 dakika)
- **Zorluk:** Kolay, Orta, Zor
- **Porsiyon:** 1-10 kişilik
- **Kalori:** 0-1000 kcal aralığı

### 📊 Besin Değerleri
- Kalori (kcal)
- Protein (g)
- Karbonhidrat (g)
- Yağ (g)
- Lif (g)
- Şeker (g)
- Sodyum (mg)
- Kolesterol (mg)
- Doymuş Yağ (g)
- Trans Yağ (g)

**Porsiyon başına ve toplam hesaplama**

### 🔗 Paylaşma Platformları
- WhatsApp
- Twitter (X)
- Facebook
- Telegram
- Email
- Link kopyala (clipboard)

### 👤 Profil Özellikleri
- Diyet tercihleri (Vegan, Vejetaryen, Glutensiz, vb.)
- Alerji bilgileri
- Sevmediği yiyecekler
- Tema seçimi (Light/Dark)
- Dil tercihi (TR/EN)

## 🧪 Test

```bash
# Tüm testleri çalıştır
pytest

# Kapsam raporu ile
pytest --cov=app

# Spesifik test
pytest tests/unit/test_ai_service.py

# Verbose mod
pytest -v
```

## 🚀 Production Deployment

### Docker ile (Öneri)

```bash
# Dockerfile oluşturun
docker build -t tarif-e .

# Container çalıştırın
docker run -p 8000:8000 -e GEMINI_API_KEY=your_key tarif-e
```

### Geleneksel

```bash
# Production dependencies
pip install -r requirements-prod.txt

# Gunicorn ile çalıştırın
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 📊 İstatistikler

| Kategori | Dosya Sayısı | Kod Satırı |
|----------|--------------|------------|
| Python (Backend) | 27+ | ~4000+ |
| JavaScript (Frontend) | 5 | ~1800+ |
| HTML | 2 | ~800 |
| CSS | 5 | ~1400+ |
| Tests | 15+ | ~800+ |
| Docs | 5 | ~700+ |
| **TOPLAM** | **59+** | **~9500+** |

## 🔐 Güvenlik

- ✅ Password hashing (bcrypt)
- ✅ JWT token authentication
- ✅ CORS protection
- ✅ SQL injection prevention (SQLAlchemy ORM)
- ✅ XSS protection
- ✅ Rate limiting (planned)
- ✅ Input validation (Pydantic)

## 🎯 Roadmap

### v1.1 (Tamamlandı) ✅
- [x] Haftalık menü planlama
- [x] Seçimli malzeme sistemi
- [x] Otomatik alışveriş listesi (menüden)

### v1.2 (Yakında)
- [ ] Fiş okuma (OCR) - Fiyat takibi
- [ ] Barkod tarama
- [ ] Kampanya bildirimleri
- [ ] PWA manifest (offline mode)
- [ ] Menüde drag & drop

### v1.3 (Gelecek)
- [ ] Multi-language support
- [ ] Recipe rating system
- [ ] Social features (takip, yorum)
- [ ] Video tarifler
- [ ] Sesli asistan entegrasyonu

### v2.0 (Uzun Vadeli)
- [ ] Mobile app (React Native / Flutter)
- [ ] Smart fridge integration
- [ ] Meal kit delivery
- [ ] AI chef chatbot
- [ ] Blockchain-based recipe ownership

## 📝 Lisans

Bu proje [MIT Lisansı](LICENSE) altında lisanslanmıştır.

## 👨‍💻 Geliştirici

**Tarif-e Team**
- Backend: Python/FastAPI
- Frontend: Vanilla JavaScript
- AI: Google Gemini API
- Design: Modern, minimal, mobile-first

## 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Commit yapın (`git commit -m 'Add amazing feature'`)
4. Push yapın (`git push origin feature/amazing-feature`)
5. Pull Request açın

## 🐛 Bug Raporu

Hata bulduysanız lütfen [Issues](https://github.com/yourusername/tarif-e/issues) bölümünde bildirin.

## 💬 İletişim

- Email: support@tarif-e.app
- Twitter: @tarifeapp
- Discord: [Tarif-e Community](https://discord.gg/tarifeapp)

---

**Tarif-e ile mutfağınız artık daha akıllı!** 🍳✨

Made with ❤️ in Turkey 🇹🇷