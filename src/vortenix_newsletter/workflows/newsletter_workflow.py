"""Newsletter generation workflows."""

from __future__ import annotations

import logging

from vortenix_newsletter.domain.enums import NewsletterStatus
from vortenix_newsletter.domain.models import (
    Audience,
    Newsletter,
    SourceDocument,
    SourceRequest,
    Subscriber,
    VerticalResearchResult,
)
from vortenix_newsletter.ingestion.deduplicator import deduplicate
from vortenix_newsletter.ingestion.rss_connector import RSSConnector
from vortenix_newsletter.newsletter.composer import compose
from vortenix_newsletter.newsletter.renderer import Renderer
from vortenix_newsletter.persistence.repositories import (
    NewsletterRepository,
    ResultRepository,
    SourceRepository,
)
from vortenix_newsletter.research.validator import validate_findings
from vortenix_newsletter.verticals.registry import VerticalRegistry

log = logging.getLogger(__name__)


async def collect_documents(config: object, session: object, demo: bool = False) -> list[SourceDocument]:
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
) -> dict[str, VerticalResearchResult]:
    """Analyse each requested vertical once and return results keyed by vertical ID."""
    registry = VerticalRegistry(config.verticals)  # type: ignore[attr-defined]
    results: dict[str, VerticalResearchResult] = {}
    for vertical_id in dict.fromkeys(vertical_ids):
        try:
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
) -> Newsletter:
    """Compose and persist one review-ready newsletter."""
    selected = [results[item] for item in audience.enabled_verticals if item in results]
    newsletter = compose(audience, selected, config.verticals)  # type: ignore[attr-defined]
    newsletter.recipients = list(audience.recipients)
    newsletter.subscriber_id = subscriber.id if subscriber else None
    newsletter = Renderer().render(newsletter)
    newsletter.transition_to(NewsletterStatus.READY_FOR_REVIEW)
    NewsletterRepository(session).save(newsletter)
    return newsletter


async def run_daily(config: object, audience: Audience, session: object, demo: bool = False) -> Newsletter:
    """Generate the existing audience-level newsletter."""
    documents = await collect_documents(config, session, demo)
    results = await research_verticals(
        config,
        session,
        documents,
        audience.enabled_verticals,
    )
    return persist_newsletter(config, session, audience, results)


async def run_personalized(
    config: object,
    audience: Audience,
    subscribers: list[Subscriber],
    session: object,
    demo: bool = False,
) -> list[Newsletter]:
    """Generate one independently reviewable newsletter per subscriber."""
    if not subscribers:
        return []
    personalized = [subscriber.personalized_audience(audience) for subscriber in subscribers]
    vertical_ids = [
        vertical
        for subscriber_audience in personalized
        for vertical in subscriber_audience.enabled_verticals
    ]
    documents = await collect_documents(config, session, demo)
    results = await research_verticals(config, session, documents, vertical_ids)
    return [
        persist_newsletter(config, session, subscriber_audience, results, subscriber)
        for subscriber, subscriber_audience in zip(subscribers, personalized, strict=True)
    ]
