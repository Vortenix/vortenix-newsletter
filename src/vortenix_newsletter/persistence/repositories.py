from datetime import UTC,datetime
from sqlalchemy import select
from sqlalchemy.orm import Session
from vortenix_newsletter.domain.models import Newsletter,SourceDocument,VerticalResearchResult
from .orm_models import NewsletterRecord,ResultRecord,SourceRecord
class SourceRepository:
    def __init__(self,s: Session): self.s=s
    def add_all(self,items: list[SourceDocument]):
        for x in items:
            if not self.s.get(SourceRecord,x.id): self.s.add(SourceRecord(id=x.id,payload=x.model_dump_json(),created_at=datetime.now(UTC)))
        self.s.commit()
    def list(self): return [SourceDocument.model_validate_json(x.payload) for x in self.s.scalars(select(SourceRecord))]
class ResultRepository:
    def __init__(self,s: Session): self.s=s
    def add(self,x: VerticalResearchResult): self.s.merge(ResultRecord(id=x.id,payload=x.model_dump_json(),created_at=datetime.now(UTC))); self.s.commit()
    def list(self): return [VerticalResearchResult.model_validate_json(x.payload) for x in self.s.scalars(select(ResultRecord))]
class NewsletterRepository:
    def __init__(self,s: Session): self.s=s
    def save(self,x: Newsletter): self.s.merge(NewsletterRecord(id=x.id,payload=x.model_dump_json(),status=x.status.value,created_at=x.created_at)); self.s.commit()
    def get(self,ident: str):
        row=self.s.get(NewsletterRecord,ident)
        if row is None: raise KeyError(f"Newsletter not found: {ident}")
        return Newsletter.model_validate_json(row.payload)
    def list(self): return [Newsletter.model_validate_json(x.payload) for x in self.s.scalars(select(NewsletterRecord).order_by(NewsletterRecord.created_at.desc()))]
