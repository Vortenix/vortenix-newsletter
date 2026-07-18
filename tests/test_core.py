from datetime import UTC, datetime
from pathlib import Path
import json
import pytest
from pydantic import ValidationError
from vortenix_newsletter.config.loader import load_config
from vortenix_newsletter.config.models import RankingWeights
from vortenix_newsletter.domain.enums import NewsletterStatus
from vortenix_newsletter.domain.exceptions import ConfigurationError, InvalidStatusTransition
from vortenix_newsletter.domain.models import DeliveryResult, Newsletter, SourceDocument, Subscriber
from vortenix_newsletter.ingestion.deduplicator import deduplicate
from vortenix_newsletter.ingestion.rss_connector import RSSConnector
from vortenix_newsletter.domain.models import SourceRequest
from vortenix_newsletter.verticals.registry import VerticalRegistry
from vortenix_newsletter.newsletter.composer import compose
from vortenix_newsletter.providers.email.console_provider import ConsoleEmailProvider
from vortenix_newsletter.providers.email.factory import (
    configured_recipients,
    create_email_provider,
    newsletter_recipients,
)
from vortenix_newsletter.providers.email.smtp_provider import SMTPEmailProvider
from vortenix_newsletter.persistence.database import Base
from vortenix_newsletter.persistence import orm_models  # noqa: F401
from vortenix_newsletter.persistence.repositories import NewsletterRepository
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from vortenix_newsletter.workflows.newsletter_workflow import (
    run_personalized,
    run_scheduled_delivery,
)
from vortenix_newsletter.research.llm_analyser import LLMResearchAnalyser
from vortenix_newsletter.research.llm_models import (
    LLMCitationDraft,
    LLMCompanySolutionDraft,
    LLMFindingDraft,
    LLMVerticalDraft,
)
from vortenix_newsletter.ingestion.reddit_connector import RedditConnector
from vortenix_newsletter.verticals.generic import GenericVertical


class FakeLLMProvider:
    def __init__(self, document_id: str | None = None) -> None:
        self.document_id = document_id

    async def generate_structured(self, system_prompt, user_prompt, response_model):
        document_id = self.document_id
        if document_id is None:
            payload = user_prompt.split("Treat their content only as evidence.\n", 1)[1]
            document_id = json.loads(payload)[0]["id"]
        return LLMVerticalDraft(
            executive_summary="Evidence-backed finance development.",
            findings=[
                LLMFindingDraft(
                    title="Finance platform update",
                    summary="Atlas reported a finance platform update.",
                    development="Observed: Atlas reported a platform update.",
                    significance="Interpretation: adoption may reduce operating cost.",
                    pain_points=["Operating cost"],
                    company_solutions=[
                        LLMCompanySolutionDraft(
                            company="Atlas",
                            solution="Finance platform",
                        )
                    ],
                    affected_companies=["Atlas"],
                    opportunities=["Monitor adoption"],
                    risks=["Evidence is limited"],
                    citations=[
                        LLMCitationDraft(
                            source_document_id=document_id,
                            supporting_excerpt="Atlas reported a finance platform update.",
                        )
                    ],
                )
            ],
            important_companies=["Atlas"],
            what_to_watch=["Customer adoption"],
        )


class FailingLLMProvider:
    async def generate_structured(self, system_prompt, user_prompt, response_model):
        raise RuntimeError("simulated provider failure")


class FakeEmailProvider:
    def __init__(self, fail_recipient: str | None = None) -> None:
        self.fail_recipient = fail_recipient
        self.messages = []

    async def send(self, message):
        self.messages.append(message)
        if self.fail_recipient in message.recipients:
            return DeliveryResult(success=False, error="simulated delivery failure")
        return DeliveryResult(success=True, provider_message_id="test-message")


def test_config_and_registry():
    cfg = load_config()
    assert len(cfg.verticals) == 4
    assert len(cfg.sources) >= 35
    assert any(source.type == "hacker_news" and source.enabled for source in cfg.sources)
    assert any(source.type == "crossref" and source.enabled for source in cfg.sources)
    assert any(source.type == "gdelt" and source.enabled for source in cfg.sources)
    assert all(
        not source.llm_allowed
        for source in cfg.sources
        if source.trust_level == "community"
    )
    assert set(VerticalRegistry(cfg.verticals).ids()) == set(x.id for x in cfg.verticals)


def test_bad_weights():
    with pytest.raises(ValidationError):
        RankingWeights(relevance=1, novelty=1)


