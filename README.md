# 🍳 Tarif-e - Akıllı Mutfak Asistanı

Evdeki malzemelerden tarif bulan ve akıllı alışveriş planlaması yapan web uygulaması.

## 🚀 Özellikler

- 📸 Fotoğraf ile malzeme tanıma (Google Gemini AI)
- ✍️ Manuel malzeme girişi
- 🍽️ Akıllı tarif önerileri
- 🛒 Otomatik alışveriş listesi oluşturma
- ⚙️ Kullanıcı kontrollü AI kullanımı

## 🛠️ Teknolojiler

- **Backend:** Python 3.10+, FastAPI
- **Frontend:** HTML5, CSS3, JavaScript
- **AI:** Google Gemini API
- **Database:** SQLite
- **Hosting:** Local (geliştirme aşaması)

## 📦 Kurulum

### 1. Gereksinimleri Yükleyin

```bash
cd backend
pip install -r requirements.txt
```

### 2. Çevre Değişkenlerini Ayarlayın

`.env` dosyası oluşturun:

```
GEMINI_API_KEY=your_api_key_here
DATABASE_URL=sqlite:///./data/tarif_e.db
SECRET_KEY=your_secret_key_here
```

### 3. Veritabanını Başlatın

```bash
python -m app.database
```

### 4. Uygulamayı Çalıştırın

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Tarayıcıda Açın

```
http://localhost:8000
```

Mobil telefondan erişmek için (aynı WiFi'deyseniz):
```
http://[BILGISAYAR_IP]:8000
```

## 📱 Kullanım

1. Ana sayfada "Fotoğraf Çek" veya "Manuel Ekle" seçin
2. Malzemelerinizi ekleyin
3. AI size tarif önerecek
4. Beğendiğiniz tarifi seçin
5. Eksik malzemeler için alışveriş listesi oluşturun

## 🗂️ Proje Yapısı

```
tarif-e/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI ana dosya
│   │   ├── config.py            # Ayarlar
│   │   ├── database.py          # Veritabanı
│   │   ├── models/              # Veri modelleri
│   │   ├── routes/              # API endpoints
│   │   ├── services/            # İş mantığı
│   │   └── utils/               # Yardımcı fonksiyonlar
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── css/
│   ├── js/
│   └── assets/
├── data/
│   └── tarif_e.db
└── docs/
```

## 🔑 API Endpoints

- `GET /` - Ana sayfa
- `POST /api/malzeme/tani` - Fotoğraftan malzeme tanıma
- `POST /api/malzeme/ekle` - Manuel malzeme ekleme
- `GET /api/malzeme/liste` - Kullanıcının malzemeleri
- `POST /api/tarif/oner` - Tarif önerisi
- `GET /api/tarif/{id}` - Tarif detayı
- `POST /api/alisveris/olustur` - Alışveriş listesi

## 📝 Lisans

Bu proje kişisel kullanım için geliştirilmiştir.

## 👨‍💻 Geliştirici

Yapım aşamasında... 🚧

## 🤝 Katkıda Bulunma

Şu an için kişisel proje. İleride açık kaynak olabilir!

---

**Tarif-e ile mutfağınız artık daha akıllı!** 🍳✨
