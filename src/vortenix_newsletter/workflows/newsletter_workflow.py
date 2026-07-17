import logging
from pathlib import Path
from vortenix_newsletter.domain.enums import NewsletterStatus
from vortenix_newsletter.domain.models import SourceRequest
from vortenix_newsletter.ingestion.deduplicator import deduplicate
from vortenix_newsletter.ingestion.rss_connector import RSSConnector
from vortenix_newsletter.newsletter.composer import compose
from vortenix_newsletter.newsletter.renderer import Renderer
from vortenix_newsletter.persistence.repositories import NewsletterRepository,ResultRepository,SourceRepository
from vortenix_newsletter.research.validator import validate_findings
from vortenix_newsletter.verticals.registry import VerticalRegistry
log=logging.getLogger(__name__)
async def run_daily(config,audience,session,demo=False):
    docs=[]; connector=RSSConnector()
    for source in config.sources:
        if not source.enabled: continue
        try:
            url="tests/fixtures/sample.rss" if demo else source.url
            docs.extend(await connector.fetch(SourceRequest(source_name=source.name,url=url,lookback_hours=24*3650 if demo else 24,retrieve_articles=False if demo else source.retrieve_articles)))
        except Exception as exc: log.warning("source_failed",extra={"source":source.name,"error":str(exc)})
    docs=deduplicate(docs); SourceRepository(session).add_all(docs); results=[]; registry=VerticalRegistry(config.verticals)
    for ident in audience.enabled_verticals:
        try:
            result=await registry.get(ident).analyse(docs); result.findings,failures=validate_findings(result.findings,docs,config.application.confidence_threshold)
            if failures: log.warning("finding_validation_failed",extra={"count":len(failures),"vertical":ident})
            ResultRepository(session).add(result); results.append(result)
        except Exception as exc: log.warning("vertical_failed",extra={"vertical":ident,"error":str(exc)})
    newsletter=Renderer().render(compose(audience,results,config.verticals)); newsletter.transition_to(NewsletterStatus.READY_FOR_REVIEW); NewsletterRepository(session).save(newsletter); return newsletter
