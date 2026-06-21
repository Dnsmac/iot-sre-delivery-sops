from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

from engine.models import JobItem


def _playwright():
    from playwright.sync_api import sync_playwright

    return sync_playwright


def login_liepin(config: dict) -> None:
    sync_playwright = _playwright()
    browser_cfg = config["browser"]
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=browser_cfg["user_data_dir"],
            headless=False,
            slow_mo=browser_cfg.get("slow_mo_ms", 0),
        )
        page = ctx.new_page()
        page.goto(config["liepin"]["base_url"], wait_until="domcontentloaded")
        print("请在浏览器中登录猎聘，完成后关闭浏览器窗口。")
        try:
            page.wait_for_event("close", timeout=0)
        except Exception:
            pass
        ctx.close()


def _extract_cards(page, selectors: dict) -> list[dict]:
    cards = page.locator(selectors.get("job_card", ".job-card-pc"))
    count = cards.count()
    items: list[dict] = []
    for i in range(min(count, 40)):
        card = cards.nth(i)
        try:
            title = _safe_text(card, selectors.get("title", "")) or _safe_text(card, "a")
            salary = _safe_text(card, selectors.get("salary", ""))
            company = _safe_text(card, selectors.get("company", ""))
            href = card.locator("a").first.get_attribute("href") or ""
            tags = _safe_text(card, selectors.get("tags", ""))
            if title:
                items.append(
                    {
                        "title": title.strip(),
                        "salary_text": (salary or "").strip(),
                        "company": (company or "").strip(),
                        "url": href,
                        "raw_tags": (tags or "").strip(),
                    }
                )
        except Exception:
            continue
    return items


def _safe_text(root, selector: str) -> str:
    if not selector:
        return ""
    loc = root.locator(selector).first
    if loc.count() == 0:
        return ""
    return loc.inner_text(timeout=2000)


def collect_liepin(config: dict) -> list[JobItem]:
    sync_playwright = _playwright()
    browser_cfg = config["browser"]
    liepin_cfg = config["liepin"]
    selectors = liepin_cfg.get("selectors", {})
    now = datetime.now(timezone.utc).isoformat()
    all_jobs: list[JobItem] = []

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=browser_cfg["user_data_dir"],
            headless=browser_cfg.get("headless", False),
            slow_mo=browser_cfg.get("slow_mo_ms", 0),
        )
        page = ctx.new_page()
        page.set_default_timeout(browser_cfg.get("page_timeout_ms", 30000))

        for search in config.get("searches", []):
            lp = search.get("liepin")
            if not lp:
                continue
            keyword = lp["keyword"]
            pages = int(lp.get("pages", 1))
            url = f"{liepin_cfg['base_url']}{liepin_cfg.get('search_path', '/zhaopin/')}?key={quote(keyword)}&city=050090"
            for pn in range(pages):
                page_url = url if pn == 0 else f"{url}&curPage={pn}"
                try:
                    page.goto(page_url, wait_until="domcontentloaded")
                    page.wait_for_timeout(2000)
                    cards = _extract_cards(page, selectors)
                except Exception as ex:
                    print(f"[warn] 猎聘采集失败 {search['id']}: {ex}")
                    cards = []

                for c in cards:
                    title = c["title"]
                    filt = search.get("filter_out", {})
                    if any(x in title for x in filt.get("title_contains", [])):
                        continue
                    all_jobs.append(
                        JobItem(
                            title=title,
                            company=c.get("company", ""),
                            salary_text=c.get("salary_text", ""),
                            url=c.get("url", ""),
                            source="liepin",
                            search_id=search["id"],
                            direction=search["direction"],
                            scraped_at=now,
                            raw_tags=c.get("raw_tags", ""),
                        )
                    )
                time.sleep(2)
        ctx.close()
    return all_jobs


def save_raw(jobs: list[JobItem], raw_dir: Path, week_id: str) -> Path:
    raw_dir.mkdir(parents=True, exist_ok=True)
    path = raw_dir / f"{week_id}-liepin.json"
    path.write_text(
        json.dumps([j.to_dict() for j in jobs], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path


def load_raw(raw_dir: Path, week_id: str) -> list[JobItem]:
    path = raw_dir / f"{week_id}-liepin.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return [JobItem(**{**item, "flags": item.get("flags", {})}) for item in data]
