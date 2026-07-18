from pathlib import Path
import pytest
from pydantic import ValidationError
from vortenix_newsletter.config.loader import load_config
from vortenix_newsletter.config.models import RankingWeights
from vortenix_newsletter.domain.enums import NewsletterStatus
from vortenix_newsletter.domain.exceptions import InvalidStatusTransition
from vortenix_newsletter.domain.models import Newsletter, Subscriber
from vortenix_newsletter.ingestion.deduplicator import deduplicate
from vortenix_newsletter.ingestion.rss_connector import RSSConnector
from vortenix_newsletter.domain.models import SourceRequest
from vortenix_newsletter.verticals.registry import VerticalRegistry
from vortenix_newsletter.newsletter.composer import compose
from vortenix_newsletter.providers.email.console_provider import ConsoleEmailProvider
from vortenix_newsletter.providers.email.factory import configured_recipients, create_email_provider, newsletter_recipients
from vortenix_newsletter.providers.email.smtp_provider import SMTPEmailProvider
from vortenix_newsletter.persistence.database import Base
from vortenix_newsletter.persistence import orm_models  # noqa: F401
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from vortenix_newsletter.workflows.newsletter_workflow import run_personalized

def test_config_and_registry():
    cfg=load_config(); assert len(cfg.verticals)==4; assert set(VerticalRegistry(cfg.verticals).ids())==set(x.id for x in cfg.verticals)
def test_bad_weights():
    with pytest.raises(ValidationError): RankingWeights(relevance=1,novelty=1)
def test_status_transition():
    n=Newsletter(title="x",executive_summary="x",sections=[],audience_id="a")
    with pytest.raises(InvalidStatusTransition): n.transition_to(NewsletterStatus.SENT)
    n.transition_to(NewsletterStatus.READY_FOR_REVIEW); n.transition_to(NewsletterStatus.APPROVED); n.transition_to(NewsletterStatus.SENT)
    assert n.sent_at is not None
@pytest.mark.asyncio
async def test_fixture_ingestion_and_deduplication():
    docs=await RSSConnector().fetch(SourceRequest(source_name="fixture",url="tests/fixtures/sample.rss",lookback_hours=99999))
    assert len(docs)==3; assert len(deduplicate(docs+docs))==3

def test_private_email_environment(monkeypatch):
    monkeypatch.setenv("VORTENIX_EMAIL_PROVIDER", "console")
    monkeypatch.setenv("VORTENIX_RECIPIENTS", "first@example.com, second@example.com")
    assert isinstance(create_email_provider(), ConsoleEmailProvider)
    assert configured_recipients(["fallback@example.com"]) == ["first@example.com", "second@example.com"]

def test_newsletter_title_uses_ascii_separator():
    cfg = load_config()
    newsletter = compose(cfg.audiences[0], [], cfg.verticals)
    assert newsletter.title == "Vortenix Newsletter - Daily Research Brief"
    assert "—" not in newsletter.title

def test_smtp_sender_name_defaults_to_vortenix(monkeypatch):
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_FROM_EMAIL", "sender@example.com")
    monkeypatch.delenv("SMTP_USERNAME", raising=False)
    monkeypatch.delenv("SMTP_FROM_NAME", raising=False)
    provider = SMTPEmailProvider()
    assert provider.sender_name == "Vortenix Newsletter"

def test_subscriber_restricts_parent_audience_verticals():
    cfg = load_config()
    subscriber = Subscriber(
        id="finance_reader",
        name="Finance Reader",
        email="finance@example.com",
        audience_id="anish_daily",
        enabled_verticals=["finance"],
    )
    personalized = subscriber.personalized_audience(cfg.audience("anish_daily"))
    assert personalized.enabled_verticals == ["finance"]
    assert personalized.recipients == ["finance@example.com"]

def test_personalized_recipient_is_not_overridden(monkeypatch):
    monkeypatch.setenv("VORTENIX_RECIPIENTS", "global@example.com")
    newsletter = Newsletter(
        title="Personalized",
        executive_summary="Summary",
        sections=[],
        audience_id="anish_daily",
        subscriber_id="finance_reader",
        recipients=["finance@example.com"],
    )
    assert newsletter_recipients(newsletter, ["fallback@example.com"]) == [
        "finance@example.com"
    ]

@pytest.mark.asyncio
async def test_personalized_workflow_creates_independent_newsletters():
    cfg = load_config()
    subscribers = [
        Subscriber(
            id="finance_reader",
            name="Finance Reader",
            email="finance@example.com",
            audience_id="anish_daily",
            enabled_verticals=["finance"],
        ),
        Subscriber(
            id="technology_reader",
            name="Technology Reader",
            email="technology@example.com",
            audience_id="anish_daily",
            enabled_verticals=[
                "ai_infrastructure",
                "semiconductors",
                "technology_radar",
            ],
        ),
    ]
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        newsletters = await run_personalized(
            cfg,
            cfg.audience("anish_daily"),
            subscribers,
            session,
            demo=True,
        )
    assert len(newsletters) == 2
    assert newsletters[0].subscriber_id == "finance_reader"
    assert newsletters[0].recipients == ["finance@example.com"]
    assert [section.vertical_id for section in newsletters[0].sections] == ["finance"]
    assert newsletters[1].subscriber_id == "technology_reader"
    assert newsletters[1].recipients == ["technology@example.com"]
    assert {section.vertical_id for section in newsletters[1].sections} == {
        "ai_infrastructure",
        "semiconductors",
        "technology_radar",
    }
