---
name: code-review
description: >-
  Post-fix code review for BSP/BUC. Prioritize bugs, regressions, call-chain
  redundant IO, high-concurrency impact, security. Read-only by default. Use when
  /code-review invoked or BUC Phase B.
---
# Code Review Skill（BSP/BUC 配套）

**开场声明：** `[Code Review] 已 Read code-review skill，只读审查。`

---

## 范围

- **默认**：本会话 BSP/BUC 改动 + `git diff`（工作区 + 当前分支相对 merge-base）
- **BUC Phase B**：必须对照 Phase A 交付包 / hotfix readme 的「改什么 / 影响面 / parity 表 / 高并发表」
- **衍生轮**（L0 或 Phase C 含 **`Review 衍生 #n`**）：**仅**审查 Phase C 表格中列出的项 + Gate 4.4 D1–D8；**不得**新增未列入表格的 P1
- **禁止**：未授权修改业务代码（L0 含 `直接修 review 问题` 除外）
- **同一 commit 范围**：手动 `/code-review` **最多 1 次**；若 BUC Phase B 已完成且 Verdict 通过，**拒绝**重复全量 Review（提示用 Review 衍生 #n+1）

---

## 输出格式（Findings 优先）

```markdown
[Code Review] 审查完成

### Verdict
`通过` | `通过（含建议）` | `需回到 BSP`

### Findings（按严重级别）

#### P0 — 阻塞
- [文件:行] 问题 … → 建议 …

#### P1 — 高
- …

#### P2 — 中（建议）
- …

#### P3 — 低
- …

### 回归关注点
- …

### 缺测（如有）
- …
```

无 P0/P1 时 Verdict 为 **通过** 或 **通过（含建议）**（存在 P2/P3 时）。

---

## 审查清单（BUG 修复）

### 1. 正确性
- 修复是否对准根因，而非症状？
- 边界：`null`、空列表、级联 ID `@platformId` 后缀
- 字符串比较：`cascadeLogicalDelete` 是 String `"0"`/`"1"`，非 int

### 2. 行为回归（原有业务）
- 修复是否 **只影响目标场景**，未删除/移出/禁用等 **旁路** 仍按原逻辑工作？
- 正常在线/离线设备展示是否仍正确？列表 vs 详情 **状态字段是否同源**（如 `state` vs `cascadeState`）？
- 列表过滤 `deleteFlag` / `getNoCascadeDeleteTerm` 是否误伤？
- **换路径/OpenApi**：成功响应字段、失败异常类型（如 `BusinessException` vs `I18nSupportException`）、`@ApiInvokeStatistics`、无 Auth 日志是否 **parity**
- 对照 Phase A **业务影响表 / G0-6**：是否与现有定时、Buffer、双写、补偿 **叠加或冲突**？

### 2.5 调用链 / 多余操作（BUG 修复常见漏项，**必查**）

> 新代码「复用已有方法」不等于安全：须沿 **调用链** 看副作用与频率，不单看本 diff 行数。

| 查什么 | 怎么判 | 典型严重度 |
|--------|--------|------------|
| **副作用外溢** | 被调方法是否带 **写 DB / 写 Redis / 发 MQ / 注册表同步**？读路径修复是否误触发写？ | 热路径写 → **P0/P1** |
| **重复 IO** | 列表/详情/心跳等高频入口：是否 **多查一层 DB、多打一次 Redis、N+1**？同一请求内相同 key 是否查两次？ | 热路径 → **P1**；冷路径 → P2 |
| **读修写** | 展示层/兜底逻辑（如 `updateXxxOffline`、`reconcile`）是否在 **每次查询** 时写库？与修复前相比写放大是否增加？ | **P0/P1** |
| **可短路未短路** | 是否仅 cascade 设备、仅状态变化、仅 `cascade_logical_delete≠0` 等条件才需执行？无差别全量调用？ | 热路径 → **P1** |
| **批量化缺失** | 循环内单条 `get`/`update` 能否用已有 **批量 / pipeline / 一次 IN 查询**？ | 热路径 → **P1** |
| **缓存语义** | Redis 无 key / 过期后，兜底逻辑是否与 DB 展示 **分叉**（如列表在线、详情离线）？ | **P1** |

