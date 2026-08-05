<!-- 合并到仓库根 AGENTS.md 或 CODEX.md / WORKBUDDY 项目说明 -->

## Agent Skills：BS / BSP / BUC 链

> 分发包源：`skills/`（iot-sre-delivery-sops）  
> 安装：`skills/install.ps1` 或 `skills/install.sh`  
> 版本：见 `skills/manifest.yaml`

### 命令一览

| 快捷键 | 用途 | Agent 须 Read |
|--------|------|---------------|
| `/bs` | Superpowers 头脑风暴（不写码） | superpowers brainstorming（若有） |
| `/bsp` | BUG 分析 → 批准 → 编码 → 落盘 | `bsp-orchestrator/SKILL.md` **全文** |
| `/buc` | BSP + 自动 Code Review + 有问题回 BSP | `buc-orchestrator` + `bsp-orchestrator` **全文** |
| `/code-review` | 标准只读 Review | `code-review/SKILL.md` |
| `/coder` | 五维深度 Review | `coder/SKILL.md` |

**Skill 路径**（按安装方式择一）：

- 用户级：`~/.cursor/skills/<id>/SKILL.md`
- 项目级：`.cursor/skills/<id>/SKILL.md`
- 分发包源：`<repo>/skills/<id>/SKILL.md`

### 触发规则

**`/bsp` 或用户说「按 BSP / bsp-orchestrator」：**

1. Read `bsp-orchestrator/SKILL.md` 全文
2. 回复第一行：`[BSP] 已 Read bsp-orchestrator，Gate 0 起执行。`
3. 交付包 → **停** → 等用户 `批准修复`（L0 含 `直接修`/`零确认` 除外）
4. 硬约束：禁止自批；G0-9 文档闭环；高并发默认多实例

**`/buc` 或用户说「按 BUC / buc-orchestrator」：**

1. Read `buc-orchestrator/SKILL.md` + `bsp-orchestrator/SKILL.md` 全文
2. 回复第一行：`[BUC] 已 Read buc-orchestrator，Phase A（BSP）起执行。`
3. Phase A = 完整 BSP；编码后 **自动 Phase B** Code Review
4. P0/P1 → Review 衍生交付包 → 再次 `批准修复`（最多 3 轮代码修复）

**无 `/bsp` 快捷键时**（Codex / Workbuddy / 纯 CLI Agent），用户开场白：

```text
按 buc-orchestrator 执行。Read .cursor/skills/buc-orchestrator/SKILL.md 和 bsp-orchestrator/SKILL.md 全文。
我的需求：BUG 37xxx …
```

或仅分析不修：

```text
按 bsp-orchestrator 执行，Read SKILL.md 全文 Gate 0 起。只出交付包，不要改代码。
我的需求：BUG …
```

### 文档落盘

- 业务仓 `bugfix-readme/hotfix_{BugId}-readme.md`（主）
- `docs/cascade/级联BUG排查-*.md`（归档）
- 模板：`skills/templates/BUG排查专项模板.md`

### 安装（新 Agent 环境同步）

```powershell
# Windows — 用户级（推荐）
cd <path-to>/iot-sre-delivery-sops/skills
.\install.ps1

# 覆盖更新
.\install.ps1 -Force

# 同时装到业务仓库（可进 git，团队共享）
.\install.ps1 -ProjectRoot "D:\gerrit\iot-server"
```

```bash
# macOS / Linux
cd /path/to/iot-sre-delivery-sops/skills
chmod +x install.sh && ./install.sh
./install.sh --force
./install.sh --project /path/to/iot-server
```

安装后重启 IDE 或新开 Agent 会话。验证：

```powershell
Test-Path "$env:USERPROFILE\.cursor\skills\bsp-orchestrator\SKILL.md"
Test-Path "$env:USERPROFILE\.cursor\skills\buc-orchestrator\SKILL.md"
Test-Path "$env:USERPROFILE\.cursor\commands\buc.md"
```
