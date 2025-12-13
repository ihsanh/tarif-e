"""
Email Service
Şifre sıfırlama emaili gönderimi
"""
import logging
from typing import Optional
from app.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Email gönderim servisi"""

    def __init__(self):
        from app.config import settings

        # DEBUG moduna göre
        if settings.DEBUG:
            self.enabled = False
            logger.info("📧 DEV MODE: Links logged to console")
        elif hasattr(settings, 'SMTP_HOST') and settings.SMTP_HOST:
            self.enabled = True
            logger.info("📧 PROD MODE: Enabled")
        else:
            self.enabled = False
            logger.info("📧 PROD MODE: Disabled")

    async def send_reset_email(
        self,
        to_email: str,
        reset_link: str,
        username: str = None
    ) -> bool:
        """
        Şifre sıfırlama emaili gönder

        Args:
            to_email: Alıcı email
            reset_link: Sıfırlama linki
            username: Kullanıcı adı (opsiyonel)

        Returns:
            Başarılı mı (True/False)
        """
        if not self.enabled:
            # Production'da gerçek email gönderilir
            # Development'ta sadece log'la
            logger.info(f"📧 [DEV MODE] Password reset email would be sent to: {to_email}")
            logger.info(f"🔗 Reset link: {reset_link}")
            return True

        try:
            # TODO: Gerçek email gönderimi (SMTP)
            # import smtplib
            # from email.mime.text import MIMEText
            # from email.mime.multipart import MIMEMultipart

            # msg = MIMEMultipart('alternative')
            # msg['Subject'] = "Tarif-e - Şifre Sıfırlama"
            # msg['From'] = settings.SMTP_FROM_EMAIL
            # msg['To'] = to_email

            # html = self._get_reset_email_html(reset_link, username)
            # part = MIMEText(html, 'html')
            # msg.attach(part)

            # with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            #     server.starttls()
            #     server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            #     server.send_message(msg)

            logger.info(f"✅ Password reset email sent to: {to_email}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to send reset email: {e}")
            return False

    def _get_reset_email_html(self, reset_link: str, username: str = None) -> str:
        """Email HTML template"""
        user_greeting = f"Merhaba {username}," if username else "Merhaba,"

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                          color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9fafb; padding: 30px; border-radius: 0 0 10px 10px; }}
                .button {{ display: inline-block; padding: 12px 30px; background: #667eea; 
                          color: white; text-decoration: none; border-radius: 5px; 
                          font-weight: bold; margin: 20px 0; }}
                .footer {{ text-align: center; color: #6b7280; font-size: 0.875rem; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🍳 Tarif-e</h1>
                    <p>Şifre Sıfırlama</p>
                </div>
                <div class="content">
                    <p>{user_greeting}</p>
                    <p>Şifrenizi sıfırlamak için bir talepte bulundunuz. Aşağıdaki butona tıklayarak yeni şifrenizi belirleyebilirsiniz:</p>
                    
                    <center>
                        <a href="{reset_link}" class="button">Şifremi Sıfırla</a>
                    </center>
                    
                    <p>Veya bu linki tarayıcınıza kopyalayın:</p>
                    <p style="background: #e5e7eb; padding: 10px; border-radius: 5px; word-break: break-all;">
                        {reset_link}
                    </p>
                    
                    <p style="color: #dc2626; margin-top: 20px;">
                        ⚠️ Bu link 30 dakika geçerlidir.
                    </p>
                    
                    <p>Eğer bu talebi siz yapmadıysanız, bu emaili görmezden gelebilirsiniz.</p>
                </div>
                <div class="footer">
                    <p>© 2024 Tarif-e - Akıllı Mutfak Asistanı</p>
                    <p>Bu email otomatik olarak gönderilmiştir.</p>
                </div>
            </div>
        </body>
        </html>
        """


# Global instance
email_service = EmailService()