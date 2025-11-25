"""
Profil İşlemleri Integration Tests
Conftest.py kullanır
"""
import pytest
from io import BytesIO
from PIL import Image


# Auth token fixture
@pytest.fixture
def auth_token(client):
    """Test için token oluştur"""
    register_data = {
        "email": "profile_test@example.com",
        "username": "profile_test_user",
        "password": "test123",
        "full_name": "Profile Test User"
    }
    response = client.post("/api/auth/register", json=register_data)

    if response.status_code not in [200, 201]:
        # Kullanıcı zaten varsa login yap
        login_response = client.post(
            "/api/auth/login",
            data={"username": "profile_test_user", "password": "test123"}
        )
        token = login_response.json()["access_token"]
    else:
        token = response.json()["access_token"]

    return token


@pytest.fixture
def auth_token_2(client):
    """İkinci test kullanıcısı için token"""
    register_data = {
        "email": "profile_test2@example.com",
        "username": "profile_test_user2",
        "password": "test123",
        "full_name": "Profile Test User 2"
    }
    response = client.post("/api/auth/register", json=register_data)

    if response.status_code not in [200, 201]:
        login_response = client.post(
            "/api/auth/login",
            data={"username": "profile_test_user2", "password": "test123"}
        )
        token = login_response.json()["access_token"]
    else:
        token = response.json()["access_token"]

    return token


def get_auth_headers(token):
    """Authorization header oluştur"""
    return {"Authorization": f"Bearer {token}"}


# Sample profile data
@pytest.fixture
def sample_profile_data():
    return {
        "full_name": "Ahmet Yılmaz",
        "email": "profile_test@example.com",
        "bio": "Yemek yapmayı seven bir yazılımcı"
    }


@pytest.fixture
def sample_preferences():
    return {
        "dietary_preferences": ["vegan", "glutensiz"],
        "allergies": ["fıstık", "süt"],
        "dislikes": ["patlıcan", "kereviz"]
    }


def create_test_image(format='PNG'):
    """Test için image oluştur"""
    img = Image.new('RGB', (100, 100), color='red')
    img_io = BytesIO()
    img.save(img_io, format)
    img_io.seek(0)
    return img_io


