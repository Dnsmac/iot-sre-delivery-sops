from __future__ import annotations

import json
from pathlib import Path

from engine.models import JobItem


def save_jobs(jobs: list[JobItem], raw_dir: Path, week_id: str) -> Path:
    raw_dir.mkdir(parents=True, exist_ok=True)
    path = raw_dir / f"{week_id}.json"
    path.write_text(
        json.dumps([j.to_dict() for j in jobs], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path


def load_jobs(raw_dir: Path, week_id: str) -> list[JobItem]:
    for name in (f"{week_id}.json", f"{week_id}-liepin.json"):
        path = raw_dir / name
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            return [JobItem(**{**item, "flags": item.get("flags", {})}) for item in data]
    return []