**审查动作（Agent 内部，输出 findings 时引用具体方法名）**：
1. 对 diff 中 **每一处** 新增/变更的 **外部方法调用**，向上追 1～2 层：是否写库、是否在热路径、调用频率量级。
2. 对照交付包 **「只改」**：若通过「多调一个已有 Service」引入副作用，须在 findings 写明 **调用链**（`A → B → C`）与 **为何多余或可接受**。
3. iot-server 默认按 **高并发、多实例、Reactive** 评估；无法确认频率时标 **P1 + 未覆盖场景**，不得默认「调用一次无所谓」。

### 3. 并发 / 多实例（iot-server 默认）
- 是否新增热路径 DB 写？（与 §2.5「读修写」交叉核对，**任一条命中即列 finding**）
- 定时任务是否与现有 Supplement/心跳 **叠加**？
- Redis key / TTL / 无 TTL 泄漏？
- 多实例下 cap / 幂等 / 锁顺序是否仍成立？写放大是否 ≈ **N × 单实例**？

### 4. 安全
- 用户输入进 SQL/日志
- 权限注解 / 级联跨平台越权

### 5. 文档与闭环（G0-9）

- `bugfix-readme/hotfix_{BugId}-readme.md` 是否齐：影响面 / 怎么验证 / 验证结果占位 / 后续演进
- 专项 md 是否链到 hotfix
- **全文一致性**：grep 交付包「改什么」中的旧名；readme 根因表 / 改动说明 / 行为变化 / 排查记录 **四段同口径**
- **`application.yml`** 与 readme 配置表、代码默认值 **三角一致**
- **配置分环境**：压测专用 key 是否 **仅** 写在 profile/env，未误改生产默认

---

## 衍生轮模式（v2，Review 衍生 #n）

当 L0 或 BUC Phase C 标明 **`Review 衍生 #n`** 时：

1. **Findings 仅允许**来自 Phase C 表格的行；表格外问题标 **P2 建议**，**不**升 P1、**不**触发「需回到 BSP」
2. 核对每项 **已修 / 未修**；未修 → Verdict **`需回到 BSP`**（同 #n，不新开 #n+1）
3. 全表已修 + D1–D8 过 → Verdict **`通过`**

---

## BUC 专用 Verdict

| 条件 | Verdict |
|------|---------|
| 存在 P0 或 P1（含 **文档与代码/yaml 事实矛盾**、**同一 readme 内前后矛盾**） | **`需回到 BSP`** — 列出须修项，触发 Phase C |
| 仅 P2/P3 | **`通过（含建议）`** — 不阻断 T7（P2 含专项 md 过期时须同轮修 md） |
| 无 findings 且文档落盘表已对齐 | **`通过`** |

---

## 可选：Bugbot 子 agent

改动面大（>5 文件或触热路径）时，可 **额外** 只读调用 `review-bugbot` skill（不替代本 skill 的 Verdict 输出）。**或** 使用 **`/coder`**（五维 R1～R5，见 `~/.cursor/skills/coder/SKILL.md`）。

---

## 与 `/coder` 的关系（加深层）

| 场景 | 用 |
|------|-----|
| 小改、BUC Phase B **默认** | **本 skill** |
| 热路径 / 多模块 / 合 Gerrit 前加严 | **`/coder`** 或 BUC L0 **`coder+`** |
| 无 diff，只要方案五维 | **`/coder`** 或 `/bsp` L0 **`仅影响评估`** |

---

## 禁止

- 因 Review 通过就跳过 T7 功能验收
- Review 中直接改代码（除非用户显式授权）
- 用「看起来没问题」代替按级别列 findings
- **同一 commit 范围**重复全量 Review（BUC Phase B 已通过时；含 **重复 `/coder`**）
- **衍生轮**新增未列入 Phase C 表格的 P1
