from pathlib import Path
from vortenix_newsletter.domain.enums import NewsletterStatus
from vortenix_newsletter.domain.models import EmailMessage
class NewsletterService:
    def __init__(self,repo,provider): self.repo=repo; self.provider=provider
    def approve(self,ident): n=self.repo.get(ident); n.transition_to(NewsletterStatus.APPROVED); self.repo.save(n); return n
    def reject(self,ident): n=self.repo.get(ident); n.transition_to(NewsletterStatus.REJECTED); self.repo.save(n); return n
    async def send(self,ident,recipients,force=False):
        n=self.repo.get(ident)
        if n.status==NewsletterStatus.SENT and force: n.status=NewsletterStatus.APPROVED
        if n.status!=NewsletterStatus.APPROVED: raise ValueError("Newsletter must be APPROVED before sending")
        subject=f"{n.title} - {n.edition_date.isoformat()}"
        message=EmailMessage(subject=subject,recipients=recipients,text_body=Path(n.text_path or "").read_text(),html_body=Path(n.html_path or "").read_text(),text_path=n.text_path,html_path=n.html_path)
        result=await self.provider.send(message); n.transition_to(NewsletterStatus.SENT if result.success else NewsletterStatus.FAILED); self.repo.save(n); return result
