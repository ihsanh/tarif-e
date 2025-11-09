"""
Regression Tests - Kritik özelliklerin çalıştığını garanti et
Auth Güncellenmiş
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine

client = TestClient(app)


# Test veritabanını sıfırla
@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


# Auth token fixture
@pytest.fixture
def auth_token():
    """Test için token oluştur"""
    register_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "test123"
    }
    response = client.post("/api/auth/register", json=register_data)
    assert response.status_code == 201
    
    token = response.json()["access_token"]
    return token


def get_auth_headers(token):
    """Authorization header oluştur"""
    return {"Authorization": f"Bearer {token}"}


# Sample malzemeler fixture
@pytest.fixture
def sample_malzemeler(auth_token):
    """Test için örnek malzemeler"""
    malzemeler = [
        {"name": "domates", "miktar": 5, "birim": "adet"},
        {"name": "soğan", "miktar": 2, "birim": "kg"},
        {"name": "biber", "miktar": 3, "birim": "adet"}
    ]
    
    for malzeme in malzemeler:
        client.post(
            "/api/malzeme/ekle",
            json=malzeme,
            headers=get_auth_headers(auth_token)
        )
    
    return malzemeler


class TestCriticalFeatures:
    """Kritik özellikler - Bunlar asla bozulmamalı"""
    
    def test_health_check(self):
        """Health check her zaman çalışmalı - AUTH GEREKMİYOR"""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    
    def test_malzeme_ekleme_ve_listeleme(self, auth_token):
        """Malzeme ekleme ve listeleme temel özellik"""
        # Ekle
        add_response = client.post(
            "/api/malzeme/ekle",
            json={"name": "test_malzeme", "miktar": 1, "birim": "adet"},
            headers=get_auth_headers(auth_token)  # ✅ Token ekle
        )
        assert add_response.status_code == 200
        
        # Listede olmalı
        list_response = client.get(
            "/api/malzeme/liste",
            headers=get_auth_headers(auth_token)  # ✅ Token ekle
        )
        assert list_response.status_code == 200
        malzemeler = list_response.json()["malzemeler"]
        assert any(m["name"] == "test_malzeme" for m in malzemeler)
    
    
    def test_alisveris_listesi_olusturma(self, auth_token, sample_malzemeler):
        """Alışveriş listesi oluşturma kritik"""
        response = client.post(
            "/api/alisveris/olustur",
            json={
                "malzemeler": [
                    "domates - 5 adet",
                    "yumurta - 6 adet"  # Bu eksik
                ]
            },
            headers=get_auth_headers(auth_token)  # ✅ Token ekle
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "liste_id" in data
        assert len(data["eksik_malzemeler"]) > 0  # Yumurta eksik olmalı
    
    
    def test_favori_ekleme_ve_silme(self, auth_token):
        """Favori ekleme ve silme kritik"""
        tarif = {
            "baslik": "Test Tarif",
            "malzemeler": ["test - 1 adet"],
            "adimlar": ["Test adım"]
        }
        
        # Ekle
        add_response = client.post(
            "/api/favoriler/ekle",
            json={"tarif": tarif},
            headers=get_auth_headers(auth_token)  # ✅ Token ekle
        )
        assert add_response.status_code == 200
        favori_id = add_response.json()["favori_id"]
        
        # Sil
        delete_response = client.delete(
            f"/api/favoriler/{favori_id}",
            headers=get_auth_headers(auth_token)  # ✅ Token ekle
        )
        assert delete_response.status_code == 200


class TestBackwardCompatibility:
    """Geriye dönük uyumluluk - Eski özellikler çalışmalı"""
    
    def test_old_api_endpoints_still_work(self, auth_token):
        """Eski API endpoint'leri hala çalışmalı"""
        # Health check (v1'den beri var) - AUTH GEREKMİYOR
        response = client.get("/api/health")
        assert response.status_code == 200
        
        # Malzeme listesi (v1'den beri var) - AUTH GEREKİYOR
        response = client.get(
            "/api/malzeme/liste",
            headers=get_auth_headers(auth_token)
        )
        assert response.status_code == 200
        assert "malzemeler" in response.json()
    
    
    def test_response_format_unchanged(self, auth_token):
        """Response formatı değişmemeli (breaking change olmasın)"""
        response = client.get(
            "/api/malzeme/liste",
            headers=get_auth_headers(auth_token)  # ✅ Token ekle
        )
        data = response.json()
        
        # Eski format: {"malzemeler": [...]}
        assert "malzemeler" in data
        assert isinstance(data["malzemeler"], list)
        
        # Eğer malzeme varsa, her birinin id, name, miktar, birim olmalı
        if len(data["malzemeler"]) > 0:
            malzeme = data["malzemeler"][0]
            assert "id" in malzeme
            assert "name" in malzeme
            assert "miktar" in malzeme
            assert "birim" in malzeme


