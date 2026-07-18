"""Public structured-data connectors used for research discovery."""

from __future__ import annotations

import asyncio
import os
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from urllib.parse import quote_plus

import httpx

from vortenix_newsletter.domain.enums import SourceType
from vortenix_newsletter.domain.exceptions import ConfigurationError
from vortenix_newsletter.domain.models import SourceDocument, SourceRequest


def _metadata(request: SourceRequest, **extra: object) -> dict[str, object]:
    return {
        "trust_level": request.trust_level,
        "llm_allowed": request.llm_allowed,
        "verticals": request.verticals,
        **extra,
    }


def _document(
    request: SourceRequest,
    source_type: SourceType,
    title: str,
    content: str,
    url: str,
    published_at: datetime | None,
    **metadata: object,
) -> SourceDocument:
    return SourceDocument(
        source_type=source_type,
        source_name=request.source_name,
        title=title[:500],
        content=content[:50_000],
        url=url,
        published_at=published_at,
        content_hash=sha256(f"{url}\n{content}".encode()).hexdigest(),
        metadata=_metadata(request, **metadata),
    )


async def _get_with_retries(
    client: httpx.AsyncClient, url: str, params: dict[str, object]
) -> httpx.Response:
    for attempt in range(3):
        response = await client.get(url, params=params)
        if response.status_code != 429:
            response.raise_for_status()
            return response
        retry_after = response.headers.get("Retry-After")
        delay = min(15.0, float(retry_after)) if retry_after else float(2 ** (attempt + 1))
        await asyncio.sleep(delay)
    response.raise_for_status()
    return response


class HackerNewsConnector:
    """Collect recent, highly ranked stories from the official Hacker News API."""

    async def fetch(self, request: SourceRequest) -> list[SourceDocument]:
        cutoff = datetime.now(UTC) - timedelta(hours=request.lookback_hours)
        async with httpx.AsyncClient(timeout=15) as client:
            ids = (await client.get("https://hacker-news.firebaseio.com/v0/topstories.json")).json()
            semaphore = asyncio.Semaphore(10)

            async def item(item_id: int) -> dict:
                async with semaphore:
                    response = await client.get(
                        f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json"
                    )
                    response.raise_for_status()
                    return response.json() or {}

            items = await asyncio.gather(*(item(item_id) for item_id in ids[:75]))
        documents = []
        for data in items:
            published = datetime.fromtimestamp(float(data.get("time", 0)), UTC)
            if published < cutoff or data.get("type") != "story" or data.get("dead"):
                continue
            title = str(data.get("title", "")).strip()
            item_id = data.get("id")
            if not title or not item_id:
                continue
            discussion = f"https://news.ycombinator.com/item?id={item_id}"
            content = f"{title}. Hacker News score {data.get('score', 0)} with {data.get('descendants', 0)} comments."
            documents.append(
                _document(
                    request,
                    SourceType.HACKER_NEWS,
                    title,
                    content,
                    discussion,
                    published,
                    score=int(data.get("score", 0)),
                    comments=int(data.get("descendants", 0)),
                    linked_url=data.get("url"),
                )
            )
        return documents


class CrossrefConnector:
    """Collect recent scholarly metadata from Crossref's public REST API."""

    async def fetch(self, request: SourceRequest) -> list[SourceDocument]:
        cutoff = datetime.now(UTC) - timedelta(hours=request.lookback_hours)
        params = {
            "query": request.url,
            "filter": f"from-pub-date:{cutoff.date().isoformat()}",
            "rows": 50,
            "select": "DOI,title,abstract,published,URL,publisher,author,type",
            "mailto": os.getenv("CROSSREF_MAILTO", ""),
        }
        async with httpx.AsyncClient(timeout=20, headers={"User-Agent": "VortenixNewsletter/0.2"}) as client:
            response = await _get_with_retries(client, "https://api.crossref.org/works", params)
            items = response.json().get("message", {}).get("items", [])
        documents = []
        for item in items:
            parts = item.get("published", {}).get("date-parts", [[]])[0]
            try:
                published = datetime(*(parts + [1, 1])[:3], tzinfo=UTC)
            except (TypeError, ValueError):
                published = None
            titles = item.get("title") or []
            url = item.get("URL")
            if not titles or not url:
                continue
            content = str(item.get("abstract") or titles[0])
            documents.append(
                _document(
                    request,
                    SourceType.CROSSREF,
                    str(titles[0]),
                    content,
                    str(url),
                    published,
                    doi=item.get("DOI"),
                    publisher=item.get("publisher"),
                )
            )
        return documents


class FredConnector:
    """Turn recent FRED series observations into cited finance evidence."""

    async def fetch(self, request: SourceRequest) -> list[SourceDocument]:
        api_key = os.getenv("FRED_API_KEY", "").strip()
        if not api_key:
            raise ConfigurationError("FRED requires FRED_API_KEY")
        series_ids = [item.strip() for item in request.url.split(",") if item.strip()]
        documents = []
        async with httpx.AsyncClient(timeout=15) as client:
            for series_id in series_ids:
                response = await client.get(
                    "https://api.stlouisfed.org/fred/series/observations",
                    params={
                        "series_id": series_id,
                        "api_key": api_key,
                        "file_type": "json",
                        "sort_order": "desc",
                        "limit": 2,
                    },
                )
                response.raise_for_status()
                observations = response.json().get("observations", [])
                if not observations:
                    continue
                latest = observations[0]
                previous = observations[1] if len(observations) > 1 else None
                content = f"FRED series {series_id}: latest value {latest.get('value')} on {latest.get('date')}."
                if previous:
                    content += f" Previous value {previous.get('value')} on {previous.get('date')}."
                published = datetime.fromisoformat(latest["date"]).replace(tzinfo=UTC)
                url = f"https://fred.stlouisfed.org/series/{quote_plus(series_id)}"
                documents.append(
                    _document(request, SourceType.FRED, f"FRED update: {series_id}", content, url, published, series_id=series_id)
                )
        return documents


class GdeltConnector:
    """Discover recent global reporting through GDELT while citing original URLs."""

    async def fetch(self, request: SourceRequest) -> list[SourceDocument]:
        params = {
            "query": request.url,
            "mode": "ArtList",
            "format": "json",
            "maxrecords": 50,
            "timespan": f"{request.lookback_hours}h",
            "sort": "DateDesc",
        }
        async with httpx.AsyncClient(timeout=30, headers={"User-Agent": "VortenixNewsletter/0.2"}) as client:
            response = await _get_with_retries(
                client, "https://api.gdeltproject.org/api/v2/doc/doc", params
            )
            articles = response.json().get("articles", [])
        documents = []
        for article in articles:
            title = str(article.get("title", "")).strip()
            url = article.get("url")
            seen = article.get("seendate")
            if not title or not url:
                continue
            try:
                published = datetime.strptime(seen, "%Y%m%dT%H%M%SZ").replace(tzinfo=UTC)
            except (TypeError, ValueError):
                published = None
            content = f"{title}. Published by {article.get('domain', 'an original news source')}."
            documents.append(
                _document(
                    request,
                    SourceType.GDELT,
                    title,
                    content,
                    str(url),
                    published,
                    discovery_provider="GDELT",
                    domain=article.get("domain"),
                    language=article.get("language"),
                )
            )
        return documents
