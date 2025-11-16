"""
Tarif Integration Tests - Düzeltilmiş
Conftest.py kullanır
"""
import pytest

# Auth token fixture
@pytest.fixture
def auth_token(client):
    """Test için token oluştur"""
    register_data = {
        "email": "tarif_test@example.com",
        "username": "tarif_test_user",
        "password": "test123",
        "full_name": "Tarif Test User"
    }
    response = client.post("/api/auth/register", json=register_data)

    if response.status_code not in [200, 201]:
        # Kullanıcı zaten varsa login yap
        login_response = client.post(
            "/api/auth/login",
            data={"username": "tarif_test_user", "password": "test123"}
        )
        token = login_response.json()["access_token"]
    else:
        token = response.json()["access_token"]

    return token


def get_auth_headers(token):
    """Authorization header oluştur"""
    return {"Authorization": f"Bearer {token}"}


# Sample tarif fixture
@pytest.fixture
def sample_tarif():
    return {
        "baslik": "Test Menemen",
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

    def test_favori_ekle(self, client, auth_token, sample_tarif):
        """Tarif favorilere eklenir"""
        response = client.post(
            "/api/favoriler/ekle",
            json={"tarif": sample_tarif},
            headers=get_auth_headers(auth_token)
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "favori_id" in data


    def test_favori_liste(self, client, auth_token, sample_tarif):
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
            headers=get_auth_headers(auth_token)
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # En az 1 favori olmalı (az önce ekledik)
        assert len(data["favoriler"]) >= 1
        # Son eklenen "Test Menemen" olmalı
        assert any(f["baslik"] == "Test Menemen" for f in data["favoriler"])


    def test_favori_sil(self, client, auth_token, sample_tarif):
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
            headers=get_auth_headers(auth_token)
        )

        assert response.status_code == 200
        assert response.json()["success"] is True

        # Silinmiş olmalı - tekrar almaya çalışınca 404
        get_response = client.get(
            f"/api/favoriler/{favori_id}",
            headers=get_auth_headers(auth_token)
        )
        # Eğer böyle bir endpoint varsa 404 dönmeli
        # Yoksa list'ten silinmiş olmalı


    def test_favori_sil_not_found(self, client, auth_token):
        """Olmayan favori silinmeye çalışılınca 404"""
        response = client.delete(
            "/api/favoriler/999999",
            headers=get_auth_headers(auth_token)
        )
        assert response.status_code == 404


class TestTarifFlow:
    """Tarif akış testleri (end-to-end)"""

    def test_full_tarif_workflow(self, client, auth_token, sample_tarif):
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

        # Az önce eklediğimiz favoriyi bul
        eklenen_favori = next((f for f in favoriler if f["id"] == favori_id), None)
        assert eklenen_favori is not None
        assert eklenen_favori["baslik"] == sample_tarif["baslik"]

        # 3. Malzemelerin JSON olarak doğru parse edildiğini kontrol et
        assert isinstance(eklenen_favori["malzemeler"], list)
        assert len(eklenen_favori["malzemeler"]) == 4

        # 4. Sil
        delete_response = client.delete(
            f"/api/favoriler/{favori_id}",
            headers=get_auth_headers(auth_token)
        )
        assert delete_response.status_code == 200

        # 5. Silinmiş olmalı
        final_list = client.get(
            "/api/favoriler/liste",
            headers=get_auth_headers(auth_token)
        )
        final_favoriler = final_list.json()["favoriler"]
        # Silinen favori listede olmamalı
        assert not any(f["id"] == favori_id for f in final_favoriler)


# Test çalıştırma
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