class TestEdgeCases:
    """Kenar durumlar - Beklenmedik inputlar"""

    def test_cok_uzun_malzeme_adi(self, auth_token):
        """Çok uzun malzeme adı"""
        long_name = "a" * 1000
        response = client.post(
            "/api/malzeme/ekle",
            json={"name": long_name, "miktar": 1, "birim": "adet"},
            headers=get_auth_headers(auth_token)  # ✅ Token ekle
        )
        # 422 beklenir (max_length=100 validasyonu)
        assert response.status_code == 422

    def test_ozel_karakterler_malzeme_adi(self, auth_token):
        """Özel karakterlerle malzeme adı"""
        response = client.post(
            "/api/malzeme/ekle",
            json={"name": "domates🍅", "miktar": 1, "birim": "adet"},
            headers=get_auth_headers(auth_token)  # ✅ Token ekle
        )
        # Emoji'ler geçerli, başarılı olmalı
        assert response.status_code == 200

    def test_bos_alisveris_listesi(self, auth_token):
        """Boş malzeme listesiyle alışveriş listesi oluşturma"""
        response = client.post(
            "/api/alisveris/olustur",
            json={"malzemeler": []},
            headers=get_auth_headers(auth_token)  # ✅ Token ekle
        )
        # 400 Bad Request beklenir (malzemeler boş)
        assert response.status_code == 400

    def test_negatif_miktar_alisveris(self, auth_token):
        """Negatif miktarla ürün ekleme"""
        # Önce bir liste oluştur
        list_response = client.post(
            "/api/alisveris/olustur",
            json={"malzemeler": ["test - 1 adet"]},
            headers=get_auth_headers(auth_token)
        )
        liste_id = list_response.json()["liste_id"]

        # Negatif miktar ile ürün eklemeye çalış
        response = client.post(
            f"/api/alisveris/{liste_id}/urun",
            json={
                "malzeme_adi": "test",
                "miktar": -5,
                "birim": "adet"
            },
            headers=get_auth_headers(auth_token)  # ✅ Token ekle
        )
        # 422 beklenir (gt=0 validasyonu)
        assert response.status_code == 422


class TestPerformance:
    """Performans testleri - Basit metrikler"""
    
    def test_coklu_malzeme_ekleme_performansi(self, auth_token):
        """100 malzeme eklemek hızlı olmalı"""
        import time
        
        start = time.time()
        
        for i in range(100):
            client.post(
                "/api/malzeme/ekle",
                json={"name": f"malzeme_{i}", "miktar": 1, "birim": "adet"},
                headers=get_auth_headers(auth_token)  # ✅ Token ekle
            )
        
        elapsed = time.time() - start
        
        # 100 ekleme 10 saniyeden az sürmeli
        assert elapsed < 10, f"100 malzeme eklemek {elapsed:.2f}s sürdü"
    
    
    def test_liste_performansi(self, auth_token, sample_malzemeler):
        """Listeleme hızlı olmalı"""
        import time
        
        start = time.time()
        response = client.get(
            "/api/malzeme/liste",
            headers=get_auth_headers(auth_token)  # ✅ Token ekle
        )
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 1, f"Listeleme {elapsed:.2f}s sürdü"


# Test çalıştırma
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
