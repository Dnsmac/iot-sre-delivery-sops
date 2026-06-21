from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class JobItem:
    title: str
    company: str
    salary_text: str
    url: str
    source: str
    search_id: str
    direction: str
    scraped_at: str
    flags: dict[str, bool] = field(default_factory=dict)
    raw_tags: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DirectionScore:
    search_id: str
    direction: str
    job_count: int
    age_risk_ratio: float
    edu_risk_ratio: float
    outsource_ratio: float
    embedded_ratio: float
    salary_median_k: float | None
    consider_score: float
    notes: str = ""
    sample_jobs: list[JobItem] = field(default_factory=list)

    def risk_label(self) -> str:
        if self.edu_risk_ratio >= 0.5 or self.age_risk_ratio >= 0.4:
            return "高"
        if self.edu_risk_ratio >= 0.25 or self.age_risk_ratio >= 0.2:
            return "中"
        return "低"

    def why_one_liner(self) -> str:
        parts = [f"本周{self.job_count}条"]
        if self.salary_median_k:
            parts.append(f"薪资中位约{self.salary_median_k:.0f}K")
        if "比亚迪" in self.direction:
            parts.append("锚点雇主需筛平台向")
        elif "IoT" in self.direction or "物联网" in self.direction:
            parts.append("贴现职栈")
        return "、".join(parts[:3])
