#!/usr/bin/env python3
"""职业方向雷达 — 采集 + 生成 L1/L2。

用法:
  pip install -r requirements.txt
  playwright install chromium
  copy config.example.yaml config.yaml

  python run.py --login liepin          # 首次登录
  python run.py --week 2026-W22         # 采集 + 生成
  python run.py --week 2026-W22 --demo  # 样本数据（无需登录）
  python run.py --week 2026-W22 --render-only
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from collectors.liepin import collect_liepin, load_raw, login_liepin, save_raw
from engine.models import JobItem
from engine.render import diff_line, write_outputs
from engine.score import build_reject_lines, flag_job, score_directions


def iso_week(d: date | None = None) -> str:
    d = d or date.today()
    y, w, _ = d.isocalendar()
    return f"{y}-W{w:02d}"


def load_config(path: Path) -> dict:
    if not path.exists():
        example = ROOT / "config.example.yaml"
        if example.exists():
            print(f"未找到 {path.name}，使用 config.example.yaml")
            return yaml.safe_load(example.read_text(encoding="utf-8"))
        print(f"缺少 {path}，请复制 config.example.yaml → config.yaml")
        sys.exit(1)
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def repo_root_from_config(cfg: dict) -> Path:
    return (ROOT / cfg["output"]["repo_root"]).resolve()


def load_demo_jobs() -> list[JobItem]:
    data = json.loads((ROOT / "fixtures" / "demo_jobs.json").read_text(encoding="utf-8"))
    return [JobItem(**{**item, "flags": item.get("flags", {})}) for item in data]


def prev_week_top(l1_dir: Path, week_id: str) -> list[str] | None:
    m = re.match(r"(\d{4})-W(\d{2})", week_id)
    if not m:
        return None
    y, w = int(m.group(1)), int(m.group(2))
    prev_w = w - 1
    prev_y = y
    if prev_w < 1:
        prev_y -= 1
        prev_w = 52
    prev_id = f"{prev_y}-W{prev_w:02d}"
    prev_file = l1_dir / f"{prev_id}.md"
    if not prev_file.exists():
        return None
    names = []
    for line in prev_file.read_text(encoding="utf-8").splitlines():
        if line.startswith("|") and not line.startswith("| #") and "---" not in line:
            cols = [c.strip() for c in line.split("|") if c.strip()]
            if len(cols) >= 2 and cols[0].isdigit():
                names.append(cols[1])
    return names or None


def run_pipeline(cfg: dict, week_id: str, demo: bool, render_only: bool) -> None:
    rules = cfg.get("rules", {})
    searches = cfg.get("searches", [])
    out = cfg["output"]
    repo = repo_root_from_config(cfg)
    raw_dir = ROOT / out.get("raw_dir", "out/raw")
    l1_dir = repo / out["l1_dir"]

    if render_only:
        jobs = load_raw(raw_dir, week_id)
    elif demo:
        jobs = load_demo_jobs()
        save_raw(jobs, raw_dir, week_id)
    else:
        jobs = collect_liepin(cfg)
        save_raw(jobs, raw_dir, week_id)

    for i, j in enumerate(jobs):
        jobs[i] = flag_job(j, rules)

    scores = score_directions(jobs, searches)
    top3 = scores[:3]
    while len(top3) < 3:
        from engine.models import DirectionScore

        top3.append(
            DirectionScore(
                search_id="none",
                direction="（该方向本周无样本）",
                job_count=0,
                age_risk_ratio=0.0,
                edu_risk_ratio=0.0,
                outsource_ratio=0.0,
                embedded_ratio=0.0,
                salary_median_k=None,
                consider_score=-999.0,
            )
        )

    reject2 = build_reject_lines(scores, rules)
    prev_names = prev_week_top(l1_dir, week_id)
    diff = diff_line(top3, prev_names)

    l1_path, l2_dir = write_outputs(
        repo_root=repo,
        week_id=week_id,
        top3=top3,
        reject2=reject2,
        diff_line=diff,
        prev_top=prev_names,
        profile=cfg.get("profile", {}),
        demo=demo,
        cfg_output=out,
    )
    print(f"L1 → {l1_path}")
    print(f"L2 → {l2_dir}")
    print("完成。默认只读 L1（≤5min）。")


def main() -> None:
    parser = argparse.ArgumentParser(description="职业方向雷达")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--week", default=None, help="ISO 周，如 2026-W22")
    parser.add_argument("--login", choices=["liepin"], help="首次登录猎聘")
    parser.add_argument("--demo", action="store_true", help="使用 fixtures 样本")
    parser.add_argument("--render-only", action="store_true", help="仅从 raw 重新渲染")
    args = parser.parse_args()

    cfg_path = ROOT / args.config
    cfg = load_config(cfg_path)
    week_id = args.week or iso_week()

    if args.login == "liepin":
        login_liepin(cfg)
        return

    run_pipeline(cfg, week_id, demo=args.demo, render_only=args.render_only)


if __name__ == "__main__":
    main()
