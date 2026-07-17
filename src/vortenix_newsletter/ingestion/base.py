from typing import Protocol
from vortenix_newsletter.domain.models import SourceDocument, SourceRequest
class SourceConnector(Protocol):
    """Contract for adapters that collect normalised source documents."""

    async def fetch(self, request: SourceRequest) -> list[SourceDocument]: ...
