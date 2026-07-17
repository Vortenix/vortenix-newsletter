from .rss_connector import RSSConnector
class ConnectorRegistry:
    def __init__(self): self._items={"rss":RSSConnector()}
    def get(self,name: str): return self._items[name]
