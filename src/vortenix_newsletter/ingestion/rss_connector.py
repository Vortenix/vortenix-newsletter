from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from hashlib import sha256
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
import asyncio, feedparser, httpx
from bs4 import BeautifulSoup
from vortenix_newsletter.domain.enums import SourceType
from vortenix_newsletter.domain.models import SourceDocument, SourceRequest

def canonical_url(url: str) -> str:
    p=urlsplit(url); return urlunsplit((p.scheme.lower(),p.netloc.lower(),p.path.rstrip("/") or "/",p.query,""))
def clean_html(value: str) -> str: return " ".join(BeautifulSoup(value,"html.parser").get_text(" ").split())
class RSSConnector:
    """Fetch RSS feeds and produce bounded, cleaned source documents."""

    def __init__(self, client: httpx.AsyncClient|None=None, max_bytes: int=2_000_000): self.client=client; self.max_bytes=max_bytes
    async def _bytes(self,url: str)->bytes:
        if not url.startswith(("http://","https://")): return Path(url).read_bytes()[:self.max_bytes]
        client=self.client or httpx.AsyncClient(timeout=15,headers={"User-Agent":"VortenixNewsletter/0.1"},follow_redirects=True)
        try:
            for attempt in range(3):
                try:
                    response=await client.get(url); response.raise_for_status(); return response.content[:self.max_bytes]
                except httpx.HTTPError:
                    if attempt==2: raise
                    await asyncio.sleep(2**attempt)
        finally:
            if self.client is None: await client.aclose()
        return b""
    async def fetch(self,request: SourceRequest)->list[SourceDocument]:
        parsed=feedparser.parse(await self._bytes(request.url)); cutoff=datetime.now(UTC)-timedelta(hours=request.lookback_hours)
        output=[]
        for entry in parsed.entries:
            try:
                published=parsedate_to_datetime(entry.published).astimezone(UTC) if entry.get("published") else None
                if published and published<cutoff: continue
                url=canonical_url(entry.link); content=clean_html(entry.get("summary",entry.get("description","")))
                if request.retrieve_articles and url.startswith("http"): content=clean_html((await self._bytes(url)).decode(errors="replace"))
                digest=sha256((url+"\n"+content).encode()).hexdigest()
                output.append(SourceDocument(source_type=SourceType.RSS,source_name=request.source_name,title=clean_html(entry.title),content=content[:50_000],url=url,author=entry.get("author"),published_at=published,content_hash=digest))
            except (KeyError,ValueError,TypeError): continue
        return output
