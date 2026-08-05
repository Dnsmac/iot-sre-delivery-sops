<!-- 合并到项目 CLAUDE.md -->

## Agent：BUG 修复请用 BSP / BUC

- **安装**：`iot-sre-delivery-sops/skills/install.ps1`（详见 `skills/INSTALL.md`）
- **版本**：`skills/manifest.yaml`

### Skill 路径（择一）

| 级别 | 路径 |
|------|------|
| 用户级 | `~/.cursor/skills/bsp-orchestrator/SKILL.md` |
| 项目级 | `.cursor/skills/bsp-orchestrator/SKILL.md` |
| 分发包源 | `skills/bsp-orchestrator/SKILL.md` |

BUC 链额外 Read：`buc-orchestrator/SKILL.md`、`code-review/SKILL.md`（Phase B 默认）

### 何时用哪个

| 命令 | 场景 |
|------|------|
| `/bs` | 纯方案讨论，不写码 |
| `/bsp` | BUG 分析 + 编码 + 落盘（不含自动 Review） |
| `/buc` | **合 Gerrit 的 BUG 修复（默认）** — BSP + 自动 Review |
| `/code-review` | 单独 Review 已编码 diff |
| `/coder` | 热路径/多模块时五维加深 |

### 流程摘要（BUC）

1. Read `buc-orchestrator` + `bsp-orchestrator` 全文
2. Phase A：交付包 → **停** → 等 `批准修复`（零确认 L0 除外）
3. 授权后：编码 + hotfix readme + 专项 md
4. Phase B：自动 `code-review`（按需 `coder`）
5. P0/P1 → Review 衍生 #n → 再次 `批准修复`

### 禁止

- 自批自改、未授权改业务代码
- 首轮标题写「已执行」且同轮有 diff
- 只聊天不落盘

### 无快捷键时触发

```text
按 buc-orchestrator 执行，Read SKILL.md 全文 Phase A 起。
我的需求：BUG …
```
