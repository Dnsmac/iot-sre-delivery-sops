from __future__ import annotations

from datetime import datetime
from pathlib import Path

from engine.models import DirectionScore
from engine.score import pick_actions


def _slug(s: str) -> str:
    return (
        s.replace("·", "-")
        .replace("(", "")
        .replace(")", "")
        .replace("/", "-")
        .replace(" ", "-")[:40]
    )


def render_l1(
    week_id: str,
    top3: list[DirectionScore],
    reject2: list[str],
    diff_line: str,
    prev_top: list[str] | None,
    generated_at: str,
    l2_rel: str,
    demo: bool,
    data_source: str = "",
) -> str:
    warn = "（demo 样本数据）" if demo else ""
    lines = [
        f"# {week_id} 值得考虑（≤5min · {generated_at[:10]}）{warn}",
    ]
    if data_source:
        lines.append(f"> 数据来源：{data_source}")
    lines += [
        "",
        "## ① 本周只看这 3 条",
        "| # | 方向 | 为啥值得看（1句） | 35+/专升本 | 动作 |",
        "|---|------|-------------------|------------|------|",
    ]
    for i, d in enumerate(top3, 1):
        lines.append(
            f"| {i} | {d.direction} | {d.why_one_liner()} | {d.risk_label()} | {pick_actions(d)} |"
        )
    lines += [
        "",
        "## ② 本周别浪费时间（2条）",
    ]
    for r in reject2:
        lines.append(f"- {r}")
    lines += [
        "",
        "## ③ 相对上周（1行）",
        f"- {diff_line}",
        "",
        "## ④ 下周主跟（勾1个）",
        "[ ] 1  [ ] 2  [ ] 3  [ ] 都不跟，主轨IoT",
        "",
        "---",
        f"深挖 → [{l2_rel}]({l2_rel})（可选）",
        "",
    ]
    if prev_top:
        lines.insert(2, f"> 上周 Top：{' · '.join(prev_top)}")
        lines.insert(3, "")
    return "\n".join(lines)


def render_l2_detail(week_id: str, rank: int, d: DirectionScore, profile: dict) -> str:
    lines = [
        f"# {week_id} 详情 #{rank} · {d.direction}",
        "",
        "## 结论（1句）",
        d.why_one_liner() + f"；歧视风险 **{d.risk_label()}**。",
        "",
        "## 数据",
        f"- 样本岗位数：**{d.job_count}**",
        f"- 35+ 字样占比：**{int(d.age_risk_ratio * 100)}%**",
        f"- 统招/一类本字样占比：**{int(d.edu_risk_ratio * 100)}%**",
        f"- 外包字样占比：**{int(d.outsource_ratio * 100)}%**",
        f"- 嵌入式/PLC 字样占比：**{int(d.embedded_ratio * 100)}%**",
    ]
    if d.salary_median_k:
        lines.append(f"- 薪资中位（粗）：**约 {d.salary_median_k:.0f}K**")
    lines += [
        "",
        "## 与你画像",
        f"- {profile.get('birth_year')} 出生 · **{profile.get('education')}** · Java {profile.get('years_java')}y · IoT {profile.get('years_iot')}y",
        f"- 目标：**{profile.get('target_city')} {profile.get('target_salary_k')}** · 主轨 {profile.get('main_track')}",
    ]
    if d.edu_risk_ratio >= 0.4:
        lines.append("- **硬伤提示**：学历字样过滤偏多，投递前确认 JD 是否接受专升本")
    if "比亚迪" in d.direction:
        lines.append("- **BYD**：优先 **Java+IoT 平台/设备对接**；带嵌入式/PLC 主责的岗默认低优先")
    lines += ["", "## 样本 JD Top 5", ""]
    if not d.sample_jobs:
        lines.append("（本周无样本，请编辑 inbox/YYYY-W__.txt 粘贴 JD）")
    else:
        for j in d.sample_jobs:
            flags = []
            if j.flags.get("age_35_limit"):
                flags.append("35+")
            if j.flags.get("zhuanke_risk"):
                flags.append("统招")
            if j.flags.get("embedded_hint"):
                flags.append("嵌入式")
            flag_s = f" [{','.join(flags)}]" if flags else ""
            link = j.url if j.url.startswith("http") else ""
            title = j.title
            if link:
                title = f"[{j.title}]({link})"
            lines.append(f"- {title} · {j.salary_text} · {j.company}{flag_s}")
    if d.notes:
        lines += ["", "## 备注", d.notes]
    return "\n".join(lines) + "\n"


def render_l2_index(week_id: str, top3: list[DirectionScore]) -> str:
    lines = [f"# {week_id} 详情索引（可选阅读）", ""]
    for i, d in enumerate(top3, 1):
        slug = f"{i:02d}-{_slug(d.direction)}.md"
        lines.append(f"- [{d.direction}](./{slug})")
    lines.append("")
    lines.append("> 默认只看 [`../方向/{}.md`](../方向/{}.md)".format(week_id, week_id))
    return "\n".join(lines) + "\n"


def write_outputs(
    repo_root: Path,
    week_id: str,
    top3: list[DirectionScore],
    reject2: list[str],
    diff_line: str,
    prev_top: list[str] | None,
    profile: dict,
    demo: bool,
    cfg_output: dict,
    data_source: str = "",
) -> tuple[Path, Path]:
    l1_dir = repo_root / cfg_output["l1_dir"]
    l2_week = repo_root / cfg_output["l2_dir"] / week_id
    l1_dir.mkdir(parents=True, exist_ok=True)
    l2_week.mkdir(parents=True, exist_ok=True)

    generated_at = datetime.now().isoformat(timespec="seconds")
    l2_rel = f"../详情/{week_id}/README.md"
    l1_path = l1_dir / f"{week_id}.md"
    l1_path.write_text(
        render_l1(week_id, top3, reject2, diff_line, prev_top, generated_at, l2_rel, demo, data_source),
        encoding="utf-8",
    )

    (l2_week / "README.md").write_text(render_l2_index(week_id, top3), encoding="utf-8")
    for i, d in enumerate(top3, 1):
        slug = f"{i:02d}-{_slug(d.direction)}.md"
        (l2_week / slug).write_text(render_l2_detail(week_id, i, d, profile), encoding="utf-8")

    return l1_path, l2_week


def diff_line(current: list[DirectionScore], prev_names: list[str] | None) -> str:
    if not prev_names:
        return "（首周，无对比）"
    cur = [d.direction for d in current[:3]]
    up = [c for c in cur if c not in prev_names]
    down = [p for p in prev_names if p not in cur]
    parts = []
    if up:
        parts.append("↑ " + " · ".join(up[:2]))
    if down:
        parts.append("↓ " + " · ".join(down[:2]))
    return "  ".join(parts) if parts else "Top3 与上周相同"
