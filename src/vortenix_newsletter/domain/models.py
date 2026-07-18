from __future__ import annotations
from datetime import UTC, date, datetime
from typing import Any, Literal
from uuid import uuid4
from pydantic import BaseModel, Field, HttpUrl
from .enums import NewsletterStatus, SourceType
from .exceptions import InvalidStatusTransition


def utcnow() -> datetime:
    return datetime.now(UTC)


def uid() -> str:
    return str(uuid4())


class SourceDocument(BaseModel):
    id: str = Field(default_factory=uid)
    source_type: SourceType = SourceType.RSS
    source_name: str
    title: str
    content: str
    url: HttpUrl
    author: str | None = None
    published_at: datetime | None = None
    retrieved_at: datetime = Field(default_factory=utcnow)
    content_hash: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class Citation(BaseModel):
    source_document_id: str
    source_title: str
    url: HttpUrl
    supporting_excerpt: str = Field(max_length=500)


class ResearchFinding(BaseModel):
    id: str = Field(default_factory=uid)
    vertical_id: str
    title: str
    summary: str
    development: str = ""
    significance: str = ""
    pain_points: list[str] = Field(default_factory=list)
    company_solutions: list[dict[str, str]] = Field(default_factory=list)
    affected_companies: list[str] = Field(default_factory=list)
    opportunities: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    relevance_score: float = Field(ge=0, le=1)
    novelty_score: float = Field(ge=0, le=1)
    significance_score: float = Field(ge=0, le=1)
    confidence_score: float = Field(ge=0, le=1)
    evidence_score: float = Field(ge=0, le=1)
    recency_score: float = Field(ge=0, le=1)
    citations: list[Citation]
    created_at: datetime = Field(default_factory=utcnow)
    rank_score: float = Field(default=0, ge=0, le=1)


class VerticalResearchResult(BaseModel):
    id: str = Field(default_factory=uid)
    vertical_id: str
    research_date: date = Field(default_factory=lambda: utcnow().date())
    executive_summary: str
    findings: list[ResearchFinding]
    emerging_trends: list[str] = Field(default_factory=list)
    important_companies: list[str] = Field(default_factory=list)
    what_to_watch: list[str] = Field(default_factory=list)
    analysis_mode: Literal["deterministic", "llm"] = "deterministic"
    analysis_warnings: list[str] = Field(default_factory=list)


class Audience(BaseModel):
    id: str
    name: str
    recipients: list[str]
    enabled_verticals: list[str]
    topic_priorities: dict[str, str] = Field(default_factory=dict)
    frequency: str = "daily"
    depth: str = "detailed"
    enabled: bool = True


class Subscriber(BaseModel):
    """Private subscriber preferences loaded from local configuration."""

    id: str
    name: str
    email: str
    audience_id: str
    enabled_verticals: list[str]
    topic_priorities: dict[str, str] = Field(default_factory=dict)
    frequency: str = "daily"
    depth: str = "detailed"
    research_mode: Literal["deterministic", "llm"] = "deterministic"
    enabled: bool = True

    def personalized_audience(self, audience: Audience) -> Audience:
        """Build an audience view restricted to this subscriber's selected verticals."""
        if self.audience_id != audience.id:
            raise ValueError(f"Subscriber {self.id} does not belong to audience {audience.id}")
        allowed = set(audience.enabled_verticals)
        verticals = [vertical for vertical in self.enabled_verticals if vertical in allowed]
        if not verticals:
            raise ValueError(
                f"Subscriber {self.id} has no enabled verticals in audience {audience.id}"
            )
        return Audience(
            id=audience.id,
            name=audience.name,
            recipients=[self.email],
            enabled_verticals=verticals,
            topic_priorities=self.topic_priorities,
            frequency=self.frequency,
            depth=self.depth,
            enabled=self.enabled,
        )


class NewsletterSection(BaseModel):
    vertical_id: str
    heading: str
    introduction: str
    items: list[ResearchFinding]
    what_to_watch: list[str] = Field(default_factory=list)


TRANSITIONS = {
    NewsletterStatus.DRAFT: {NewsletterStatus.READY_FOR_REVIEW},
    NewsletterStatus.READY_FOR_REVIEW: {NewsletterStatus.APPROVED, NewsletterStatus.REJECTED},
    NewsletterStatus.APPROVED: {
        NewsletterStatus.SCHEDULED,
        NewsletterStatus.SENT,
        NewsletterStatus.FAILED,
    },
    NewsletterStatus.SCHEDULED: {NewsletterStatus.SENT, NewsletterStatus.FAILED},
    NewsletterStatus.FAILED: {NewsletterStatus.APPROVED},
}


class Newsletter(BaseModel):
    id: str = Field(default_factory=uid)
    title: str
    edition_date: date = Field(default_factory=lambda: utcnow().date())
    executive_summary: str
    sections: list[NewsletterSection]
    status: NewsletterStatus = NewsletterStatus.DRAFT
    audience_id: str
    subscriber_id: str | None = None
    recipients: list[str] = Field(default_factory=list)
    research_mode: Literal["deterministic", "llm"] = "deterministic"
    analysis_mode: Literal["deterministic", "llm", "mixed"] = "deterministic"
    analysis_warnings: list[str] = Field(default_factory=list)
    html_path: str | None = None
    text_path: str | None = None
    json_path: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    approved_at: datetime | None = None
    sent_at: datetime | None = None

    def transition_to(self, status: NewsletterStatus) -> None:
        if status not in TRANSITIONS.get(self.status, set()):
            raise InvalidStatusTransition(f"Cannot transition {self.status} to {status}")
        self.status = status
        if status == NewsletterStatus.APPROVED:
            self.approved_at = utcnow()
        if status == NewsletterStatus.SENT:
            self.sent_at = utcnow()


class SourceRequest(BaseModel):
    source_name: str
    url: str
    lookback_hours: int = 24
    retrieve_articles: bool = False
    trust_level: str = "industry"
    llm_allowed: bool = True
    verticals: list[str] = Field(default_factory=list)


class ResearchContext(BaseModel):
    vertical_id: str
    lookback_hours: int = 24


class ResearchPlan(BaseModel):
    vertical_id: str
    research_areas: list[str]
    keywords: list[str]


class EmailMessage(BaseModel):
    subject: str
    recipients: list[str]
    text_body: str
    html_body: str
    html_path: str | None = None
    text_path: str | None = None


class DeliveryResult(BaseModel):
    success: bool
    provider_message_id: str | None = None
    error: str | None = None


class ScheduledDeliveryOutcome(BaseModel):
    subscriber_id: str
    newsletter_id: str
    success: bool
    research_mode: Literal["deterministic", "llm"]
    analysis_mode: Literal["deterministic", "llm", "mixed"]
    error: str | None = None
