from pathlib import Path
import yaml
from vortenix_newsletter.domain.exceptions import ConfigurationError
from vortenix_newsletter.domain.models import Audience
from .models import AppConfig, SourceConfig, VerticalConfig

class ConfigBundle:
    def __init__(self, root: Path):
        self.root=root
        self.application=AppConfig.model_validate(_load(root/"application.yaml"))
        self.sources=[SourceConfig.model_validate(x) for x in _load(root/"sources.yaml").get("sources",[])]
        self.audiences=[Audience.model_validate(x) for x in _load(root/"audiences.yaml").get("audiences",[])]
        self.verticals=[VerticalConfig.model_validate(_load(p)) for p in sorted((root/"verticals").glob("*.yaml"))]
    def audience(self, ident: str) -> Audience:
        try: return next(x for x in self.audiences if x.id==ident and x.enabled)
        except StopIteration as exc: raise ConfigurationError(f"Unknown or disabled audience: {ident}") from exc
def _load(path: Path) -> dict:
    try: return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError,yaml.YAMLError) as exc: raise ConfigurationError(f"Invalid configuration {path}: {exc}") from exc
def load_config(root: Path=Path("config")) -> ConfigBundle: return ConfigBundle(root)
