---
description: 对本次改动做 Code Review（缺陷/回归/安全/缺测优先）；BSP/BUC 编码后自动调用
---

**触发 `/code-review` 时：**

1. **Read** `~/.cursor/skills/code-review/SKILL.md`（全文）
2. 审查范围默认：**本会话 BSP/BUC 刚改动的文件**；未指明时用 `git diff`（uncommitted + 当前分支相对 merge-base）

**回复第一行必须是：** `[Code Review] 已 Read code-review skill，只读审查。`

**硬性要求：**

- **Findings 优先**：按严重级别排序（P0 阻塞 / P1 高 / P2 中 / P3 低）
- **默认不改代码**（除非用户同条写 `直接修 review 问题`）
- 须对照 **hotfix 影响面**、**parity 表** 与 **G0-5 高并发** 检查衍生问题
- 输出末尾给 **Verdict**：`通过` / `需回到 BSP`（列出须修复项）

**轮次限制（v2）：**

- **同一 commit 范围**手动 `/code-review` **最多 1 次**
- **BUC Phase B 已完成且 Verdict 通过** → 不必再调；新发现走 **Review 衍生 #n+1**
- L0 含 **`Review 衍生 #n`** → **衍生轮模式**：仅查 Phase C 表格项 + D1–D8，**不**新增 P1

**BUC 链内调用时：**

- P0/P1 或行为回归 → Verdict = **`需回到 BSP`**，附「Review 衍生 #n」（**一批修完**）
- 仅 P2/P3 → Verdict = **`通过（含建议）`**，不阻断 T7
---

审查范围（选填，默认本会话改动）：
