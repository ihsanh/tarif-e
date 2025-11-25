"""
Malzeme API Testleri - Düzeltilmiş (conftest.py kullanır)
"""
import pytest

# Test kullanıcısı oluştur ve token al
@pytest.fixture
def auth_token(client):
    """Test için token oluştur"""
    # Önce kullanıcı oluştur
    register_data = {
        "email": "test_malzeme@example.com",
        "username": "test_malzeme_user",
        "password": "test123"
    }
    register_response = client.post("/api/auth/register", json=register_data)

    # Eğer kullanıcı zaten varsa (409), devam et
    if register_response.status_code not in [200, 201, 409]:
        print(f"⚠️ Register failed: {register_response.json()}")

    # Login yap
    login_data = {
        "username": "test_malzeme_user",
        "password": "test123"
    }
    response = client.post("/api/auth/login", data=login_data)  # ✅ data= (FormData)

    if response.status_code != 200:
        print(f"❌ Login failed: {response.json()}")
        pytest.fail("Login başarısız")

    token = response.json()["access_token"]
    return token


# Auth headers helper
def get_auth_headers(token):
    """Authorization header oluştur"""
    return {"Authorization": f"Bearer {token}"}


class TestMalzemeValidation:
    """Malzeme validasyon testleri"""

    def test_malzeme_ekle_basarili(self, client, auth_token):
        """Başarılı malzeme ekleme"""
        data = {
            "name": "domates",
            "miktar": 5,
            "birim": "adet"
        }
        response = client.post(
            "/api/malzeme/ekle",
            json=data,
            headers=get_auth_headers(auth_token)
        )

        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "domates" in result["message"].lower()

    def test_malzeme_ekle_bos_name(self, client, auth_token):
        """Boş isimle malzeme ekleme - hata vermeli"""
        data = {
            "name": "",  # Boş isim
            "miktar": 5,
            "birim": "adet"
        }
        response = client.post(
            "/api/malzeme/ekle",
            json=data,
            headers=get_auth_headers(auth_token)
        )

        assert response.status_code == 422  # Validation error

    def test_malzeme_ekle_negatif_miktar(self, client, auth_token):
        """Negatif miktarla malzeme ekleme - hata vermeli"""
        data = {
            "name": "soğan",
            "miktar": -5,  # Negatif miktar
            "birim": "kg"
        }
        response = client.post(
            "/api/malzeme/ekle",
            json=data,
            headers=get_auth_headers(auth_token)
        )

        assert response.status_code == 422  # Validation error


class TestMalzemeListeleme:
    """Malzeme listeleme testleri"""

    def test_malzeme_liste_bos(self, client, auth_token):
        """Boş malzeme listesi"""
        response = client.get(
            "/api/malzeme/liste",
            headers=get_auth_headers(auth_token)
        )

        assert response.status_code == 200
        result = response.json()
        assert "malzemeler" in result
        # Liste boş olabilir veya olmayabilir (önceki testlerden kalma)
        assert isinstance(result["malzemeler"], list)

    def test_malzeme_liste_dolu(self, client, auth_token):
        """Malzemeler eklenmiş liste"""
        # Önce malzeme ekle
        malzemeler = [
            {"name": "test_domates", "miktar": 3, "birim": "adet"},
            {"name": "test_soğan", "miktar": 2, "birim": "kg"}
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
            headers=get_auth_headers(auth_token)
        )

        assert response.status_code == 200
        result = response.json()
        # En az 2 malzeme olmalı (az önce eklediklerimiz)
        assert len(result["malzemeler"]) >= 2


class TestMalzemeGuncelleme:
    """Malzeme güncelleme testleri"""

    def test_malzeme_guncelle_basarili(self, client, auth_token):
        """Başarılı malzeme güncelleme"""
        # Önce malzeme ekle
        data = {"name": "test_update_domates", "miktar": 3, "birim": "adet"}
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
            headers=get_auth_headers(auth_token)
        )

        assert response.status_code == 200
        result = response.json()
        assert result["malzeme"]["miktar"] == 5
        assert result["malzeme"]["birim"] == "kg"

    def test_malzeme_guncelle_olmayan_id(self, client, auth_token):
        """Olmayan ID ile güncelleme - 404 dönmeli"""
        update_data = {"miktar": 5, "birim": "kg"}
        response = client.put(
            "/api/malzeme/99999",  # Olmayan ID
            json=update_data,
            headers=get_auth_headers(auth_token)
        )

        assert response.status_code == 404


class TestMalzemeSilme:
    """Malzeme silme testleri"""

    def test_malzeme_sil_basarili(self, client, auth_token):
        """Başarılı malzeme silme"""
        # Önce malzeme ekle
        data = {"name": "test_delete_domates", "miktar": 3, "birim": "adet"}
        add_response = client.post(
            "/api/malzeme/ekle",
            json=data,
            headers=get_auth_headers(auth_token)
        )
        malzeme_id = add_response.json()["malzeme"]["id"]

        # Sil
        response = client.delete(
            f"/api/malzeme/{malzeme_id}",
            headers=get_auth_headers(auth_token)
        )

        assert response.status_code == 200
        assert response.json()["success"] is True

        # Silinmiş olmalı - tekrar almaya çalışınca 404
        list_response = client.get(
            "/api/malzeme/liste",
            headers=get_auth_headers(auth_token)
        )
        malzemeler = list_response.json()["malzemeler"]
        assert not any(m["id"] == malzeme_id for m in malzemeler)

    def test_malzeme_sil_olmayan_id(self, client, auth_token):
        """Olmayan ID ile silme - 404 dönmeli"""
        response = client.delete(
            "/api/malzeme/99999",  # Olmayan ID
            headers=get_auth_headers(auth_token)
        )

        assert response.status_code == 404


# Test çalıştırma
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
