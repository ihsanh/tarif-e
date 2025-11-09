"""
Malzeme API Testleri - Auth Güncellenmiş
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db, Base, engine

client = TestClient(app)

# Test veritabanını sıfırla
@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


# Test kullanıcısı oluştur ve token al
@pytest.fixture
def auth_token():
    """Test için token oluştur"""
    # Önce kullanıcı oluştur (sadece 1 kere)
    register_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "test123"
    }
    client.post("/api/auth/register", json=register_data)

    # Sonra login yap
    login_data = {
        "username": "testuser",
        "password": "test123"
    }
    response = client.post("/api/auth/login", data=login_data)  # ✅ data= (FormData)
    assert response.status_code == 200

    token = response.json()["access_token"]
    return token


# Auth headers helper
def get_auth_headers(token):
    """Authorization header oluştur"""
    return {"Authorization": f"Bearer {token}"}


class TestMalzemeValidation:
    """Malzeme validasyon testleri"""

    def test_malzeme_ekle_basarili(self, auth_token):
        """Başarılı malzeme ekleme"""
        data = {
            "name": "domates",
            "miktar": 5,
            "birim": "adet"
        }
        response = client.post(
            "/api/malzeme/ekle",
            json=data,
            headers=get_auth_headers(auth_token)  # ✅ Token ekle
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "domates" in result["message"].lower()

    def test_malzeme_ekle_bos_name(self, auth_token):
        """Boş isimle malzeme ekleme - hata vermeli"""
        data = {
            "name": "",  # Boş isim
            "miktar": 5,
            "birim": "adet"
        }
        response = client.post(
            "/api/malzeme/ekle",
            json=data,
            headers=get_auth_headers(auth_token)  # ✅ Token ekle
        )
        
        assert response.status_code == 422  # Validation error

    def test_malzeme_ekle_negatif_miktar(self, auth_token):
        """Negatif miktarla malzeme ekleme - hata vermeli"""
        data = {
            "name": "soğan",
            "miktar": -5,  # Negatif miktar
            "birim": "kg"
        }
        response = client.post(
            "/api/malzeme/ekle",
            json=data,
            headers=get_auth_headers(auth_token)  # ✅ Token ekle
        )
        
        assert response.status_code == 422  # Validation error


class TestMalzemeListeleme:
    """Malzeme listeleme testleri"""

    def test_malzeme_liste_bos(self, auth_token):
        """Boş malzeme listesi"""
        response = client.get(
            "/api/malzeme/liste",
            headers=get_auth_headers(auth_token)  # ✅ Token ekle
        )
        
        assert response.status_code == 200
        result = response.json()
        assert "malzemeler" in result
        assert len(result["malzemeler"]) == 0

    def test_malzeme_liste_dolu(self, auth_token):
        """Malzemeler eklenmiş liste"""
        # Önce malzeme ekle
        malzemeler = [
            {"name": "domates", "miktar": 3, "birim": "adet"},
            {"name": "soğan", "miktar": 2, "birim": "kg"}
        ]
        
        for malzeme in malzemeler:
            client.post(
                "/api/malzeme/ekle",
                json=malzeme,
                headers=get_auth_headers(auth_token)
            )
        
        # Listeyi al
        response = client.get(
            "/api/malzeme/liste",
            headers=get_auth_headers(auth_token)  # ✅ Token ekle
        )
        
        assert response.status_code == 200
        result = response.json()
        assert len(result["malzemeler"]) == 2


class TestMalzemeGuncelleme:
    """Malzeme güncelleme testleri"""

    def test_malzeme_guncelle_basarili(self, auth_token):
        """Başarılı malzeme güncelleme"""
        # Önce malzeme ekle
        data = {"name": "domates", "miktar": 3, "birim": "adet"}
        add_response = client.post(
            "/api/malzeme/ekle",
            json=data,
            headers=get_auth_headers(auth_token)
        )
        malzeme_id = add_response.json()["malzeme"]["id"]
        
        # Güncelle
        update_data = {"miktar": 5, "birim": "kg"}
        response = client.put(
            f"/api/malzeme/{malzeme_id}",
            json=update_data,
            headers=get_auth_headers(auth_token)  # ✅ Token ekle
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["malzeme"]["miktar"] == 5
        assert result["malzeme"]["birim"] == "kg"

    def test_malzeme_guncelle_olmayan_id(self, auth_token):
        """Olmayan ID ile güncelleme - 404 dönmeli"""
        update_data = {"miktar": 5, "birim": "kg"}
        response = client.put(
            "/api/malzeme/99999",  # Olmayan ID
            json=update_data,
            headers=get_auth_headers(auth_token)  # ✅ Token ekle
        )
        
        assert response.status_code == 404


class TestMalzemeSilme:
    """Malzeme silme testleri"""

    def test_malzeme_sil_basarili(self, auth_token):
        """Başarılı malzeme silme"""
        # Önce malzeme ekle
        data = {"name": "domates", "miktar": 3, "birim": "adet"}
        add_response = client.post(
            "/api/malzeme/ekle",
            json=data,
            headers=get_auth_headers(auth_token)
        )
        malzeme_id = add_response.json()["malzeme"]["id"]
        
        # Sil
        response = client.delete(
            f"/api/malzeme/{malzeme_id}",
            headers=get_auth_headers(auth_token)  # ✅ Token ekle
        )
        
        assert response.status_code == 200
        assert response.json()["success"] is True
        
        # Listede olmamalı
        list_response = client.get(
            "/api/malzeme/liste",
            headers=get_auth_headers(auth_token)
        )
        assert len(list_response.json()["malzemeler"]) == 0

    def test_malzeme_sil_olmayan_id(self, auth_token):
        """Olmayan ID ile silme - 404 dönmeli"""
        response = client.delete(
            "/api/malzeme/99999",  # Olmayan ID
            headers=get_auth_headers(auth_token)  # ✅ Token ekle
        )
        
        assert response.status_code == 404


# Test çalıştırma
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
