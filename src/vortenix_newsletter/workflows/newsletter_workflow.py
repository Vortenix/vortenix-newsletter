"""Newsletter generation workflows."""

from __future__ import annotations

import logging
import os

from vortenix_newsletter.domain.enums import NewsletterStatus
from vortenix_newsletter.domain.models import (
    Audience,
    Newsletter,
    SourceDocument,
    SourceRequest,
    Subscriber,
    ScheduledDeliveryOutcome,
    VerticalResearchResult,
)
from vortenix_newsletter.ingestion.deduplicator import deduplicate
from vortenix_newsletter.ingestion.rss_connector import RSSConnector
from vortenix_newsletter.newsletter.service import NewsletterService
from vortenix_newsletter.newsletter.composer import compose
from vortenix_newsletter.newsletter.renderer import Renderer
from vortenix_newsletter.persistence.repositories import (
    NewsletterRepository,
    ResultRepository,
    SourceRepository,
)
from vortenix_newsletter.providers.llm.base import LLMProvider
from vortenix_newsletter.providers.email.base import EmailProvider
from vortenix_newsletter.providers.email.factory import newsletter_recipients
from vortenix_newsletter.domain.exceptions import ConfigurationError
from vortenix_newsletter.providers.llm.factory import create_llm_provider, research_mode
from vortenix_newsletter.research.llm_analyser import LLMResearchAnalyser
from vortenix_newsletter.research.validator import validate_findings
from vortenix_newsletter.verticals.registry import VerticalRegistry

log = logging.getLogger(__name__)


async def collect_documents(
    config: object, session: object, demo: bool = False
) -> list[SourceDocument]:
    """Collect enabled sources once and persist the deduplicated documents."""
    documents: list[SourceDocument] = []
    connector = RSSConnector()
    for source in config.sources:  # type: ignore[attr-defined]
        if not source.enabled:
            continue
        try:
            url = "tests/fixtures/sample.rss" if demo else source.url
            request = SourceRequest(
                source_name=source.name,
                url=url,
                lookback_hours=24 * 3650 if demo else 24,
                retrieve_articles=False if demo else source.retrieve_articles,
            )
            documents.extend(await connector.fetch(request))
        except Exception as exc:
            log.warning("source_failed", extra={"source": source.name, "error": str(exc)})
    documents = deduplicate(documents)
    SourceRepository(session).add_all(documents)
    return documents


async def research_verticals(
    config: object,
    session: object,
    documents: list[SourceDocument],
    vertical_ids: list[str],
    llm_provider: LLMProvider | None = None,
    mode: str | None = None,
) -> dict[str, VerticalResearchResult]:
    """Analyse each requested vertical once and return results keyed by vertical ID."""
    registry = VerticalRegistry(config.verticals)  # type: ignore[attr-defined]
    vertical_configs = {
        item.id: item
        for item in config.verticals  # type: ignore[attr-defined]
    }
    selected_mode = mode or research_mode()
    provider = llm_provider
    if selected_mode == "llm" and provider is None:
        try:
            provider = create_llm_provider()
        except Exception as exc:
            log.warning("llm_provider_unavailable", extra={"error": str(exc)})
    results: dict[str, VerticalResearchResult] = {}
    for vertical_id in dict.fromkeys(vertical_ids):
        try:
            if selected_mode == "llm" and provider is not None:
                try:
                    result = await LLMResearchAnalyser(provider).analyse(
                        vertical_configs[vertical_id],
                        documents,
                    )
                except Exception as exc:
                    log.warning(
                        "llm_analysis_failed_falling_back: %s",
                        exc,
                        extra={"vertical": vertical_id, "error": str(exc)},
                    )
                    result = await registry.get(vertical_id).analyse(documents)
                    result.analysis_warnings.append(
                        f"{vertical_id}: LLM unavailable; deterministic fallback used."
                    )
            else:
                result = await registry.get(vertical_id).analyse(documents)
            result.findings, failures = validate_findings(
                result.findings,
                documents,
                config.application.confidence_threshold,  # type: ignore[attr-defined]
            )
            if failures:
                log.warning(
                    "finding_validation_failed",
                    extra={"count": len(failures), "vertical": vertical_id},
                )
            ResultRepository(session).add(result)
            results[vertical_id] = result
        except Exception as exc:
            log.warning(
                "vertical_failed",
                extra={"vertical": vertical_id, "error": str(exc)},
            )
    return results


