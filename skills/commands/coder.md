---
description: CODER — 深度审查（高并发/业务影响/性能/YAGNI/调用链），只读；可单独跑或 BUC 按需加深
---

**触发 `/coder` 时：**

1. **Read** `~/.cursor/skills/coder/SKILL.md`（**全文**）
2. 用户「我的需求：」= 审查范围（当前 diff / 已编码分支 / 方案级仅 R1+R2）

**回复第一行必须是：** `[CODER] 已 Read coder skill，只读深度审查。`

**与 `/code-review` 区别：**

| 命令 | 深度 | 何时 |
|------|------|------|
| `/code-review` | 标准，快 | 小改、BUC Phase B **默认** |
| **`/coder`** | **五维 R1～R5 表** | 热路径/多模块/合 Gerrit 前加严 |

**只读**：不改业务代码（除非 L0 含 `直接修 review 问题`）。

**单独跑示例：**

```text
/coder
我的需求：审查当前未提交 diff，五维必查
```

**与 BUC 配合：**

| /buc L0 | Phase B |
|---------|---------|
| 默认 | code-review → **命中条件则追加 coder** |
| `coder` | 仅 coder |
| `coder+` | code-review + coder |
| `coder跳过` | 仅 code-review |

**与 BSP 配合：** L0 `仅影响评估` → 只出 R1/R2，**禁止编码**。

---

我的需求：
