"""
Google Gemini AI entegrasyon servisi
"""
import google.generativeai as genai
from PIL import Image
from typing import List, Optional
from ..config import settings


class AIService:
    """AI servis sınıfı - Gemini API ile görüntü tanıma ve tarif üretimi"""

    def __init__(self):
        """AI servisini başlat"""
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            # Gemini 2.5 Flash - hem görüntü hem metin için en yeni model
            self.model = genai.GenerativeModel('gemini-2.5-flash')
            self.enabled = True
            print("✅ Gemini AI aktif: gemini-2.5-flash")
        else:
            self.enabled = False
            print("⚠️  Warning: GEMINI_API_KEY not found. AI features disabled.")

    def malzeme_tani(self, image_path: str) -> List[str]:
        """
        Fotoğraftan malzemeleri tanı

        Args:
            image_path: Görüntü dosyasının yolu

        Returns:
            Tanınan malzemelerin listesi
        """
        if not self.enabled:
            return []

        try:
            # Görüntüyü aç
            img = Image.open(image_path)

            # Prompt
            prompt = """
            Bu resimde hangi yiyecek malzemeleri var?
            
            Kurallar:
            - Sadece malzeme isimlerini listele
            - Her satıra bir malzeme
            - Türkçe isimler kullan
            - Sade isimler (örn: "domates" not "kırmızı domates")
            - Belirsizsen ekleme
            
            Format:
            domates
            biber
            soğan
            """

            # AI'ya sor
            response = self.model.generate_content([prompt, img])

            # Sonucu parse et
            malzemeler = [
                line.strip().lower()
                for line in response.text.strip().split('\n')
                if line.strip() and not line.startswith('-')
            ]

            return malzemeler

        except Exception as e:
            print(f"❌ Error in malzeme_tani: {e}")
            return []

    def tarif_oner(self, malzemeler: List[str], preferences: Optional[dict] = None) -> dict:
        """
        Malzemelerden tarif öner

        Args:
            malzemeler: Mevcut malzeme listesi
            preferences: Kullanıcı tercihleri (süre, zorluk, vb.)

        Returns:
            Tarif bilgileri (başlık, malzemeler, adımlar)
        """
        if not self.enabled:
            return self._get_fallback_recipe(malzemeler)

        try:
            # Tercihleri hazırla
            pref_text = ""
            if preferences:
                if preferences.get('sure'):
                    pref_text += f"\n- Maksimum süre: {preferences['sure']} dakika"
                if preferences.get('zorluk'):
                    pref_text += f"\n- Zorluk seviyesi: {preferences['zorluk']}"
                if preferences.get('kategori'):
                    pref_text += f"\n- Kategori: {preferences['kategori']}"

            # Prompt
            malzeme_listesi = ", ".join(malzemeler)
            prompt = f"""
            Elimde bu malzemeler var: {malzeme_listesi}
            
            Bana bir Türk mutfağı tarifi öner.{pref_text}
            
            Lütfen şu formatta yanıt ver:
            
            BAŞLIK: [Yemeğin adı]
            
            AÇIKLAMA: [Kısa açıklama, 1-2 cümle]
            
            MALZEMELER:
            - [malzeme 1] - [miktar]
            - [malzeme 2] - [miktar]
            ...
            
            ADIMLAR:
            1. [Adım 1]
            2. [Adım 2]
            ...
            
            SÜRE: [X] dakika
            ZORLUK: [kolay/orta/zor]
            KATEGORİ: [ana yemek/çorba/tatlı/vb]
            """

            # AI'ya sor
            response = self.model.generate_content(prompt)

            # Sonucu parse et
            tarif = self._parse_tarif_response(response.text)

            return tarif

        except Exception as e:
            print(f"❌ Error in tarif_oner: {e}")
            return self._get_fallback_recipe(malzemeler)

    def _parse_tarif_response(self, response_text: str) -> dict:
        """AI yanıtını parse et"""
        lines = response_text.strip().split('\n')

        tarif = {
            'baslik': '',
            'aciklama': '',
            'malzemeler': [],
            'adimlar': [],
            'sure': 30,
            'zorluk': 'orta',
            'kategori': 'ana yemek'
        }

        current_section = None

        for line in lines:
            line = line.strip()

            if line.startswith('BAŞLIK:'):
                tarif['baslik'] = line.replace('BAŞLIK:', '').strip()
            elif line.startswith('AÇIKLAMA:'):
                tarif['aciklama'] = line.replace('AÇIKLAMA:', '').strip()
            elif line.startswith('MALZEMELER:'):
                current_section = 'malzemeler'
            elif line.startswith('ADIMLAR:'):
                current_section = 'adimlar'
            elif line.startswith('SÜRE:'):
                try:
                    sure_text = line.replace('SÜRE:', '').strip()
                    tarif['sure'] = int(''.join(filter(str.isdigit, sure_text)))
                except:
                    pass
            elif line.startswith('ZORLUK:'):
                tarif['zorluk'] = line.replace('ZORLUK:', '').strip().lower()
            elif line.startswith('KATEGORİ:'):
                tarif['kategori'] = line.replace('KATEGORİ:', '').strip().lower()
            elif current_section == 'malzemeler' and line.startswith('-'):
                tarif['malzemeler'].append(line[1:].strip())
            elif current_section == 'adimlar' and (line[0:2].replace('.', '').isdigit()):
                tarif['adimlar'].append(line.split('.', 1)[1].strip())

        return tarif

    def _get_fallback_recipe(self, malzemeler: List[str]) -> dict:
        """AI çalışmazsa basit tarif döndür"""
        return {
            'baslik': 'Basit Yemek',
            'aciklama': f'{", ".join(malzemeler[:3])} ile hazırlanan basit bir yemek.',
            'malzemeler': [f'{m} - uygun miktar' for m in malzemeler],
            'adimlar': [
                'Malzemeleri hazırlayın',
                'Bir tavada uygun şekilde pişirin',
                'Servis yapın'
            ],
            'sure': 30,
            'zorluk': 'kolay',
            'kategori': 'ana yemek'
        }


# Global AI service instance
ai_service = AIService()