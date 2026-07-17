from vortenix_newsletter.config.models import VerticalConfig
from .generic import GenericVertical
class VerticalRegistry:
    def __init__(self,configs: list[VerticalConfig]): self._items={c.id:GenericVertical(c) for c in configs if c.enabled}
    def get(self,ident: str): return self._items[ident]
    def ids(self): return list(self._items)
