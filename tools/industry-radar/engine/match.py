from __future__ import annotations

from engine.models import JobItem


def assign_search(job: JobItem, searches: list[dict]) -> JobItem:
    """按 config 关键词把 inbox/公开页岗位归到方向。"""
    if job.search_id and job.search_id not in ("", "unassigned"):
        for s in searches:
            if s["id"] == job.search_id:
                job.direction = s["direction"]
                return job

    blob = f"{job.title} {job.company} {job.raw_tags}".lower()
    best_id = "unassigned"
    best_dir = "未分类·待手动指定"
    best_score = 0

    for s in searches:
        score = 0
        for kw in s.get("match_keywords", []):
            if kw.lower() in blob:
                score += 2
        lp = s.get("liepin") or {}
        if lp.get("keyword"):
            for part in lp["keyword"].replace("，", " ").split():
                if len(part) >= 2 and part.lower() in blob:
                    score += 1
        if "比亚迪" in s.get("direction", "") and ("比亚迪" in blob or "byd" in blob):
            score += 3
        filt = s.get("filter_out", {})
        if any(x in job.title for x in filt.get("title_contains", [])):
            score -= 5
        if score > best_score:
            best_score = score
            best_id = s["id"]
            best_dir = s["direction"]

    if best_score > 0:
        job.search_id = best_id
        job.direction = best_dir
    else:
        job.search_id = "unassigned"
        job.direction = best_dir
    return job
