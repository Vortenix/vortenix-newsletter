"""Minimal offline connector example."""
from hashlib import sha256
from vortenix_newsletter.domain.models import SourceDocument, SourceRequest

class SampleConnector:
    """Return one stable document without external I/O."""
    async def fetch(self, request: SourceRequest) -> list[SourceDocument]:
        content = "Example evidence supplied by an offline connector."
        return [SourceDocument(source_name=request.source_name,title="Example source",content=content,url="https://example.com/research",content_hash=sha256(content.encode()).hexdigest())]