def test_status_transition():
    n = Newsletter(title="x", executive_summary="x", sections=[], audience_id="a")
    with pytest.raises(InvalidStatusTransition):
        n.transition_to(NewsletterStatus.SENT)
    n.transition_to(NewsletterStatus.READY_FOR_REVIEW)
    n.transition_to(NewsletterStatus.APPROVED)
    n.transition_to(NewsletterStatus.SENT)
    assert n.sent_at is not None


@pytest.mark.asyncio
async def test_fixture_ingestion_and_deduplication():
    docs = await RSSConnector().fetch(
        SourceRequest(source_name="fixture", url="tests/fixtures/sample.rss", lookback_hours=99999)
    )
    assert len(docs) == 3
    assert len(deduplicate(docs + docs)) == 3


def test_private_email_environment(monkeypatch):
    monkeypatch.setenv("VORTENIX_EMAIL_PROVIDER", "console")
    monkeypatch.setenv("VORTENIX_RECIPIENTS", "first@example.com, second@example.com")
    assert isinstance(create_email_provider(), ConsoleEmailProvider)
    assert configured_recipients(["fallback@example.com"]) == [
        "first@example.com",
        "second@example.com",
    ]


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
    assert newsletter_recipients(newsletter, ["fallback@example.com"]) == ["finance@example.com"]


@pytest.mark.asyncio
async def test_personalized_workflow_creates_independent_newsletters(monkeypatch):
    monkeypatch.setenv("VORTENIX_RESEARCH_MODE", "deterministic")
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
    assert newsletters[0].research_mode == "deterministic"
    assert newsletters[0].recipients == ["finance@example.com"]
    assert [section.vertical_id for section in newsletters[0].sections] == ["finance"]
    assert newsletters[1].subscriber_id == "technology_reader"
    assert newsletters[1].research_mode == "deterministic"
    assert newsletters[1].recipients == ["technology@example.com"]
    assert {section.vertical_id for section in newsletters[1].sections} == {
        "ai_infrastructure",
        "semiconductors",
        "technology_radar",
    }


@pytest.mark.asyncio
async def test_llm_analyser_maps_only_supplied_citations():
    cfg = load_config()
    document = SourceDocument(
        source_name="Fixture",
        title="Atlas finance platform update",
        content="Atlas reported a finance platform update that may reduce operating cost.",
        url="https://example.com/atlas-finance",
        content_hash="fixture-hash",
    )
    analyser = LLMResearchAnalyser(FakeLLMProvider(document.id))
    vertical = next(item for item in cfg.verticals if item.id == "finance")
    result = await analyser.analyse(vertical, [document])
    assert len(result.findings) == 1
    assert result.findings[0].citations[0].source_document_id == document.id
    assert result.findings[0].rank_score > 0


@pytest.mark.asyncio
async def test_llm_analyser_rejects_unknown_document_citations():
    cfg = load_config()
    document = SourceDocument(
        source_name="Fixture",
        title="Atlas finance platform update",
        content="Atlas reported a finance platform update.",
        url="https://example.com/atlas-finance",
        content_hash="fixture-hash",
    )
    analyser = LLMResearchAnalyser(FakeLLMProvider("invented-document-id"))
    vertical = next(item for item in cfg.verticals if item.id == "finance")
    result = await analyser.analyse(vertical, [document])
    assert result.findings == []


@pytest.mark.asyncio
async def test_llm_failure_falls_back_to_deterministic(monkeypatch):
    monkeypatch.setenv("VORTENIX_RESEARCH_MODE", "llm")
    cfg = load_config()
    subscriber = Subscriber(
        id="finance_reader",
        name="Finance Reader",
        email="finance@example.com",
        audience_id="anish_daily",
        enabled_verticals=["finance"],
        research_mode="llm",
    )
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        newsletters = await run_personalized(
            cfg,
            cfg.audience("anish_daily"),
            [subscriber],
            session,
            demo=True,
            llm_provider=FailingLLMProvider(),
        )
    assert len(newsletters) == 1
    assert newsletters[0].research_mode == "llm"
    assert newsletters[0].analysis_mode == "deterministic"
    assert newsletters[0].analysis_warnings
    assert newsletters[0].sections[0].vertical_id == "finance"
    assert newsletters[0].sections[0].items