def persist_newsletter(
    config: object,
    session: object,
    audience: Audience,
    results: dict[str, VerticalResearchResult],
    subscriber: Subscriber | None = None,
    requested_mode: str = "deterministic",
) -> Newsletter:
    """Compose and persist one review-ready newsletter."""
    selected = [results[item] for item in audience.enabled_verticals if item in results]
    newsletter = compose(audience, selected, config.verticals)  # type: ignore[attr-defined]
    newsletter.recipients = list(audience.recipients)
    newsletter.subscriber_id = subscriber.id if subscriber else None
    newsletter.research_mode = requested_mode  # type: ignore[assignment]
    actual_modes = {result.analysis_mode for result in selected}
    if actual_modes == {"llm"}:
        newsletter.analysis_mode = "llm"
    elif actual_modes == {"deterministic"} or not actual_modes:
        newsletter.analysis_mode = "deterministic"
    else:
        newsletter.analysis_mode = "mixed"
    newsletter.analysis_warnings = [
        warning for result in selected for warning in result.analysis_warnings
    ]
    newsletter = Renderer().render(newsletter)
    newsletter.transition_to(NewsletterStatus.READY_FOR_REVIEW)
    NewsletterRepository(session).save(newsletter)
    return newsletter


async def run_daily(
    config: object,
    audience: Audience,
    session: object,
    demo: bool = False,
    llm_provider: LLMProvider | None = None,
) -> Newsletter:
    """Generate the existing audience-level newsletter."""
    documents = await collect_documents(config, session, demo)
    mode = research_mode()
    results = await research_verticals(
        config,
        session,
        documents,
        audience.enabled_verticals,
        llm_provider,
        mode,
    )
    return persist_newsletter(config, session, audience, results, requested_mode=mode)


async def run_personalized(
    config: object,
    audience: Audience,
    subscribers: list[Subscriber],
    session: object,
    demo: bool = False,
    llm_provider: LLMProvider | None = None,
) -> list[Newsletter]:
    """Generate one independently reviewable newsletter per subscriber."""
    if not subscribers:
        return []
    personalized = [subscriber.personalized_audience(audience) for subscriber in subscribers]
    documents = await collect_documents(config, session, demo)
    result_sets: dict[str, dict[str, VerticalResearchResult]] = {}
    for mode in dict.fromkeys(subscriber.research_mode for subscriber in subscribers):
        vertical_ids = [
            vertical
            for subscriber, subscriber_audience in zip(
                subscribers,
                personalized,
                strict=True,
            )
            if subscriber.research_mode == mode
            for vertical in subscriber_audience.enabled_verticals
        ]
        result_sets[mode] = await research_verticals(
            config,
            session,
            documents,
            vertical_ids,
            llm_provider,
            mode,
        )
    return [
        persist_newsletter(
            config,
            session,
            subscriber_audience,
            result_sets[subscriber.research_mode],
            subscriber,
            subscriber.research_mode,
        )
        for subscriber, subscriber_audience in zip(subscribers, personalized, strict=True)
    ]


async def run_scheduled_delivery(
    config: object,
    audience: Audience,
    subscribers: list[Subscriber],
    session: object,
    email_provider: EmailProvider,
    demo: bool = False,
    llm_provider: LLMProvider | None = None,
) -> list[ScheduledDeliveryOutcome]:
    """Generate, auto-approve, and deliver one newsletter per enabled subscriber."""
    allowed = os.getenv("VORTENIX_ALLOW_AUTOMATIC_SEND", "false").strip().casefold()
    if allowed not in {"1", "true", "yes", "on"}:
        raise ConfigurationError(
            "Automatic delivery is disabled; set VORTENIX_ALLOW_AUTOMATIC_SEND=true locally"
        )

    newsletters = await run_personalized(config, audience, subscribers, session, demo, llm_provider)
    repository = NewsletterRepository(session)
    service = NewsletterService(repository, email_provider)
    outcomes: list[ScheduledDeliveryOutcome] = []
    for newsletter in newsletters:
        subscriber_id = newsletter.subscriber_id or "unknown"
        try:
            service.approve(newsletter.id)
            recipients = newsletter_recipients(newsletter, audience.recipients)
            result = await service.send(newsletter.id, recipients)
            outcomes.append(
                ScheduledDeliveryOutcome(
                    subscriber_id=subscriber_id,
                    newsletter_id=newsletter.id,
                    success=result.success,
                    research_mode=newsletter.research_mode,
                    analysis_mode=newsletter.analysis_mode,
                    error=result.error,
                )
            )
        except Exception as exc:
            log.exception(
                "scheduled_delivery_failed",
                extra={"subscriber_id": subscriber_id, "newsletter_id": newsletter.id},
            )
            outcomes.append(
                ScheduledDeliveryOutcome(
                    subscriber_id=subscriber_id,
                    newsletter_id=newsletter.id,
                    success=False,
                    research_mode=newsletter.research_mode,
                    analysis_mode=newsletter.analysis_mode,
                    error=str(exc),
                )
            )
    return outcomes
