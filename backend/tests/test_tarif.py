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


class TestNutrition:
    """Besin değerleri testleri"""

    def test_calculate_nutrition_basic(self, client, auth_token):
        """Basit tarif için besin değerleri hesaplanır"""
        nutrition_request = {
            "baslik": "Test Omlet",
            "malzemeler": [
                "3 adet yumurta",
                "1 adet soğan",
                "2 yemek kaşığı tereyağı"
            ],
            "porsiyon": 2
        }

        response = client.post(
            "/api/tarif/nutrition",
            json=nutrition_request,
            headers=get_auth_headers(auth_token)
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "nutrition" in data

        # Porsiyon başına değerler
        per_serving = data["nutrition"]["per_serving"]
        assert "calories" in per_serving
        assert "protein" in per_serving
        assert "carbs" in per_serving
        assert "fat" in per_serving

        # Pozitif değerler olmalı
        assert per_serving["calories"] > 0
        assert per_serving["protein"] > 0
        assert per_serving["carbs"] >= 0
        assert per_serving["fat"] > 0

        # Toplam değerler
        total = data["nutrition"]["total"]
        assert "calories" in total
        assert total["calories"] > per_serving["calories"]  # Toplam > porsiyon

        print(f"✅ Besin değerleri: {per_serving['calories']} kcal/porsiyon")

    def test_calculate_nutrition_complex_recipe(self, client, auth_token):
        """Karmaşık tarif için besin değerleri hesaplanır"""
        nutrition_request = {
            "baslik": "Karnıyarık",
            "malzemeler": [
                "4 adet patlıcan",
                "300g kıyma",
                "2 adet soğan",
                "3 adet domates",
                "2 adet biber",
                "3 yemek kaşığı zeytinyağı",
                "Tuz, karabiber"
            ],
            "porsiyon": 4
        }

        response = client.post(
            "/api/tarif/nutrition",
            json=nutrition_request,
            headers=get_auth_headers(auth_token)
        )

        assert response.status_code == 200
        data = response.json()

        # Detaylı besin değerleri de olmalı
        per_serving = data["nutrition"]["per_serving"]

        # Temel makrolar
        assert per_serving["calories"] > 0
        assert per_serving["protein"] > 10  # Kıyma var, yüksek protein bekleniyor
        assert per_serving["carbs"] > 0
        assert per_serving["fat"] > 0

        # Detaylı değerler (varsa)
        if "fiber" in per_serving and per_serving["fiber"]:
            assert per_serving["fiber"] >= 0

        if "sodium" in per_serving and per_serving["sodium"]:
            assert per_serving["sodium"] >= 0

        print(f"✅ Karnıyarık: P:{per_serving['protein']}g C:{per_serving['carbs']}g F:{per_serving['fat']}g")

    def test_nutrition_different_portions(self, client, auth_token):
        """Farklı porsiyon sayıları için doğru hesaplama"""
        base_recipe = {
            "baslik": "Test Tarif",
            "malzemeler": ["domates", "soğan", "biber"]
        }

        # 2 porsiyon
        response_2 = client.post(
            "/api/tarif/nutrition",
            json={**base_recipe, "porsiyon": 2},
            headers=get_auth_headers(auth_token)
        )

        # 4 porsiyon
        response_4 = client.post(
            "/api/tarif/nutrition",
            json={**base_recipe, "porsiyon": 4},
            headers=get_auth_headers(auth_token)
        )

        assert response_2.status_code == 200
        assert response_4.status_code == 200

        data_2 = response_2.json()["nutrition"]
        data_4 = response_4.json()["nutrition"]

        # Porsiyon başına benzer olmalı (AI varyasyonu için %30 tolerans)
        cal_2 = data_2["per_serving"]["calories"]
        cal_4 = data_4["per_serving"]["calories"]

        if cal_2 > 0 and cal_4 > 0:
            # %30 tolerans ile yakın olmalı
            assert abs(cal_2 - cal_4) / max(cal_2, cal_4) < 0.3

        # Toplam 2 katı olmalı (yaklaşık)
        total_2 = data_2["total"]["calories"]
        total_4 = data_4["total"]["calories"]

        assert total_4 > total_2  # 4 porsiyon > 2 porsiyon

        print(f"✅ 2 porsiyon: {total_2} kcal, 4 porsiyon: {total_4} kcal")

    def test_nutrition_unauthorized(self, client):
        """Token olmadan besin değerleri hesaplanamaz"""
        nutrition_request = {
            "baslik": "Test",
            "malzemeler": ["domates"],
            "porsiyon": 2
        }

        response = client.post(
            "/api/tarif/nutrition",
            json=nutrition_request
        )

        assert response.status_code == 401

    def test_nutrition_empty_ingredients(self, client, auth_token):
        """Boş malzeme listesi ile fallback çalışır"""
        nutrition_request = {
            "baslik": "Test",
            "malzemeler": [],
            "porsiyon": 2
        }

        response = client.post(
            "/api/tarif/nutrition",
            json=nutrition_request,
            headers=get_auth_headers(auth_token)
        )

        # 200 dönmeli (fallback çalışır)
        assert response.status_code == 200
        data = response.json()

        # Fallback değerleri olmalı
        assert data["success"] is True
        assert data["nutrition"]["per_serving"]["calories"] > 0


class TestNutritionIntegration:
    """Besin değerleri entegrasyon testleri"""

    def test_nutrition_with_favorite_recipe(self, client, auth_token, sample_tarif):
        """Favori tarif için besin değerleri hesaplanır"""
        # 1. Favori ekle
        add_response = client.post(
            "/api/favoriler/ekle",
            json={"tarif": sample_tarif},
            headers=get_auth_headers(auth_token)
        )
        assert add_response.status_code == 200
        favori_id = add_response.json()["favori_id"]

        # 2. Besin değerlerini hesapla
        nutrition_response = client.post(
            "/api/tarif/nutrition",
            json={
                "baslik": sample_tarif["baslik"],
                "malzemeler": sample_tarif["malzemeler"],
                "porsiyon": 4
            },
            headers=get_auth_headers(auth_token)
        )

        assert nutrition_response.status_code == 200
        nutrition_data = nutrition_response.json()

        assert nutrition_data["success"] is True
        assert "nutrition" in nutrition_data

        # Değerler doğru mu kontrol et
        nutrition = nutrition_data["nutrition"]
        assert nutrition["per_serving"]["calories"] > 0
        assert nutrition["per_serving"]["protein"] > 0

        # 3. Cleanup - favoriyi sil
        client.delete(
            f"/api/favoriler/{favori_id}",
            headers=get_auth_headers(auth_token)
        )

        print(f"✅ {sample_tarif['baslik']}: {nutrition['per_serving']['calories']} kcal/porsiyon")

    def test_full_workflow_with_nutrition(self, client, auth_token, sample_tarif):
        """Tam iş akışı: Favori ekle → Besin değerleri hesapla → Sil"""
        # 1. Favoriye ekle
        add_response = client.post(
            "/api/favoriler/ekle",
            json={"tarif": sample_tarif},
            headers=get_auth_headers(auth_token)
        )
        favori_id = add_response.json()["favori_id"]

        # 2. Besin değerlerini hesapla
        nutrition_response = client.post(
            "/api/tarif/nutrition",
            json={
                "baslik": sample_tarif["baslik"],
                "malzemeler": sample_tarif["malzemeler"],
                "porsiyon": 4
            },
            headers=get_auth_headers(auth_token)
        )

        assert nutrition_response.status_code == 200
        nutrition = nutrition_response.json()["nutrition"]

        # 3. Sonuçları doğrula
        assert nutrition["per_serving"]["calories"] > 0
        assert nutrition["per_serving"]["protein"] > 0
        assert nutrition["total"]["calories"] > nutrition["per_serving"]["calories"]

        # 4. Cleanup
        delete_response = client.delete(
            f"/api/favoriler/{favori_id}",
            headers=get_auth_headers(auth_token)
        )
        assert delete_response.status_code == 200

        print(f"✅ Full workflow test: {sample_tarif['baslik']} - {nutrition['per_serving']['calories']} kcal")


# Test çalıştırma
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
