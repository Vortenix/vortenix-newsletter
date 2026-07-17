from urllib.parse import urlparse
from vortenix_newsletter.domain.models import ResearchFinding, SourceDocument
def validate_findings(findings: list[ResearchFinding],documents: list[SourceDocument],threshold: float=.35)->tuple[list[ResearchFinding],list[str]]:
    ids={d.id for d in documents}; valid=[]; errors=[]; seen=set()
    for finding in findings:
        reason=None
        if not finding.summary.strip(): reason="empty summary"
        elif finding.confidence_score<threshold: reason="low confidence"
        elif not finding.citations: reason="missing citation"
        elif any(c.source_document_id not in ids or urlparse(str(c.url)).scheme not in {"http","https"} for c in finding.citations): reason="invalid citation"
        elif finding.title.casefold() in seen: reason="duplicate finding"
        if reason: errors.append(f"{finding.id}: {reason}")
        else: valid.append(finding); seen.add(finding.title.casefold())
    return valid,errors
