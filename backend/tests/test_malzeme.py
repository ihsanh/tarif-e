class TestMalzemeValidation:
    """Malzeme validasyon testleri"""
    
    def test_malzeme_ekle_bos_name(self, client):
        """Boş isimle malzeme eklenemez"""
        response = client.post(
            "/api/malzeme/ekle",
            json={"name": "", "miktar": 5, "birim": "adet"}
        )
        # Pydantic validation hatası beklenir
        assert response.status_code == 422  # Unprocessable Entity
        
        # Hata mesajını kontrol et
        data = response.json()
        assert "detail" in data
    
    
    def test_malzeme_ekle_sadece_bosluk(self, client):
        """Sadece boşluklu isimle malzeme eklenemez"""
        response = client.post(
            "/api/malzeme/ekle",
            json={"name": "   ", "miktar": 5, "birim": "adet"}
        )
        assert response.status_code == 422
    
    
    def test_malzeme_ekle_negatif_miktar(self, client):
        """Negatif miktarla malzeme eklenemez"""
        response = client.post(
            "/api/malzeme/ekle",
            json={"name": "domates", "miktar": -5, "birim": "adet"}
        )
        assert response.status_code == 422
        
        # Hata mesajını kontrol et
        data = response.json()
        assert "detail" in data
    
    
    def test_malzeme_ekle_sifir_miktar(self, client):
        """Sıfır miktarla malzeme eklenemez"""
        response = client.post(
            "/api/malzeme/ekle",
            json={"name": "domates", "miktar": 0, "birim": "adet"}
        )
        assert response.status_code == 422
    
    
    def test_malzeme_ekle_gecerli(self, client):
        """Geçerli veri ile malzeme eklenir"""
        response = client.post(
            "/api/malzeme/ekle",
            json={"name": "domates", "miktar": 5, "birim": "adet"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["malzeme"]["name"] == "domates"
        assert data["malzeme"]["miktar"] == 5