import asyncio,os,smtplib
from email.message import EmailMessage as SMTPMessage
from vortenix_newsletter.domain.exceptions import ConfigurationError
from vortenix_newsletter.domain.models import DeliveryResult,EmailMessage
class SMTPEmailProvider:
    """SMTP adapter configured exclusively through environment variables."""

    def __init__(self):
        self.host=os.getenv("SMTP_HOST",""); self.port=int(os.getenv("SMTP_PORT","587")); self.username=os.getenv("SMTP_USERNAME",""); self.password=os.getenv("SMTP_PASSWORD",""); self.sender=os.getenv("SMTP_FROM_EMAIL",""); self.tls=os.getenv("SMTP_USE_TLS","true").lower()=="true"
        if not self.host or not self.sender:
            raise ConfigurationError("SMTP_HOST and SMTP_FROM_EMAIL are required")
        if self.username and not self.password:
            raise ConfigurationError("SMTP_PASSWORD is required when SMTP_USERNAME is set")
    async def send(self,message: EmailMessage)->DeliveryResult:
        mail=SMTPMessage(); mail["Subject"]=message.subject; mail["From"]=self.sender; mail["To"]=', '.join(message.recipients); mail.set_content(message.text_body); mail.add_alternative(message.html_body,subtype="html")
        def deliver():
            with smtplib.SMTP(self.host,self.port,timeout=20) as client:
                if self.tls: client.starttls()
                if self.username: client.login(self.username,self.password)
                client.send_message(mail)
        try: await asyncio.to_thread(deliver); return DeliveryResult(success=True)
        except (OSError,smtplib.SMTPException) as exc: return DeliveryResult(success=False,error=str(exc))
