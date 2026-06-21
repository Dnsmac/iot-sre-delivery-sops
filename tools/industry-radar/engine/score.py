from __future__ import annotations

import re
from collections import defaultdict

from engine.models import DirectionScore, JobItem


def _parse_salary_k(text: str) -> float | None:
    if not text:
        return None
    text = text.replace("·", "-").replace("—", "-")
    nums = re.findall(r"(\d+)\s*[kK]", text)
    if not nums:
        return None
    values = [int(n) for n in nums]
    return sum(values) / len(values)


def flag_job(job: JobItem, rules: dict) -> JobItem:
    blob = f"{job.title} {job.raw_tags} {job.company}"
    job.flags = {
        "age_35_limit": any(k in blob for k in rules.get("age_35", [])),
        "zhuanke_risk": any(k in blob for k in rules.get("zhuanke_risk", [])),
        "outsource_hint": any(k in blob for k in rules.get("outsource_hint", [])),
        "embedded_hint": any(k in blob for k in rules.get("embedded_hint", [])),
    }
    return job


def score_directions(jobs: list[JobItem], searches: list[dict]) -> list[DirectionScore]:
    by_id: dict[str, list[JobItem]] = defaultdict(list)
    for j in jobs:
        by_id[j.search_id].append(j)

    results: list[DirectionScore] = []
    for s in searches:
        sid = s["id"]
        group = by_id.get(sid, [])
        n = len(group) or 1
        age_r = sum(1 for j in group if j.flags.get("age_35_limit")) / n
        edu_r = sum(1 for j in group if j.flags.get("zhuanke_risk")) / n
        out_r = sum(1 for j in group if j.flags.get("outsource_hint")) / n
        emb_r = sum(1 for j in group if j.flags.get("embedded_hint")) / n
        salaries = [_parse_salary_k(j.salary_text) for j in group]
        salaries = [x for x in salaries if x is not None]
        med = sorted(salaries)[len(salaries) // 2] if salaries else None

        # 越高越值得「考虑观察」：岗量 + 薪资；减分项：歧视/嵌入式
        consider = len(group) * 2
        if med:
            consider += min(med / 5, 8)
        consider -= age_r * 15 + edu_r * 20 + emb_r * 10 + out_r * 5

        results.append(
            DirectionScore(
                search_id=sid,
                direction=s["direction"],
                job_count=len(group),
                age_risk_ratio=round(age_r, 2),
                edu_risk_ratio=round(edu_r, 2),
                outsource_ratio=round(out_r, 2),
                embedded_ratio=round(emb_r, 2),
                salary_median_k=med,
                consider_score=round(consider, 2),
                notes=s.get("notes", ""),
                sample_jobs=sorted(group, key=lambda x: x.title)[:5],
            )
        )

    results.sort(key=lambda x: x.consider_score, reverse=True)
    return results


def pick_actions(top: DirectionScore) -> str:
    if top.edu_risk_ratio >= 0.5:
        return "只读JD"
    if top.job_count == 0:
        return "观望"
    if "比亚迪" in top.direction:
        return "只读JD"
    return "观察"


def build_reject_lines(scores: list[DirectionScore], rules: dict) -> list[str]:
    lines: list[str] = []
    low = sorted(scores, key=lambda x: x.consider_score)[:2]
    for d in low:
        if d.job_count == 0:
            lines.append(f"{d.direction}：本周无样本，暂不投入")
        elif d.embedded_ratio >= 0.3:
            lines.append(f"{d.direction}：嵌入式/PLC 占比高，与 Java 平台主炮不符")
        elif d.age_risk_ratio >= 0.35:
            lines.append(f"{d.direction}：35+ 字样占比偏高（约 {int(d.age_risk_ratio*100)}%）")
        elif d.edu_risk_ratio >= 0.45:
            lines.append(f"{d.direction}：统招/一类本字样占比高（约 {int(d.edu_risk_ratio*100)}%）")
        else:
            lines.append(f"{d.direction}：综合分偏低，本周仅观察")

    generic = []
    if any(d.age_risk_ratio >= 0.3 for d in scores):
        generic.append("写死「35岁以下」占比较高的纯互联网岗")
    if any(d.edu_risk_ratio >= 0.4 for d in scores):
        generic.append("硬性「统招本科/一类本」且未写大专可议的岗")
    for g in generic[: max(0, 2 - len(lines))]:
        lines.append(g)
    return lines[:2]
