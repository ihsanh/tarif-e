# 🧪 Test Rehberi

## 📦 Kurulum

```bash
cd C:\Users\hanif\Documents\PythonProjects\Tarif-e\backend

# Test bağımlılıklarını yükle
pip install -r test_requirements.txt

# Veya tek tek:
pip install pytest pytest-asyncio pytest-cov httpx faker
```

## 🚀 Testleri Çalıştır

### Tüm Testleri Çalıştır
```bash
pytest
```

### Belirli Bir Dosyayı Test Et
```bash
pytest tests/test_malzeme.py
pytest tests/test_tarif.py
pytest tests/test_regression.py
```

### Detaylı Output
```bash
pytest -v
pytest -vv  # Daha detaylı
```

### Coverage Raporu
```bash
pytest --cov=app --cov-report=html

# Raporu aç
start htmlcov/index.html  # Windows
```

### Sadece Başarısız Testleri Tekrar Çalıştır
```bash
pytest --lf
```

### Sadece Regression Testleri
```bash
pytest -m regression tests/test_regression.py
```

### Hızlı Testler (Yavaş olanları atla)
```bash
pytest -m "not slow"
```

## 📊 Test Kategorileri

### Unit Tests (Birim Testler)
```bash
pytest tests/test_malzeme.py -v
```
- ✅ Her fonksiyon ayrı test
- ✅ Hızlı çalışır
- ✅ Dependency'siz

### Integration Tests (Entegrasyon Testler)
```bash
pytest tests/test_tarif.py -v
```
- ✅ API endpoint'leri test
- ✅ Veritabanı ile çalışır
- ✅ Gerçek akışları test eder

### Regression Tests (Gerileme Testler)
```bash
pytest tests/test_regression.py -v
```
- ✅ Kritik özellikler bozulmasın
- ✅ Geriye dönük uyumluluk
- ✅ Performans kontrolleri

## 🎯 Test Sonuçları

### Başarılı Test
```
tests/test_malzeme.py::TestMalzemeAPI::test_malzeme_ekle_success PASSED [100%]

✅ 1 passed in 0.23s
```

### Başarısız Test
```
tests/test_malzeme.py::TestMalzemeAPI::test_malzeme_ekle_success FAILED [100%]

❌ 1 failed in 0.23s
```

### Coverage Raporu
```
---------- coverage: platform win32, python 3.11.0 -----------
Name                              Stmts   Miss  Cover   Missing
---------------------------------------------------------------
app/__init__.py                       0      0   100%
app/main.py                          45      2    96%   67-68
app/routes/malzeme.py                78      5    94%   45, 67-70
app/routes/tarif.py                  62      3    95%   89-91
---------------------------------------------------------------
TOTAL                               185     10    95%
```

## 🔄 CI/CD Entegrasyonu

### GitHub Actions Örneği
`.github/workflows/tests.yml`:
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.11
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r test_requirements.txt
    
    - name: Run tests
      run: pytest --cov=app --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

## 📝 Yeni Test Yazma

### Örnek: Yeni Özellik Testi

```python
def test_yeni_ozellik(client):
    """Yeni özelliğin testi"""
    # Arrange (Hazırlık)
    data = {"field": "value"}
    
    # Act (İşlem)
    response = client.post("/api/endpoint", json=data)
    
    # Assert (Kontrol)
    assert response.status_code == 200
    assert response.json()["success"] is True
```

## 🎨 Best Practices

1. **Her özellik için test yaz**
2. **Test isimleri açıklayıcı olsun**: `test_malzeme_ekle_success`
3. **Arrange-Act-Assert** pattern kullan
4. **Her test bağımsız olmalı** (diğer testlere bağlı olmamalı)
5. **Edge case'leri test et** (boş string, null, çok büyük değer)
6. **Regression test ekle** (kritik özellikler için)

## 🐛 Hata Ayıklama

### Test Debug Mode
```bash
pytest -vv --pdb  # Hata olunca debugger açar
```

### Sadece Bir Test Çalıştır
```bash
pytest tests/test_malzeme.py::TestMalzemeAPI::test_malzeme_ekle_success -v
```

### Print Çıktılarını Gör
```bash
pytest -s  # stdout gösterir
```

## 📈 Coverage Hedefi

- ✅ **Minimum:** 80% coverage
- 🎯 **Hedef:** 90%+ coverage
- 🌟 **İdeal:** 95%+ coverage

## 🔥 Hızlı Başlangıç

```bash
# 1. Test bağımlılıklarını yükle
pip install pytest pytest-cov httpx

# 2. Testleri çalıştır
pytest

# 3. Coverage raporu oluştur
pytest --cov=app --cov-report=html

# 4. Raporu aç
start htmlcov/index.html
```

## 📚 Daha Fazla Bilgi

- pytest docs: https://docs.pytest.org/
- Coverage.py: https://coverage.readthedocs.io/
- FastAPI Testing: https://fastapi.tiangolo.com/tutorial/testing/
