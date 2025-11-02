# 🚀 Hemen Başla!

## 5 Dakikada Tarif-e

### 1️⃣ Gemini API Key Al (2 dakika)

```
1. https://makersuite.google.com/app/apikey → Aç
2. Google hesabınla giriş yap
3. "Create API Key" → Tıkla
4. Key'i kopyala (AIzaSy... ile başlayan)
```

### 2️⃣ Projeyi Hazırla (1 dakika)

**Linux/Mac:**
```bash
cd tarif-e/backend
cp .env.example .env
nano .env  # veya herhangi bir editör
```

**Windows:**
```cmd
cd tarif-e\backend
copy .env.example .env
notepad .env
```

`.env` dosyasına yapıştır:
```env
GEMINI_API_KEY=AIzaSy...BURAYA_KEYINI_YAPIŞTIR
```

Kaydet ve kapat.

### 3️⃣ Çalıştır (2 dakika)

**Linux/Mac:**
```bash
cd tarif-e
./start.sh
```

**Windows:**
```cmd
cd tarif-e\backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m app.database
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4️⃣ Aç ve Kullan!

Tarayıcıda:
```
http://localhost:8000
```

## ✅ İlk Test

1. **"Fotoğraf Çek"** veya **"Manuel Ekle"** seç
2. Malzeme ekle: `domates, biber, soğan`
3. **"Tarif Öner"** butonuna bas
4. AI sana menemen tarifi üretecek! 🍳

## 📱 Telefondan Kullan

Bilgisayarında şu komutu çalıştır:

**Linux/Mac:**
```bash
hostname -I
# Örnek çıktı: 192.168.1.105
```

**Windows:**
```cmd
ipconfig
# IPv4 Address'e bak: 192.168.1.105
```

Telefonunda tarayıcıyı aç:
```
http://192.168.1.105:8000
```

(Aynı WiFi'de olman gerekli!)

## 🔧 Sorun mu var?

### "ModuleNotFoundError"
```bash
# Virtual environment aktif et
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Paketleri kur
pip install -r requirements.txt
```

### "AI servisi çalışmıyor"
- `.env` dosyasını kontrol et
- API key doğru mu?
- İnternet bağlantın var mı?

### "Port 8000 kullanımda"
```bash
# Farklı port kullan
uvicorn app.main:app --port 8080 --reload
# Sonra http://localhost:8080 aç
```

## 📚 Daha Fazla Bilgi

- **Detaylı kurulum:** `docs/KURULUM.md`
- **API dokümantasyonu:** http://localhost:8000/docs
- **Proje özeti:** `PROJE_OZETI.md`

## 🎉 Başarılı!

Artık Tarif-e'yi kullanabilirsin!

Sorular için Projects menüsünden benimle konuşmaya devam et 💬

---

**Hadi başlayalım! 🍳**