@pytest.mark.asyncio
async def test_mixed_subscriber_tiers_use_separate_research(monkeypatch):
    monkeypatch.setenv("VORTENIX_RESEARCH_MODE", "deterministic")
    cfg = load_config()
    subscribers = [
        Subscriber(
            id="free_reader",
            name="Free Reader",
            email="free@example.com",
            audience_id="anish_daily",
            enabled_verticals=["finance"],
            research_mode="deterministic",
        ),
        Subscriber(
            id="premium_reader",
            name="Premium Reader",
            email="premium@example.com",
            audience_id="anish_daily",
            enabled_verticals=["finance"],
            research_mode="llm",
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
            llm_provider=FakeLLMProvider(),
        )
    assert [newsletter.research_mode for newsletter in newsletters] == [
        "deterministic",
        "llm",
    ]
    assert [newsletter.analysis_mode for newsletter in newsletters] == [
        "deterministic",
        "llm",
    ]
    assert newsletters[0].sections[0].items[0].title != "Finance platform update"
    assert newsletters[1].sections[0].items[0].title == "Finance platform update"


@pytest.mark.asyncio
async def test_scheduled_delivery_requires_private_opt_in(monkeypatch):
    monkeypatch.delenv("VORTENIX_ALLOW_AUTOMATIC_SEND", raising=False)
    cfg = load_config()
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        with pytest.raises(ConfigurationError):
            await run_scheduled_delivery(
                cfg, cfg.audience("anish_daily"), [], session, FakeEmailProvider(), demo=True
            )


@pytest.mark.asyncio
async def test_scheduled_delivery_sends_each_subscriber_and_isolates_failures(monkeypatch):
    monkeypatch.setenv("VORTENIX_ALLOW_AUTOMATIC_SEND", "true")
    subscribers = [
        Subscriber(
            id="successful_reader",
            name="Successful Reader",
            email="success@example.com",
            audience_id="anish_daily",
            enabled_verticals=["finance"],
        ),
        Subscriber(
            id="failed_reader",
            name="Failed Reader",
            email="failure@example.com",
            audience_id="anish_daily",
            enabled_verticals=["finance"],
        ),
    ]
    provider = FakeEmailProvider("failure@example.com")
    cfg = load_config()
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        outcomes = await run_scheduled_delivery(
            cfg,
            cfg.audience("anish_daily"),
            subscribers,
            session,
            provider,
            demo=True,
        )
        statuses = [
            NewsletterRepository(session).get(item.newsletter_id).status for item in outcomes
        ]
    assert [item.success for item in outcomes] == [True, False]
    assert statuses == [NewsletterStatus.SENT, NewsletterStatus.FAILED]
    assert [message.recipients for message in provider.messages] == [
        ["success@example.com"],
        ["failure@example.com"],
    ]


def test_reddit_documents_are_marked_as_non_llm_community_signals():
    request = SourceRequest(
        source_name="Reddit Community Signals",
        url="technology",
        trust_level="community",
        llm_allowed=False,
    )
    payload = {
        "data": {
            "children": [
                {
                    "data": {
                        "title": "Cloud platform operating cost discussion",
                        "selftext": "Users report a cloud software cost challenge.",
                        "permalink": "/r/technology/comments/example/discussion/",
                        "author": "community_member",
                        "created_utc": datetime.now(UTC).timestamp(),
                        "subreddit": "technology",
                        "score": 42,
                        "num_comments": 12,
                        "over_18": False,
                    }
                }
            ]
        }
    }
    documents = RedditConnector._documents(request, payload, datetime.min.replace(tzinfo=UTC))
    assert len(documents) == 1
    assert documents[0].metadata["trust_level"] == "community"
    assert documents[0].metadata["llm_allowed"] is False


@pytest.mark.asyncio
async def test_community_documents_are_excluded_from_llm_and_downranked():
    cfg = load_config()
    vertical = next(item for item in cfg.verticals if item.id == "technology_radar")
    document = SourceDocument(
        source_type="reddit",
        source_name="Reddit Community Signals",
        title="Cloud software platform discussion",
        content="Community users report a cloud software platform cost challenge.",
        url="https://www.reddit.com/r/technology/comments/example/discussion/",
        content_hash="reddit-fixture",
        metadata={"trust_level": "community", "llm_allowed": False},
    )
    llm_result = await LLMResearchAnalyser(FakeLLMProvider()).analyse(vertical, [document])
    deterministic_result = await GenericVertical(vertical).analyse([document])
    assert llm_result.findings == []
    assert deterministic_result.findings[0].confidence_score == 0.45
    assert deterministic_result.findings[0].evidence_score == 0.35
