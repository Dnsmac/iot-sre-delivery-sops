from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from engine.models import JobItem


def _parse_block(search_id: str | None, lines: list[str], now: str) -> list[JobItem]:
    jobs: list[JobItem] = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # 格式1: 标题 | 公司 | 薪资 | 标签(可选)
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 2:
            title = parts[0]
            company = parts[1] if len(parts) > 1 else ""
            salary = parts[2] if len(parts) > 2 else ""
            tags = parts[3] if len(parts) > 3 else ""
            jobs.append(
                JobItem(
                    title=title,
                    company=company,
                    salary_text=salary,
                    url="",
                    source="inbox",
                    search_id=search_id or "",
                    direction="",
                    scraped_at=now,
                    raw_tags=tags,
                )
            )
    return jobs


def collect_inbox(cfg: dict, week_id: str | None = None) -> list[JobItem]:
    """读取 inbox/ 下 txt/md，无需登录。优先 inbox/{week}.txt 再扫 *.txt。"""
    inbox_cfg = cfg.get("inbox", {})
    inbox_dir = Path(inbox_cfg.get("dir", "inbox"))
    if not inbox_dir.is_absolute():
        inbox_dir = Path(__file__).resolve().parent.parent / inbox_dir
    if not inbox_dir.exists():
        return []

    now = datetime.now(timezone.utc).isoformat()
    files: list[Path] = []
    if week_id:
        for ext in (".txt", ".md"):
            p = inbox_dir / f"{week_id}{ext}"
            if p.exists():
                files.append(p)
    if not files:
        files = sorted(inbox_dir.glob("*.txt")) + sorted(inbox_dir.glob("*.md"))
        files = [f for f in files if f.name.upper() != "README.MD"]

    all_jobs: list[JobItem] = []
    for fp in files:
        text = fp.read_text(encoding="utf-8", errors="ignore")
        current_id: str | None = None
        block: list[str] = []
        for line in text.splitlines():
            m = re.match(r"^\[([a-z0-9_]+)\]\s*$", line.strip(), re.I)
            if m:
                if block:
                    all_jobs.extend(_parse_block(current_id, block, now))
                current_id = m.group(1)
                block = []
            else:
                block.append(line)
        if block:
            all_jobs.extend(_parse_block(current_id, block, now))
    return all_jobs