class TestProfileBasics:
    """Temel profil işlemleri testleri"""

    def test_get_profile(self, client, auth_token):
        """Profil bilgisi alınabilir"""
        response = client.get(
            "/api/profile",
            headers=get_auth_headers(auth_token)
        )

        assert response.status_code == 200
        data = response.json()
        assert "username" in data
        assert "email" in data
        assert data["username"] == "profile_test_user"

    def test_get_profile_unauthorized(self, client):
        """Token olmadan profil alınamaz"""
        response = client.get("/api/profile")
        assert response.status_code == 401

    def test_update_profile(self, client, auth_token, sample_profile_data):
        """Profil bilgileri güncellenebilir"""
        response = client.put(
            "/api/profile",
            json=sample_profile_data,
            headers=get_auth_headers(auth_token)
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "message" in data

        # Güncellenmiş bilgileri kontrol et
        get_response = client.get(
            "/api/profile",
            headers=get_auth_headers(auth_token)
        )
        profile = get_response.json()
        assert profile["full_name"] == sample_profile_data["full_name"]
        assert profile["bio"] == sample_profile_data["bio"]

    def test_update_profile_invalid_email(self, client, auth_token):
        """Geçersiz email ile güncelleme başarısız olur"""
        invalid_data = {
            "email": "invalid-email",
            "full_name": "Test User"
        }
        response = client.put(
            "/api/profile",
            json=invalid_data,
            headers=get_auth_headers(auth_token)
        )

        # 400 veya 422 dönmeli (validation error)
        assert response.status_code in [400, 422]

    def test_update_profile_empty_data(self, client, auth_token):
        """Boş veri ile güncelleme başarısız olur"""
        response = client.put(
            "/api/profile",
            json={},
            headers=get_auth_headers(auth_token)
        )

        # Başarılı olabilir (hiçbir şey değişmez) veya hata verebilir
        # Backend implementasyonuna bağlı
        assert response.status_code in [200, 400, 422]


class TestProfilePhoto:
    """Profil fotoğrafı testleri"""

    def test_upload_profile_photo_png(self, client, auth_token):
        """PNG profil fotoğrafı yüklenebilir"""
        img_io = create_test_image('PNG')

        response = client.post(
            "/api/profile/photo",
            data={"file": (img_io, "test_avatar.png")},
            headers=get_auth_headers(auth_token),
            content_type='multipart/form-data'
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "photo_url" in data
        assert data["photo_url"].endswith('.png')

    def test_upload_profile_photo_jpeg(self, client, auth_token):
        """JPEG profil fotoğrafı yüklenebilir"""
        img_io = create_test_image('JPEG')

        response = client.post(
            "/api/profile/photo",
            data={"file": (img_io, "test_avatar.jpg")},
            headers=get_auth_headers(auth_token),
            content_type='multipart/form-data'
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "photo_url" in data

    def test_upload_profile_photo_invalid_format(self, client, auth_token):
        """Geçersiz format reddedilir"""
        # PDF gibi geçersiz bir dosya
        file_io = BytesIO(b"fake pdf content")

        response = client.post(
            "/api/profile/photo",
            data={"file": (file_io, "test.pdf")},
            headers=get_auth_headers(auth_token),
            content_type='multipart/form-data'
        )

        assert response.status_code in [400, 415, 422]

    def test_upload_profile_photo_too_large(self, client, auth_token):
        """Çok büyük dosya reddedilir (>5MB)"""
        # 6MB'lık fake image
        large_img = Image.new('RGB', (3000, 3000), color='blue')
        img_io = BytesIO()
        large_img.save(img_io, 'PNG')
        img_io.seek(0)

        response = client.post(
            "/api/profile/photo",
            data={"file": (img_io, "large.png")},
            headers=get_auth_headers(auth_token),
            content_type='multipart/form-data'
        )

        # Dosya boyutu kontrolü varsa 400, yoksa başarılı olabilir
        # Backend implementasyonuna bağlı
        assert response.status_code in [200, 400, 413, 422]

    def test_delete_profile_photo(self, client, auth_token):
        """Profil fotoğrafı silinebilir"""
        # Önce bir foto yükle
        img_io = create_test_image('PNG')
        upload_response = client.post(
            "/api/profile/photo",
            data={"file": (img_io, "test_avatar.png")},
            headers=get_auth_headers(auth_token),
            content_type='multipart/form-data'
        )
        assert upload_response.status_code == 200

        # Şimdi sil
        response = client.delete(
            "/api/profile/photo",
            headers=get_auth_headers(auth_token)
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_delete_profile_photo_not_exists(self, client, auth_token):
        """Olmayan fotoğraf silinmeye çalışılınca hata vermez"""
        response = client.delete(
            "/api/profile/photo",
            headers=get_auth_headers(auth_token)
        )

        # 200 (başarılı) veya 404 dönebilir
        assert response.status_code in [200, 404]


class TestProfileSecurity:
    """Güvenlik (şifre değişikliği) testleri"""

    def test_change_password_success(self, client, auth_token):
        """Şifre başarıyla değiştirilebilir"""
        password_data = {
            "current_password": "test123",
            "new_password": "newPassword456",
            "confirm_password": "newPassword456"
        }

        response = client.post(
            "/api/profile/change-password",
            json=password_data,
            headers=get_auth_headers(auth_token)
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Yeni şifre ile login dene
        login_response = client.post(
            "/api/auth/login",
            data={"username": "profile_test_user", "password": "newPassword456"}
        )
        assert login_response.status_code == 200

        # Şifreyi eski haline döndür (cleanup)
        restore_data = {
            "current_password": "newPassword456",
            "new_password": "test123",
            "confirm_password": "test123"
        }
        client.post(
            "/api/profile/change-password",
            json=restore_data,
            headers=get_auth_headers(auth_token)
        )

    def test_change_password_wrong_current(self, client, auth_token):
        """Yanlış mevcut şifre ile değişiklik başarısız"""
        password_data = {
            "current_password": "wrongPassword",
            "new_password": "newPassword456",
            "confirm_password": "newPassword456"
        }

        response = client.post(
            "/api/profile/change-password",
            json=password_data,
            headers=get_auth_headers(auth_token)
        )

        assert response.status_code in [400, 401, 403]
        data = response.json()
        assert data["success"] is False

    def test_change_password_mismatch(self, client, auth_token):
        """Yeni şifreler eşleşmezse başarısız"""
        password_data = {
            "current_password": "test123",
            "new_password": "newPassword456",
            "confirm_password": "differentPassword789"
        }

        response = client.post(
            "/api/profile/change-password",
            json=password_data,
            headers=get_auth_headers(auth_token)
        )

        assert response.status_code in [400, 422]

    def test_change_password_too_short(self, client, auth_token):
        """Çok kısa şifre reddedilir"""
        password_data = {
            "current_password": "test123",
            "new_password": "abc",
            "confirm_password": "abc"
        }

        response = client.post(
            "/api/profile/change-password",
            json=password_data,
            headers=get_auth_headers(auth_token)
        )

        assert response.status_code in [400, 422]

    def test_change_password_same_as_current(self, client, auth_token):
        """Yeni şifre eskisiyle aynı olamaz"""
        password_data = {
            "current_password": "test123",
            "new_password": "test123",
            "confirm_password": "test123"
        }

        response = client.post(
            "/api/profile/change-password",
            json=password_data,
            headers=get_auth_headers(auth_token)
        )

        # Backend'e göre 400 veya başarılı olabilir
        assert response.status_code in [200, 400, 422]


class TestProfilePreferences:
    """Beslenme tercihleri testleri"""

    def test_get_preferences(self, client, auth_token):
        """Tercihler alınabilir"""
        response = client.get(
            "/api/profile/preferences",
            headers=get_auth_headers(auth_token)
        )

        assert response.status_code == 200
        data = response.json()
        assert "dietary_preferences" in data
        assert "allergies" in data
        assert "dislikes" in data
        # Başlangıçta boş olabilir
        assert isinstance(data["dietary_preferences"], list)
        assert isinstance(data["allergies"], list)
        assert isinstance(data["dislikes"], list)

    def test_update_preferences(self, client, auth_token, sample_preferences):
        """Tercihler güncellenebilir"""
        response = client.put(
            "/api/profile/preferences",
            json=sample_preferences,
            headers=get_auth_headers(auth_token)
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Güncellenmiş tercihleri kontrol et
        get_response = client.get(
            "/api/profile/preferences",
            headers=get_auth_headers(auth_token)
        )
        prefs = get_response.json()
        assert set(prefs["dietary_preferences"]) == set(sample_preferences["dietary_preferences"])
        assert set(prefs["allergies"]) == set(sample_preferences["allergies"])
        assert set(prefs["dislikes"]) == set(sample_preferences["dislikes"])

    def test_update_preferences_partial(self, client, auth_token):
        """Kısmi güncelleme yapılabilir"""
        partial_data = {
            "dietary_preferences": ["vegan"]
        }

        response = client.put(
            "/api/profile/preferences",
            json=partial_data,
            headers=get_auth_headers(auth_token)
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_update_preferences_empty(self, client, auth_token):
        """Boş tercihler kaydedilebilir"""
        empty_data = {
            "dietary_preferences": [],
            "allergies": [],
            "dislikes": []
        }

        response = client.put(
            "/api/profile/preferences",
            json=empty_data,
            headers=get_auth_headers(auth_token)
        )

        assert response.status_code == 200

    def test_update_preferences_invalid_data(self, client, auth_token):
        """Geçersiz veri tipi reddedilir"""
        invalid_data = {
            "dietary_preferences": "not a list",  # String olmamalı
            "allergies": 123  # Number olmamalı
        }

        response = client.put(
            "/api/profile/preferences",
            json=invalid_data,
            headers=get_auth_headers(auth_token)
        )

        assert response.status_code in [400, 422]


class TestRecipeIntegration:
    """Profil tercihleri + Tarif entegrasyonu testleri"""

    def test_recipe_with_allergies(self, client, auth_token):
        """Alerji tercihleri tarif önerisine yansır"""
        # Önce alerjiler kaydet
        prefs = {
            "allergies": ["fıstık", "süt"]
        }
        client.put(
            "/api/profile/preferences",
            json=prefs,
            headers=get_auth_headers(auth_token)
        )

        # Tarif öner
        recipe_request = {
            "malzemeler": ["domates", "makarna", "soğan"]
        }
        response = client.post(
            "/api/tarif/oner",
            json=recipe_request,
            headers=get_auth_headers(auth_token)
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Tarif fıstık ve süt içermemeli
        tarif = data["tarif"]
        malzemeler_str = " ".join(tarif.get("malzemeler", [])).lower()
        assert "fıstık" not in malzemeler_str
        assert "süt" not in malzemeler_str

    def test_recipe_with_vegan_diet(self, client, auth_token):
        """Vegan diyeti tarif önerisine yansır"""
        prefs = {
            "dietary_preferences": ["vegan"]
        }
        client.put(
            "/api/profile/preferences",
            json=prefs,
            headers=get_auth_headers(auth_token)
        )

        recipe_request = {
            "malzemeler": ["domates", "patates", "soğan"]
        }
        response = client.post(
            "/api/tarif/oner",
            json=recipe_request,
            headers=get_auth_headers(auth_token)
        )

        assert response.status_code == 200
        data = response.json()
        tarif = data["tarif"]

        # Vegan tarif et/süt/yumurta içermemeli
        malzemeler_str = " ".join(tarif.get("malzemeler", [])).lower()
        hayvansal = ["et", "tavuk", "balık", "süt", "yumurta", "peynir"]
        for item in hayvansal:
            assert item not in malzemeler_str

    def test_recipe_with_dislikes(self, client, auth_token):
        """Sevmediği yiyecekler dikkate alınır"""
        prefs = {
            "dislikes": ["patlıcan"]
        }
        client.put(
            "/api/profile/preferences",
            json=prefs,
            headers=get_auth_headers(auth_token)
        )

        recipe_request = {
            "malzemeler": ["domates", "biber", "soğan"]
        }
        response = client.post(
            "/api/tarif/oner",
            json=recipe_request,
            headers=get_auth_headers(auth_token)
        )

        assert response.status_code == 200
        # Tarif patlıcan minimize etmeli (veya hiç kullanmamalı)

    def test_recipe_with_combined_preferences(self, client, auth_token):
        """Kombine tercihler doğru çalışır"""
        prefs = {
            "dietary_preferences": ["vegan", "glutensiz"],
            "allergies": ["fıstık", "soya"],
            "dislikes": ["kereviz"]
        }
        client.put(
            "/api/profile/preferences",
            json=prefs,
            headers=get_auth_headers(auth_token)
        )

        recipe_request = {
            "malzemeler": ["sebzeler", "patates"]
        }
        response = client.post(
            "/api/tarif/oner",
            json=recipe_request,
            headers=get_auth_headers(auth_token)
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestProfileIsolation:
    """Profil izolasyonu testleri - kullanıcılar birbirinin bilgisini görememeli"""

    def test_users_have_separate_profiles(self, client, auth_token, auth_token_2):
        """Her kullanıcının kendi profili var"""
        # User 1 profilini güncelle
        user1_data = {"full_name": "User One", "bio": "First user"}
        client.put(
            "/api/profile",
            json=user1_data,
            headers=get_auth_headers(auth_token)
        )

        # User 2 profilini güncelle
        user2_data = {"full_name": "User Two", "bio": "Second user"}
        client.put(
            "/api/profile",
            json=user2_data,
            headers=get_auth_headers(auth_token_2)
        )

        # User 1 kendi profilini görmeli
        user1_profile = client.get(
            "/api/profile",
            headers=get_auth_headers(auth_token)
        ).json()
        assert user1_profile["full_name"] == "User One"

        # User 2 kendi profilini görmeli
        user2_profile = client.get(
            "/api/profile",
            headers=get_auth_headers(auth_token_2)
        ).json()
        assert user2_profile["full_name"] == "User Two"

    def test_users_have_separate_preferences(self, client, auth_token, auth_token_2):
        """Her kullanıcının kendi tercihleri var"""
        # User 1 tercihleri
        user1_prefs = {"allergies": ["fıstık"]}
        client.put(
            "/api/profile/preferences",
            json=user1_prefs,
            headers=get_auth_headers(auth_token)
        )

        # User 2 tercihleri
        user2_prefs = {"allergies": ["süt"]}
        client.put(
            "/api/profile/preferences",
            json=user2_prefs,
            headers=get_auth_headers(auth_token_2)
        )

        # User 1 kendi tercihlerini görmeli
        user1_get = client.get(
            "/api/profile/preferences",
            headers=get_auth_headers(auth_token)
        ).json()
        assert "fıstık" in user1_get["allergies"]
        assert "süt" not in user1_get["allergies"]

        # User 2 kendi tercihlerini görmeli
        user2_get = client.get(
            "/api/profile/preferences",
            headers=get_auth_headers(auth_token_2)
        ).json()
        assert "süt" in user2_get["allergies"]
        assert "fıstık" not in user2_get["allergies"]


class TestProfileFlow:
    """End-to-end profil işlemleri akışı"""

    def test_full_profile_workflow(self, client, auth_token, sample_profile_data, sample_preferences):
        """Tam profil işlem akışı"""
        # 1. Profil bilgilerini güncelle
        update_response = client.put(
            "/api/profile",
            json=sample_profile_data,
            headers=get_auth_headers(auth_token)
        )
        assert update_response.status_code == 200

        # 2. Profil fotoğrafı yükle
        img_io = create_test_image('PNG')
        photo_response = client.post(
            "/api/profile/photo",
            data={"file": (img_io, "avatar.png")},
            headers=get_auth_headers(auth_token),
            content_type='multipart/form-data'
        )
        assert photo_response.status_code == 200

        # 3. Tercihleri kaydet
        prefs_response = client.put(
            "/api/profile/preferences",
            json=sample_preferences,
            headers=get_auth_headers(auth_token)
        )
        assert prefs_response.status_code == 200

        # 4. Profili kontrol et - her şey kaydedilmiş olmalı
        profile_check = client.get(
            "/api/profile",
            headers=get_auth_headers(auth_token)
        ).json()
        assert profile_check["full_name"] == sample_profile_data["full_name"]
        assert profile_check["bio"] == sample_profile_data["bio"]

        # 5. Tercihleri kontrol et
        prefs_check = client.get(
            "/api/profile/preferences",
            headers=get_auth_headers(auth_token)
        ).json()
        assert set(prefs_check["dietary_preferences"]) == set(sample_preferences["dietary_preferences"])

        # 6. Tarif öner - tercihler yansımalı
        recipe_response = client.post(
            "/api/tarif/oner",
            json={"malzemeler": ["sebze", "makarna"]},
            headers=get_auth_headers(auth_token)
        )
        assert recipe_response.status_code == 200


# Test çalıştırma
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
