"""
Google Gemini AI entegrasyon servisi
"""
import google.generativeai as genai
from PIL import Image
from typing import List, Optional
from ..config import settings
import logging # Logging modülü dahil edildi
import traceback # Hata izini loglamak için eklendi

# Logger nesnesi oluşturma
logger = logging.getLogger(__name__)


class AIService:
    """AI servis sınıfı - Gemini API ile görüntü tanıma ve tarif üretimi"""

    def __init__(self):
        """AI servisini başlat"""
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            # Gemini 2.5 Flash - hem görüntü hem metin için en yeni model
            self.model = genai.GenerativeModel('gemini-2.5-flash')
            self.enabled = True
            logger.info("Gemini AI aktif: gemini-2.5-flash") # print yerine logger.info
        else:
            self.enabled = False
            logger.warning("GEMINI_API_KEY not found. AI features disabled.") # print yerine logger.warning

    def malzeme_tani(self, image_path: str) -> List[str]:
        """
        Fotoğraftan malzemeleri tanı
        """
        if not self.enabled:
            return []

        try:
            # Görüntüyü aç
            img = Image.open(image_path)

            # Prompt
            prompt = """
            Bu resimde hangi yiyecek malzemeleri var?

            ÇOK ÖNEMLİ KURALLAR:
            - SADECE yiyecek malzemesi varsa listele
            - Eğer resimde yiyecek malzemesi YOKSA, kesinlikle boş yanıt ver (hiçbir şey yazma)
            - Açıklama yapma, sadece malzeme isimlerini yaz
            - Her satıra bir malzeme
            - Türkçe isimler kullan
            - Sade isimler (örn: "domates" not "kırmızı domates")
            - Belirsizsen ekleme

            YANIT FORMATI (sadece malzeme isimleri, başka hiçbir şey):
            domates
            biber
            soğan

            Eğer resimde yiyecek malzemesi yoksa hiçbir şey yazma, boş bırak.
            """

            # AI'ya sor
            response = self.model.generate_content([prompt, img])

            # Response ve parts kontrolü (text'e erişmeden önce)
            if not response:
                logger.warning("AI response None") # print yerine logger.warning
                return []

            # Parts kontrolü - text property'sine erişmeden
            if not hasattr(response, 'parts') or not response.parts:
                logger.warning("AI response parts boş") # print yerine logger.warning
                return []

            # Şimdi güvenle text'e erişebiliriz
            try:
                text = response.text.strip().lower()
            except (IndexError, AttributeError) as e:
                logger.warning(f"Response text alınamadı: {e}") # print yerine logger.warning
                return []

            if not text:
                logger.warning("AI boş yanıt döndü") # print yerine logger.warning
                return []

            # Eğer "yok", "bulunmamaktadır", "görünmüyor" gibi kelimeler varsa boş döndür
            negative_keywords = [
                'yok',
                'bulunmamaktadır',
                'bulunmuyor',
                'görünmüyor',
                'tespit edilemedi',
                'tanınamadı',
                'herhangi bir',
                'hiçbir',
                'resimde',
                'fotoğrafta'
            ]

            if any(keyword in text for keyword in negative_keywords):
                logger.warning(f"AI malzeme bulamadı: {text[:100]}") # print yerine logger.warning
                return []

            # Satırlara böl ve temizle... (Değişmedi)
            malzemeler = []
            for line in text.split('\n'):
                cleaned = line.strip().lower()

                # Boş satır atla
                if not cleaned:
                    continue

                # Çok kısa veya uzun satırları atla
                if len(cleaned) < 3 or len(cleaned) > 50:
                    continue

                # Tire, yıldız gibi işaretlerle başlayanları temizle
                if cleaned.startswith('-'):
                    cleaned = cleaned[1:].strip()
                if cleaned.startswith('*'):
                    cleaned = cleaned[1:].strip()

                # Hala geçerliyse ekle
                if cleaned and len(cleaned) >= 3:
                    malzemeler.append(cleaned)

            # Boş ise boş liste döndür
            if not malzemeler:
                logger.warning("Malzeme listesi boş") # print yerine logger.warning
                return []

            logger.info(f"{len(malzemeler)} malzeme bulundu: {malzemeler}") # print yerine logger.info
            return malzemeler

        except Exception as e:
            logger.error(f"Error in malzeme_tani: {e}\n{traceback.format_exc()}") # print yerine logger.error ve traceback eklendi
            return []

    def tarif_oner(self, malzemeler: List[str], preferences: Optional[dict] = None) -> dict:
        """
        Malzemelerden tarif öner

        Args:
            malzemeler: Mevcut malzeme listesi
            preferences: Kullanıcı tercihleri (süre, zorluk, dietary_preferences, allergies, dislikes)

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

                # Diyet tercihleri
                if preferences.get('dietary_preferences'):
                    diets = ', '.join(preferences['dietary_preferences'])
                    pref_text += f"\n- Diyet tercihleri: {diets}"

                # Alerjiler - ÇOK ÖNEMLİ
                if preferences.get('allergies'):
                    allergies = ', '.join(preferences['allergies'])
                    pref_text += f"\n- ⚠️ ALERJİLER (KESİNLİKLE KULLANMA): {allergies}"

                # Sevmediği yiyecekler
                if preferences.get('dislikes'):
                    dislikes = ', '.join(preferences['dislikes'])
                    pref_text += f"\n- Sevmediği yiyecekler (mümkünse kullanma): {dislikes}"

            # Prompt
            malzeme_listesi = ", ".join(malzemeler)
            prompt = f"""
            Elimde bu malzemeler var: {malzeme_listesi}
            
            Bana bir Türk mutfağı tarifi öner.{pref_text}
            
            ÖNEMLİ KURALLAR:
            1. Eğer alerji listesi varsa, o malzemeleri KESİNLİKLE kullanma
            2. Sevmediği yiyecekleri mümkün olduğunca kullanma
            3. Diyet tercihlerine uygun tarif hazırla
            
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
            logger.error(f"Error in tarif_oner: {e}\n{traceback.format_exc()}")
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

    # ============================================
    # BESİN DEĞERLERİ HESAPLAMA
    # ============================================

    async def calculate_nutrition(
            self,
            recipe_title: str,
            ingredients: List[str],
            portions: int = 4
    ) -> dict:
        """Besin değerlerini hesapla"""
        if not self.enabled:
            return self._get_fallback_nutrition(ingredients, portions)

        try:
            malzeme_listesi = '\n'.join(f"- {ing}" for ing in ingredients)

            prompt = f"""
Tarif: {recipe_title}
Porsiyon: {portions}
Malzemeler:
{malzeme_listesi}

SADECE JSON ver:
{{
    "per_serving": {{"calories": <float>, "protein": <float>, "carbs": <float>, "fat": <float>, "fiber": <float>, "sugar": <float>, "sodium": <float>, "cholesterol": <float>, "saturated_fat": <float>, "trans_fat": <float>}},
    "total": {{"calories": <float>, "protein": <float>, "carbs": <float>, "fat": <float>, "fiber": <float>, "sugar": <float>, "sodium": <float>, "cholesterol": <float>, "saturated_fat": <float>, "trans_fat": <float>}}
}}
"""

            response = self.model.generate_content(prompt)
            if not response:
                return self._get_fallback_nutrition(ingredients, portions)

            response_text = response.text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()

            import json
            nutrition_data = json.loads(response_text)

            def clean(data):
                return {k: round(float(v or 0), 1) for k, v in data.items()}

            nutrition_data["per_serving"] = clean(nutrition_data["per_serving"])
            nutrition_data["total"] = clean(nutrition_data["total"])

            return nutrition_data

        except Exception as e:
            logger.error(f"Nutrition error: {e}")
            return self._get_fallback_nutrition(ingredients, portions)

    def _get_fallback_nutrition(self, ingredients: List[str], portions: int) -> dict:
        """Fallback besin değerleri"""
        avg = {
            "calories": 450.0, "protein": 25.0, "carbs": 45.0, "fat": 18.0,
            "fiber": 5.0, "sugar": 8.0, "sodium": 800.0, "cholesterol": 50.0,
            "saturated_fat": 5.0, "trans_fat": 0.0
        }

        multiplier = 1 + (len(ingredients) - 5) * 0.1
        per_serving = {k: round(v * multiplier, 1) for k, v in avg.items()}
        total = {k: round(v * portions, 1) for k, v in per_serving.items()}

        return {"per_serving": per_serving, "total": total}


# Global AI service instance
ai_service = AIService()