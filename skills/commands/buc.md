---
description: BUC — BSP 修复闭环 + 自动 Code Review；有问题回到 BSP 再修
---

**触发 `/buc` 时只做一件事：**

1. **Read** `~/.cursor/skills/buc-orchestrator/SKILL.md`（**全文**）
2. **Read** `~/.cursor/skills/bsp-orchestrator/SKILL.md`（Phase A 执行 BSP）
3. 用户在本命令后的「我的需求：」即本次 **L0**（须含 BUG 现象；可选 BugId）

**回复第一行必须是：** `[BUC] 已 Read buc-orchestrator，Phase A（BSP）起执行。`

**与 `/bsp` 的区别：**

| 命令 | 范围 | 何时用 |
|------|------|--------|
| `/bsp` | 分析 → 批准 → 编码 → 落盘 → **停**（等 T7） | 纯分析、方案、台账 |
| `/buc` | 同上 + **编码后自动 Phase B Code Review** → 有问题 **回到 BSP 交付包** 再修 | **合 Gerrit 的 BUG 修复（默认）** |

**Phase B 文档硬规则（BUG 合入）：**

| 情况 | 级别 |
|------|------|
| hotfix readme 与 `application.yml` / 实现 **配置项、TTL、行为** 不一致 | **P1** → Phase C |
| 同一 readme 内前后矛盾（如根因表 vs 改动说明口径不同） | **P1** |
| mermaid / §变更 仍引用已删除符号，但 hotfix 正文已正确 | **P2**（须同轮修专项 md） |

**Phase C Review 衍生（v2）：**

- P0/P1 → **表格列全项**，**一次** `批准修复` **批完**（代码+文档同批）
- 衍生轮 Phase B **仅核对表格 + D1–D8**，不挖新 P1
- 文档-only 轮 **不占** 代码 3 轮上限

**Phase D 前置条件：** 文档落盘表 **全部「已对齐」**（无「待对齐」）方可输出「修复+Review 完成」。

**HARD-GATE：** 未 **`批准修复`**（或 L0 **零确认**）→ **禁止**改业务代码；**具体改法、打 `/buc` 均不算批准**。

**反模式（违规 = Agent 错误，须 revert 或等用户批）：**

| 禁止 | 正确 |
|------|------|
| 标题 **「交付包（已执行）」** 且同轮有 diff | 标题 **「交付包（待批准）」** → **停** |
| `/buc 把 X 改成 Y` 后首轮就编码 | 首轮只交付包 → 下一条 **`批准修复`** |
| 「您已指定改法故默认批准」 | **无效**；须原文引用用户 **`批准修复`** |

**授权（继承 BSP 三分法 v3）：**

| 口令 | Phase A 允许 |
|------|----------------|
| **`授权查询`** | 只读 ES/DB 诊断 + T-ES 清单，**立即执行** |
| **`批准运维`** | ES 重建/reindex（须先备份 SOP） |
| **`批准修复`** / L0 **`零确认`** | 改业务代码 + 落盘 |
| **`批准改流程文档`** | 仅改 `~/.cursor/skills` / `commands` |

- Phase A 未收到 **`批准修复`**（或 L0 **零确认** 代码）→ **禁止**改业务代码
- **`批准运维`** ≠ **`批准修复`**；运维不得顺带改 Java
- Phase B Code Review → **只读**，不改代码
- Phase C 若 Review 发现 P0/P1 → 输出 **Review 衍生 #n 交付包（一批修完）** → **停** → 等 **`批准修复`** 再进入下一轮

**根因版本（同一会话）**：推翻旧结论须写 **作废 #n → 当前 #n+1**；ES 类须附 **T-ES3 term** 实测数字，禁止与 alias/物模型单因子混为一谈。

**L0 可选加速：**

- 同条含 `直接修` / `零确认` → Phase A 首轮即可编码（仍执行 Phase B Review）
- 同条含 **`Review 衍生 #n`** → 跳过全新交付包，按 #n 表格续修
- 同条含 **`不分段`** → 覆盖 Gate 3 自动升分段建议（须说明理由）
- 同条含 **`coder`** / **`coder+`** / **`coder跳过`** → 见 Phase B 深度表（`~/.cursor/commands/coder.md`）

**禁止（v2）：** BUC Phase B 已通过后再对 **同一 commit** 手动 `/code-review` 或 **`/coder`**；新发现须 **Review 衍生 #n+1**。

**Phase B 深度（`/coder`，按需 — 非默认一律加深）：**

| /buc L0 | Phase B 行为 |
|---------|----------------|
| **默认** | 先 **`code-review`**；命中 **加深条件** → **同会话追加** **`/coder`** |
| `coder` | 仅 **`/coder`**（跳过标准，小 diff） |
| `coder+` | **`code-review` + `coder`**（大改推荐） |
| `coder跳过` | 仅 `code-review` |

**自动加深条件**（默认开）：>3 文件 / 跨 2+ Maven 模块 / 热路径 / 新增 DB·Redis 写·定时 → 标准 Review **通过后**跑 `coder`。

**编码：** 只认 `bsp-orchestrator` **编码硬门禁 6 条**（Phase B 先查 #3 删写、#4 范围、#6 未覆盖）。

---

我的需求：