#!/bin/bash

echo "🍳 Tarif-e Başlatılıyor..."
echo "================================"

# Renk kodları
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Backend dizinine git
cd backend

# Virtual environment var mı kontrol et
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment bulunamadı. Oluşturuluyor...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment oluşturuldu${NC}"
fi

# Virtual environment'ı aktif et
echo "📦 Virtual environment aktifleştiriliyor..."
source venv/bin/activate

# Paketleri kur (ilk çalıştırmada)
if [ ! -f "venv/.installed" ]; then
    echo "📥 Paketler yükleniyor..."
    pip install -r requirements.txt
    touch venv/.installed
    echo -e "${GREEN}✅ Paketler yüklendi${NC}"
fi

# .env dosyası var mı kontrol et
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env dosyası bulunamadı${NC}"
    echo "📝 .env.example dosyasından .env oluşturuluyor..."
    cp .env.example .env
    echo -e "${RED}❗ Lütfen .env dosyasını düzenleyin ve GEMINI_API_KEY ekleyin!${NC}"
    echo "   Dosya yolu: backend/.env"
    echo ""
    read -p "Enter'a basarak devam edin..." 
fi

# Veritabanını oluştur
if [ ! -f "../data/tarif_e.db" ]; then
    echo "🗄️  Veritabanı oluşturuluyor..."
    mkdir -p ../data
    python -m app.database
fi

# Uploads klasörünü oluştur
mkdir -p uploads

echo ""
echo -e "${GREEN}✅ Hazırlık tamamlandı!${NC}"
echo "================================"
echo "🌐 Sunucu başlatılıyor..."
echo ""
echo "📱 Tarayıcınızda açın:"
echo "   http://localhost:8000"
echo ""
echo "📱 Mobil telefonunuzdan (aynı WiFi):"
echo "   http://$(hostname -I | awk '{print $1}'):8000"
echo ""
echo "⏹️  Durdurmak için: Ctrl+C"
echo "================================"
echo ""

# Uygulamayı başlat
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
