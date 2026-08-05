# 职业方向雷达 Phase 1 Implementation Plan

> **Spec:** `docs/superpowers/specs/2026-05-30-career-direction-radar-design.md`

## Tasks

- [x] `tools/industry-radar/` 骨架 + README + requirements + .gitignore
- [x] `config.example.yaml` + `engine/` 模型/打分/渲染
- [x] `collectors/liepin.py` + `--login` + `--demo`
- [x] `run.py` 入口 → 写 L1/L2 + raw
- [x] 更新 `05-Interview-Prep/行业雷达/README.md`
- [x] 联动 PLAN / 每日协作约定 / PROGRESS_LOG / README
- [x] **零登录**：`collectors/inbox.py` + `collectors/public.py` + 默认不启猎聘
- [x] `inbox/README.md` + 示例 `inbox/2026-W22.txt`
- [x] 验收：`py -3 run.py --week 2026-W22`（inbox + 公开页，未登录）
- [ ] 本机（**仅在家**）：`playwright install chromium` + `py -3 run.py --login liepin`（可选）
