from typing import Protocol
from vortenix_newsletter.domain.models import DeliveryResult,EmailMessage
class EmailProvider(Protocol):
    """Deliver an already approved newsletter message."""

    async def send(self,message: EmailMessage)->DeliveryResult: ...
