from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

from engine.models import JobItem

ROOT = Path(__file__).resolve().parent.parent


def _fetch_html(url: str, timeout: int = 15) -> str:
    req = Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; industry-radar/1.0)"})
    with urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def _strip_tags(html: str) -> str:
    text = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.I)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text)


def _extract_jobs_from_text(text: str, source: str, search_id: str, direction: str, now: str) -> list[JobItem]:
    """从公开页纯文本粗提取含 Java/物联网/比亚迪 的短句。"""
    jobs: list[JobItem] = []
    keywords = ("java", "Java", "物联网", "IoT", "车联网", "比亚迪", "BYD", "工业软件", "交付")
    for chunk in re.split(r"[。\n；;]", text):
        chunk = chunk.strip()
        if len(chunk) < 8 or len(chunk) > 120:
            continue
        if not any(k in chunk for k in keywords):
            continue
        salary_m = re.search(r"(\d+\s*[-~～]\s*\d+\s*[kK万])", chunk)
        jobs.append(
            JobItem(
                title=chunk[:80],
                company="（公开页提取）",
                salary_text=salary_m.group(1) if salary_m else "",
                url="",
                source=source,
                search_id=search_id,
                direction=direction,
                scraped_at=now,
                raw_tags="public",
            )
        )
        if len(jobs) >= 15:
            break
    return jobs


def _load_fallback() -> list[dict]:
    path = ROOT / "fixtures" / "public_fallback.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return []


def collect_public(cfg: dict) -> list[JobItem]:
    """抓取公开 URL（无需登录）；失败则用 fixtures 并标注。"""
    pub = cfg.get("public", {})
    if not pub.get("enabled", True):
        return []

    now = datetime.now(timezone.utc).isoformat()
    jobs: list[JobItem] = []
    errors: list[str] = []

    for src in pub.get("sources", []):
        url = src.get("url", "")
        sid = src.get("search_id", "unassigned")
        direction = src.get("direction", src.get("name", ""))
        try:
            html = _fetch_html(url, timeout=pub.get("timeout_sec", 15))
            text = _strip_tags(html)
            extracted = _extract_jobs_from_text(text, f"public:{src.get('id', 'web')}", sid, direction, now)
            jobs.extend(extracted)
        except Exception as ex:
            errors.append(f"{src.get('id')}: {ex}")

    if not jobs:
        for item in _load_fallback():
            jobs.append(
                JobItem(
                    title=item["title"],
                    company=item.get("company", ""),
                    salary_text=item.get("salary_text", ""),
                    url=item.get("url", ""),
                    source="public:fallback",
                    search_id=item.get("search_id", "unassigned"),
                    direction=item.get("direction", ""),
                    scraped_at=now,
                    raw_tags=item.get("raw_tags", "offline-fallback"),
                )
            )
        if errors:
            print("[info] 公开页抓取失败，已用 fixtures/public_fallback.json（可改 inbox 粘贴真实 JD）")
            for e in errors:
                print(f"  - {e}")
    return jobs
