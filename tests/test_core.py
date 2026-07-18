from pathlib import Path
import pytest
from pydantic import ValidationError
from vortenix_newsletter.config.loader import load_config
from vortenix_newsletter.config.models import RankingWeights
from vortenix_newsletter.domain.enums import NewsletterStatus
from vortenix_newsletter.domain.exceptions import InvalidStatusTransition
from vortenix_newsletter.domain.models import Newsletter
from vortenix_newsletter.ingestion.deduplicator import deduplicate
from vortenix_newsletter.ingestion.rss_connector import RSSConnector
from vortenix_newsletter.domain.models import SourceRequest
from vortenix_newsletter.verticals.registry import VerticalRegistry
from vortenix_newsletter.newsletter.composer import compose
from vortenix_newsletter.providers.email.console_provider import ConsoleEmailProvider
from vortenix_newsletter.providers.email.factory import configured_recipients, create_email_provider
from vortenix_newsletter.providers.email.smtp_provider import SMTPEmailProvider

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
    assert newsletter.title == "Vortenix Research Brief - Anish Daily Research Brief"
    assert "—" not in newsletter.title

def test_smtp_sender_name_defaults_to_vortenix(monkeypatch):
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_FROM_EMAIL", "sender@example.com")
    monkeypatch.delenv("SMTP_USERNAME", raising=False)
    monkeypatch.delenv("SMTP_FROM_NAME", raising=False)
    provider = SMTPEmailProvider()
    assert provider.sender_name == "Vortenix Newsletter"
