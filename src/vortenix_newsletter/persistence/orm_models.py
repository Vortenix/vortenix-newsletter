from datetime import datetime
from sqlalchemy import DateTime,String,Text
from sqlalchemy.orm import Mapped,mapped_column
from .database import Base
class JsonRecord(Base):
    __abstract__=True
    id: Mapped[str]=mapped_column(String,primary_key=True)
    payload: Mapped[str]=mapped_column(Text)
    created_at: Mapped[datetime]=mapped_column(DateTime)
class SourceRecord(JsonRecord): __tablename__="source_documents"
class ResultRecord(JsonRecord): __tablename__="research_results"
class NewsletterRecord(JsonRecord):
    __tablename__="newsletters"
    status: Mapped[str]=mapped_column(String,index=True)
class AudienceRecord(JsonRecord): __tablename__="audiences"
class DeliveryRecord(JsonRecord): __tablename__="delivery_attempts"
