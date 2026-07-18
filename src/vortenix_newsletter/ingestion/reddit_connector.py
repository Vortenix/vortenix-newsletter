"""Credentialed Reddit community-signal ingestion."""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from hashlib import sha256

import httpx

from vortenix_newsletter.domain.enums import SourceType
from vortenix_newsletter.domain.exceptions import ConfigurationError
from vortenix_newsletter.domain.models import SourceDocument, SourceRequest


class RedditConnector:
    """Read recent subreddit posts through Reddit OAuth without fetching comments."""

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self.client = client

    async def fetch(self, request: SourceRequest) -> list[SourceDocument]:
        client_id = os.getenv("REDDIT_CLIENT_ID", "").strip()
        client_secret = os.getenv("REDDIT_CLIENT_SECRET", "").strip()
        user_agent = os.getenv("REDDIT_USER_AGENT", "").strip()
        if not all((client_id, client_secret, user_agent)):
            raise ConfigurationError(
                "Reddit requires REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, and REDDIT_USER_AGENT"
            )

        owns_client = self.client is None
        client = self.client or httpx.AsyncClient(timeout=15, follow_redirects=True)
        try:
            token_response = await client.post(
                "https://www.reddit.com/api/v1/access_token",
                auth=(client_id, client_secret),
                headers={"User-Agent": user_agent},
                data={"grant_type": "client_credentials"},
            )
            token_response.raise_for_status()
            token = token_response.json()["access_token"]
            listing_response = await client.get(
                f"https://oauth.reddit.com/r/{request.url}/new",
                headers={"Authorization": f"Bearer {token}", "User-Agent": user_agent},
                params={"limit": 50, "raw_json": 1},
            )
            listing_response.raise_for_status()
            cutoff = datetime.now(UTC) - timedelta(hours=request.lookback_hours)
            return self._documents(request, listing_response.json(), cutoff)
        finally:
            if owns_client:
                await client.aclose()

    @staticmethod
    def _documents(
        request: SourceRequest, payload: dict, cutoff: datetime
    ) -> list[SourceDocument]:
        documents: list[SourceDocument] = []
        for child in payload.get("data", {}).get("children", []):
            data = child.get("data", {})
            published = datetime.fromtimestamp(float(data.get("created_utc", 0)), UTC)
            if published < cutoff or data.get("over_18"):
                continue
            title = str(data.get("title", "")).strip()
            content = str(data.get("selftext", "")).strip() or title
            permalink = str(data.get("permalink", ""))
            if not title or not permalink:
                continue
            url = f"https://www.reddit.com{permalink}"
            documents.append(
                SourceDocument(
                    source_type=SourceType.REDDIT,
                    source_name=request.source_name,
                    title=title[:500],
                    content=content[:10_000],
                    url=url,
                    author=str(data.get("author", "")) or None,
                    published_at=published,
                    content_hash=sha256(f"{url}\n{content}".encode()).hexdigest(),
                    metadata={
                        "trust_level": "community",
                        "llm_allowed": False,
                        "subreddit": data.get("subreddit"),
                        "score": int(data.get("score", 0)),
                        "comments": int(data.get("num_comments", 0)),
                    },
                )
            )
        return documents
