"""Remove only known generated development artifacts inside the repository."""
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
for name in (".mypy_cache", ".ruff_cache", ".pytest_cache", "coverage.xml", ".coverage", "dist", "build"):
    target = ROOT / name
    if target.is_dir(): shutil.rmtree(target)
    elif target.is_file(): target.unlink()
print("Known development artifacts removed.")
