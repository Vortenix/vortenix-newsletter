"""Validate local Markdown links and example YAML without network access."""
from __future__ import annotations
import re
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r"(?<!!)\[[^]]+\]\(([^)]+)\)")

def main() -> None:
    failures: list[str] = []
    for document in ROOT.rglob("*.md"):
        if any(part.startswith(".") and part not in {".github"} for part in document.relative_to(ROOT).parts):
            continue
        text = document.read_text(encoding="utf-8")
        for target in LINK.findall(text):
            clean = target.split("#", 1)[0]
            if not clean or "://" in clean or clean.startswith("mailto:"):
                continue
            if not (document.parent / clean).resolve().exists():
                failures.append(f"{document.relative_to(ROOT)}: missing {target}")
    for example in (ROOT / "examples").glob("*.yaml"):
        yaml.safe_load(example.read_text(encoding="utf-8"))
    if failures:
        raise SystemExit("\n".join(failures))
    print("Documentation links and YAML examples are valid.")

if __name__ == "__main__":
    main()
