from pathlib import Path
import yaml
from vortenix_newsletter.domain.exceptions import ConfigurationError
from vortenix_newsletter.domain.models import Audience, Subscriber
from .models import AppConfig, SourceConfig, VerticalConfig

class ConfigBundle:
    def __init__(self, root: Path):
        self.root=root
        self.application=AppConfig.model_validate(_load(root/"application.yaml"))
        self.sources=[SourceConfig.model_validate(x) for x in _load(root/"sources.yaml").get("sources",[])]
        self.audiences=[Audience.model_validate(x) for x in _load(root/"audiences.yaml").get("audiences",[])]
        subscriber_data = _load_optional(root / "subscribers.local.yaml")
        self.subscribers = [
            Subscriber.model_validate(item)
            for item in subscriber_data.get("subscribers", [])
        ]
        self.verticals=[VerticalConfig.model_validate(_load(p)) for p in sorted((root/"verticals").glob("*.yaml"))]
        self._validate_subscribers()

    def _validate_subscribers(self) -> None:
        audience_ids = {audience.id for audience in self.audiences}
        vertical_ids = {vertical.id for vertical in self.verticals if vertical.enabled}
        seen: set[str] = set()
        for subscriber in self.subscribers:
            if subscriber.id in seen:
                raise ConfigurationError(f"Duplicate subscriber ID: {subscriber.id}")
            seen.add(subscriber.id)
            if subscriber.audience_id not in audience_ids:
                raise ConfigurationError(
                    f"Subscriber {subscriber.id} references unknown audience {subscriber.audience_id}"
                )
            unknown = set(subscriber.enabled_verticals) - vertical_ids
            if unknown:
                names = ", ".join(sorted(unknown))
                raise ConfigurationError(
                    f"Subscriber {subscriber.id} references unknown verticals: {names}"
                )
    def audience(self, ident: str) -> Audience:
        try: return next(x for x in self.audiences if x.id==ident and x.enabled)
        except StopIteration as exc: raise ConfigurationError(f"Unknown or disabled audience: {ident}") from exc
    def subscriber(self, ident: str) -> Subscriber:
        try:
            return next(x for x in self.subscribers if x.id == ident and x.enabled)
        except StopIteration as exc:
            raise ConfigurationError(f"Unknown or disabled subscriber: {ident}") from exc

    def subscribers_for(self, audience_id: str) -> list[Subscriber]:
        return [
            subscriber
            for subscriber in self.subscribers
            if subscriber.audience_id == audience_id and subscriber.enabled
        ]
def _load(path: Path) -> dict:
    try: return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError,yaml.YAMLError) as exc: raise ConfigurationError(f"Invalid configuration {path}: {exc}") from exc

def _load_optional(path: Path) -> dict:
    if not path.exists():
        return {}
    return _load(path)
def load_config(root: Path=Path("config")) -> ConfigBundle: return ConfigBundle(root)
