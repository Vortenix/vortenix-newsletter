from vortenix_newsletter.domain.models import DeliveryResult,EmailMessage
class ConsoleEmailProvider:
    """Development provider that prints metadata without external delivery."""

    async def send(self,message: EmailMessage)->DeliveryResult:
        print(f"Subject: {message.subject}\nRecipients: {', '.join(message.recipients)}\nHTML: {message.html_path}\nText: {message.text_path}")
        return DeliveryResult(success=True,provider_message_id="console-mock")
