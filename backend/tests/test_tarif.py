"""
Tarif Integration Tests - Auth Güncellenmiş
"""
import pytest
import json
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
        "password": "test123",
        "full_name": "Test User"
    }
    response = client.post("/api/auth/register", json=register_data)
    assert response.status_code == 201
    
    token = response.json()["access_token"]
    return token


def get_auth_headers(token):
    """Authorization header oluştur"""
    return {"Authorization": f"Bearer {token}"}


# Sample tarif fixture
@pytest.fixture
def sample_tarif():
    return {
        "baslik": "Menemen",
        "aciklama": "Klasik Türk kahvaltısı",
        "malzemeler": [
            "domates - 2 adet",
            "biber - 1 adet",
            "yumurta - 3 adet",
            "soğan - 1 adet"
        ],
        "adimlar": [
            "Soğanı doğrayın",
            "Biberleri ekleyin",
            "Domatesleri ekleyin",
            "Yumurtaları çırpın"
        ],
        "sure": "15 dakika",
        "zorluk": "kolay",
        "kategori": "kahvaltı"
    }


class TestTarifAPI:
    """Tarif API testleri"""
    
    def test_favori_ekle(self, auth_token, sample_tarif):
        """Tarif favorilere eklenir"""
        response = client.post(
            "/api/favoriler/ekle",
            json={"tarif": sample_tarif},
            headers=get_auth_headers(auth_token)  # ✅ Token ekle
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "favori_id" in data
    
    
    def test_favori_liste(self, auth_token, sample_tarif):
        """Favoriler listelenir"""
        # Önce ekle
        client.post(
            "/api/favoriler/ekle",
            json={"tarif": sample_tarif},
            headers=get_auth_headers(auth_token)
        )
        
        # Listele
        response = client.get(
            "/api/favoriler/liste",
            headers=get_auth_headers(auth_token)  # ✅ Token ekle
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["favoriler"]) == 1
        assert data["favoriler"][0]["baslik"] == "Menemen"
    
    
    def test_favori_sil(self, auth_token, sample_tarif):
        """Favori silinir"""
        # Önce ekle
        add_response = client.post(
            "/api/favoriler/ekle",
            json={"tarif": sample_tarif},
            headers=get_auth_headers(auth_token)
        )
        favori_id = add_response.json()["favori_id"]
        
        # Sil
        response = client.delete(
            f"/api/favoriler/{favori_id}",
            headers=get_auth_headers(auth_token)  # ✅ Token ekle
        )
        
        assert response.status_code == 200
        assert response.json()["success"] is True
        
        # Liste boş olmalı
        list_response = client.get(
            "/api/favoriler/liste",
            headers=get_auth_headers(auth_token)
        )
        assert len(list_response.json()["favoriler"]) == 0
    
    
    def test_favori_sil_not_found(self, auth_token):
        """Olmayan favori silinmeye çalışılınca 404"""
        response = client.delete(
            "/api/favoriler/999",
            headers=get_auth_headers(auth_token)  # ✅ Token ekle
        )
        assert response.status_code == 404


class TestTarifFlow:
    """Tarif akış testleri (end-to-end)"""
    
    def test_full_tarif_workflow(self, auth_token, sample_tarif):
        """Tam tarif iş akışı"""
        # 1. Favoriye ekle
        add_response = client.post(
            "/api/favoriler/ekle",
            json={"tarif": sample_tarif},
            headers=get_auth_headers(auth_token)
        )
        assert add_response.status_code == 200
        favori_id = add_response.json()["favori_id"]
        
        # 2. Listede görün
        list_response = client.get(
            "/api/favoriler/liste",
            headers=get_auth_headers(auth_token)
        )
        favoriler = list_response.json()["favoriler"]
        assert len(favoriler) == 1
        assert favoriler[0]["id"] == favori_id
        assert favoriler[0]["baslik"] == sample_tarif["baslik"]
        
        # 3. Malzemelerin JSON olarak doğru parse edildiğini kontrol et
        assert isinstance(favoriler[0]["malzemeler"], list)
        assert len(favoriler[0]["malzemeler"]) == 4
        
        # 4. Sil
        delete_response = client.delete(
            f"/api/favoriler/{favori_id}",
            headers=get_auth_headers(auth_token)
        )
        assert delete_response.status_code == 200
        
        # 5. Liste boş
        final_list = client.get(
            "/api/favoriler/liste",
            headers=get_auth_headers(auth_token)
        )
        assert len(final_list.json()["favoriler"]) == 0


# Test çalıştırma
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
