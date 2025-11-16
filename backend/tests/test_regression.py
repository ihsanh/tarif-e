"""
Regression Tests - Kritik özelliklerin çalıştığını garanti et
Düzeltilmiş: conftest.py kullanır
"""
import pytest

# ❌ BUNLARI KALDIR - conftest.py halledecek
# from fastapi.testclient import TestClient
# from app.main import app
# from app.database import Base, engine
# client = TestClient(app)


# Auth token fixture
@pytest.fixture
def auth_token(client):
    """Test için token oluştur"""
    register_data = {
        "email": "regression@example.com",
        "username": "regression_user",
        "password": "test123"
    }
    response = client.post("/api/auth/register", json=register_data)

    if response.status_code not in [200, 201]:
        # Kullanıcı zaten varsa login yap
        login_response = client.post(
            "/api/auth/login",
            data={"username": "regression_user", "password": "test123"}
        )
        token = login_response.json()["access_token"]
    else:
        token = response.json()["access_token"]

    return token


def get_auth_headers(token):
    """Authorization header oluştur"""
    return {"Authorization": f"Bearer {token}"}


# Sample malzemeler fixture
@pytest.fixture
def sample_malzemeler(client, auth_token):
    """Test için örnek malzemeler"""
    malzemeler = [
        {"name": "regression_domates", "miktar": 5, "birim": "adet"},
        {"name": "regression_soğan", "miktar": 2, "birim": "kg"},
        {"name": "regression_biber", "miktar": 3, "birim": "adet"}
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

    def test_health_check(self, client):
        """Health check her zaman çalışmalı - AUTH GEREKMİYOR"""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


    def test_malzeme_ekleme_ve_listeleme(self, client, auth_token):
        """Malzeme ekleme ve listeleme temel özellik"""
        # Ekle
        add_response = client.post(
            "/api/malzeme/ekle",
            json={"name": "regression_test_malzeme", "miktar": 1, "birim": "adet"},
            headers=get_auth_headers(auth_token)
        )
        assert add_response.status_code == 200

        # Listede olmalı
        list_response = client.get(
            "/api/malzeme/liste",
            headers=get_auth_headers(auth_token)
        )
        assert list_response.status_code == 200
        malzemeler = list_response.json()["malzemeler"]
        assert any(m["name"] == "regression_test_malzeme" for m in malzemeler)


    def test_alisveris_listesi_olusturma(self, client, auth_token, sample_malzemeler):
        """Alışveriş listesi oluşturma kritik"""
        response = client.post(
            "/api/alisveris/olustur",
            json={
                "baslik": "Regression Test Listesi",
                "malzemeler": [
                    "regression_domates - 5 adet",
                    "yumurta - 6 adet"  # Bu eksik
                ]
            },
            headers=get_auth_headers(auth_token)
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "liste_id" in data
        assert len(data["eksik_malzemeler"]) > 0  # Yumurta eksik olmalı


    def test_favori_ekleme_ve_silme(self, client, auth_token):
        """Favori ekleme ve silme kritik"""
        tarif = {
            "baslik": "Regression Test Tarif",
            "malzemeler": ["test - 1 adet"],
            "adimlar": ["Test adım"]
        }

        # Ekle
        add_response = client.post(
            "/api/favoriler/ekle",
            json={"tarif": tarif},
            headers=get_auth_headers(auth_token)
        )
        assert add_response.status_code == 200
        favori_id = add_response.json()["favori_id"]

        # Sil
        delete_response = client.delete(
            f"/api/favoriler/{favori_id}",
            headers=get_auth_headers(auth_token)
        )
        assert delete_response.status_code == 200


class TestBackwardCompatibility:
    """Geriye dönük uyumluluk - Eski özellikler çalışmalı"""

    def test_old_api_endpoints_still_work(self, client, auth_token):
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


    def test_response_format_unchanged(self, client, auth_token):
        """Response formatı değişmemeli (breaking change olmasın)"""
        response = client.get(
            "/api/malzeme/liste",
            headers=get_auth_headers(auth_token)
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

    def test_cok_uzun_malzeme_adi(self, client, auth_token):
        """Çok uzun malzeme adı"""
        long_name = "a" * 1000
        response = client.post(
            "/api/malzeme/ekle",
            json={"name": long_name, "miktar": 1, "birim": "adet"},
            headers=get_auth_headers(auth_token)
        )
        # 422 beklenir (max_length=100 validasyonu)
        assert response.status_code == 422

    def test_ozel_karakterler_malzeme_adi(self, client, auth_token):
        """Özel karakterlerle malzeme adı"""
        response = client.post(
            "/api/malzeme/ekle",
            json={"name": "domates🍅", "miktar": 1, "birim": "adet"},
            headers=get_auth_headers(auth_token)
        )
        # Emoji'ler geçerli, başarılı olmalı
        assert response.status_code == 200

    def test_bos_alisveris_listesi(self, client, auth_token):
        """Boş malzeme listesiyle alışveriş listesi oluşturma"""
        response = client.post(
            "/api/alisveris/olustur",
            json={"baslik": "Boş Liste", "malzemeler": []},
            headers=get_auth_headers(auth_token)
        )
        # 400 Bad Request beklenir (malzemeler boş)
        assert response.status_code in [400, 422]

    def test_negatif_miktar_alisveris(self, client, auth_token):
        """Negatif miktarla ürün ekleme"""
        # Önce bir liste oluştur
        list_response = client.post(
            "/api/alisveris/olustur",
            json={"baslik": "Test", "malzemeler": ["test - 1 adet"]},
            headers=get_auth_headers(auth_token)
        )
        # ✅ ÖNCE: Liste oluşturuldu mu kontrol et
        if list_response.status_code != 200:
            pytest.skip("Liste oluşturulamadı")

        data = list_response.json()

        # ✅ liste_id var mı kontrol et
        if "liste_id" not in data:
            pytest.skip("liste_id bulunamadı")

        liste_id = data["liste_id"]

        # Negatif miktar ile ürün eklemeye çalış
        response = client.post(
            f"/api/alisveris/{liste_id}/urun",
            json={
                "malzeme_adi": "test",
                "miktar": -5,
                "birim": "adet"
            },
            headers=get_auth_headers(auth_token)
        )
        # 422 beklenir (gt=0 validasyonu)
        assert response.status_code == 422


class TestPerformance:
    """Performans testleri - Basit metrikler"""

    def test_coklu_malzeme_ekleme_performansi(self, client, auth_token):
        """100 malzeme eklemek hızlı olmalı"""
        import time

        start = time.time()

        for i in range(100):
            client.post(
                "/api/malzeme/ekle",
                json={"name": f"perf_malzeme_{i}", "miktar": 1, "birim": "adet"},
                headers=get_auth_headers(auth_token)
            )

        elapsed = time.time() - start

        # 100 ekleme 10 saniyeden az sürmeli
        assert elapsed < 10, f"100 malzeme eklemek {elapsed:.2f}s sürdü"


    def test_liste_performansi(self, client, auth_token, sample_malzemeler):
        """Listeleme hızlı olmalı"""
        import time

        start = time.time()
        response = client.get(
            "/api/malzeme/liste",
            headers=get_auth_headers(auth_token)
        )
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 1, f"Listeleme {elapsed:.2f}s sürdü"


# Test çalıştırma
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
