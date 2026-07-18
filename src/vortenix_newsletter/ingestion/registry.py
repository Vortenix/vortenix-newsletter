from .rss_connector import RSSConnector
from .reddit_connector import RedditConnector
from .api_connectors import CrossrefConnector, FredConnector, GdeltConnector, HackerNewsConnector
class ConnectorRegistry:
    def __init__(self): self._items={"rss":RSSConnector(), "reddit":RedditConnector(), "hacker_news":HackerNewsConnector(), "crossref":CrossrefConnector(), "fred":FredConnector(), "gdelt":GdeltConnector()}
    def get(self,name: str): return self._items[name]
