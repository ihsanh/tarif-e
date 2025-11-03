"""
Tarif Integration Tests
"""
import pytest
import json


class TestTarifAPI:
    """Tarif API testleri"""
    
    def test_favori_ekle(self, client, sample_tarif):
        """Tarif favorilere eklenir"""
        response = client.post(
            "/api/favoriler/ekle",
            json={"tarif": sample_tarif}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "favori_id" in data
    
    
    def test_favori_liste(self, client, sample_tarif):
        """Favoriler listelenir"""
        # Önce ekle
        client.post("/api/favoriler/ekle", json={"tarif": sample_tarif})
        
        # Listele
        response = client.get("/api/favoriler/liste")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["favoriler"]) == 1
        assert data["favoriler"][0]["baslik"] == "Menemen"
    
    
    def test_favori_sil(self, client, sample_tarif):
        """Favori silinir"""
        # Önce ekle
        add_response = client.post("/api/favoriler/ekle", json={"tarif": sample_tarif})
        favori_id = add_response.json()["favori_id"]
        
        # Sil
        response = client.delete(f"/api/favoriler/{favori_id}")
        
        assert response.status_code == 200
        assert response.json()["success"] is True
        
        # Liste boş olmalı
        list_response = client.get("/api/favoriler/liste")
        assert len(list_response.json()["favoriler"]) == 0
    
    
    def test_favori_sil_not_found(self, client):
        """Olmayan favori silinmeye çalışılınca 404"""
        response = client.delete("/api/favoriler/999")
        assert response.status_code == 404


class TestTarifFlow:
    """Tarif akış testleri (end-to-end)"""
    
    def test_full_tarif_workflow(self, client, sample_tarif):
        """Tam tarif iş akışı"""
        # 1. Favoriye ekle
        add_response = client.post(
            "/api/favoriler/ekle",
            json={"tarif": sample_tarif}
        )
        assert add_response.status_code == 200
        favori_id = add_response.json()["favori_id"]
        
        # 2. Listede görün
        list_response = client.get("/api/favoriler/liste")
        favoriler = list_response.json()["favoriler"]
        assert len(favoriler) == 1
        assert favoriler[0]["id"] == favori_id
        assert favoriler[0]["baslik"] == sample_tarif["baslik"]
        
        # 3. Malzemelerin JSON olarak doğru parse edildiğini kontrol et
        assert isinstance(favoriler[0]["malzemeler"], list)
        assert len(favoriler[0]["malzemeler"]) == 4
        
        # 4. Sil
        delete_response = client.delete(f"/api/favoriler/{favori_id}")
        assert delete_response.status_code == 200
        
        # 5. Liste boş
        final_list = client.get("/api/favoriler/liste")
        assert len(final_list.json()["favoriler"]) == 0
