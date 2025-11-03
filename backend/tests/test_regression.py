"""
Regression Tests - Kritik özelliklerin çalıştığını garanti et
"""
import pytest


class TestCriticalFeatures:
    """Kritik özellikler - Bunlar asla bozulmamalı"""
    
    def test_health_check(self, client):
        """Health check her zaman çalışmalı"""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    
    def test_malzeme_ekleme_ve_listeleme(self, client):
        """Malzeme ekleme ve listeleme temel özellik"""
        # Ekle
        add_response = client.post(
            "/api/malzeme/ekle",
            json={"name": "test_malzeme", "miktar": 1, "birim": "adet"}
        )
        assert add_response.status_code == 200
        
        # Listede olmalı
        list_response = client.get("/api/malzeme/liste")
        assert list_response.status_code == 200
        malzemeler = list_response.json()["malzemeler"]
        assert any(m["name"] == "test_malzeme" for m in malzemeler)
    
    
    def test_alisveris_listesi_olusturma(self, client, sample_malzemeler):
        """Alışveriş listesi oluşturma kritik"""
        response = client.post(
            "/api/alisveris/olustur",
            json={
                "malzemeler": [
                    "domates - 5 adet",
                    "yumurta - 6 adet"  # Bu eksik
                ]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "liste_id" in data
        assert len(data["eksik_malzemeler"]) > 0  # Yumurta eksik olmalı
    
    
    def test_favori_ekleme_ve_silme(self, client):
        """Favori ekleme ve silme kritik"""
        tarif = {
            "baslik": "Test Tarif",
            "malzemeler": ["test - 1 adet"],
            "adimlar": ["Test adım"]
        }
        
        # Ekle
        add_response = client.post(
            "/api/favoriler/ekle",
            json={"tarif": tarif}
        )
        assert add_response.status_code == 200
        favori_id = add_response.json()["favori_id"]
        
        # Sil
        delete_response = client.delete(f"/api/favoriler/{favori_id}")
        assert delete_response.status_code == 200


class TestBackwardCompatibility:
    """Geriye dönük uyumluluk - Eski özellikler çalışmalı"""
    
    def test_old_api_endpoints_still_work(self, client):
        """Eski API endpoint'leri hala çalışmalı"""
        # Health check (v1'den beri var)
        response = client.get("/api/health")
        assert response.status_code == 200
        
        # Malzeme listesi (v1'den beri var)
        response = client.get("/api/malzeme/liste")
        assert response.status_code == 200
        assert "malzemeler" in response.json()
    
    
    def test_response_format_unchanged(self, client):
        """Response formatı değişmemeli (breaking change olmasın)"""
        response = client.get("/api/malzeme/liste")
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
    
    def test_cok_uzun_malzeme_adi(self, client):
        """Çok uzun malzeme adı"""
        long_name = "a" * 1000
        response = client.post(
            "/api/malzeme/ekle",
            json={"name": long_name, "miktar": 1, "birim": "adet"}
        )
        # Başarılı olmalı (database sınırı yoksa)
        assert response.status_code in [200, 400, 422]
    
    
    def test_ozel_karakterler_malzeme_adi(self, client):
        """Özel karakterlerle malzeme adı"""
        response = client.post(
            "/api/malzeme/ekle",
            json={"name": "domates🍅", "miktar": 1, "birim": "adet"}
        )
        assert response.status_code == 200
    
    
    def test_bos_alisveris_listesi(self, client):
        """Boş malzeme listesiyle alışveriş listesi oluşturma"""
        response = client.post(
            "/api/alisveris/olustur",
            json={"malzemeler": []}
        )
        # 400 Bad Request beklenir
        assert response.status_code == 400


class TestPerformance:
    """Performans testleri - Basit metrikler"""
    
    def test_coklu_malzeme_ekleme_performansi(self, client):
        """100 malzeme eklemek hızlı olmalı"""
        import time
        
        start = time.time()
        
        for i in range(100):
            client.post(
                "/api/malzeme/ekle",
                json={"name": f"malzeme_{i}", "miktar": 1, "birim": "adet"}
            )
        
        elapsed = time.time() - start
        
        # 100 ekleme 10 saniyeden az sürmeliassert elapsed < 10, f"100 malzeme eklemek {elapsed:.2f}s sürdü"
    
    
    def test_liste_performansi(self, client, sample_malzemeler):
        """Listeleme hızlı olmalı"""
        import time
        
        start = time.time()
        response = client.get("/api/malzeme/liste")
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 1, f"Listeleme {elapsed:.2f}s sürdü"
