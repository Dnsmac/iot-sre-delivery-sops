# BS / BSP / BUC Skills 分发包

> **用途**：给同事 / Codex / Workbuddy 一键安装 **BUG 修复编排 + Review 闭环**。  
> **快捷键**：`/bs` · `/bsp` · `/buc` · `/code-review` · `/coder`  
> **版本**：见 [`manifest.yaml`](manifest.yaml)

---

## 5 分钟上手

1. **安装**（Windows）

   ```powershell
   cd D:\demo\iot-sre-delivery-sops\skills
   .\install.ps1
   ```

2. **重启 Cursor**（或新开 Agent 会话）

3. **合 Gerrit 的 BUG**（推荐）：

   ```text
   /buc

   我的需求：
   BUG 37xxx，（截图/现象）
   验收：…
   ```

4. 看 **交付包** → 回复 **`批准修复`** → Agent 编码 + Review 闭环

详细说明：[`QUICKSTART.md`](QUICKSTART.md) · 安装细节：[`INSTALL.md`](INSTALL.md)

---

## 命令链

```text
/bs          → Superpowers 头脑风暴（仅方案，不写码）
/bsp         → 分析 → 批准 → 编码 → 落盘 → 停
/buc         → /bsp + 自动 Code Review → 有问题回 BSP（合 Gerrit 默认）
/code-review → 标准只读 Review
/coder       → 五维深度 Review（热路径/多模块时加深）
```

---

## 目录结构

```text
skills/
├── README.md
├── QUICKSTART.md / INSTALL.md
├── install.ps1 / install.sh      ← 一键同步到 ~/.cursor
├── manifest.yaml                 ← 版本与包清单
├── bsp-orchestrator/SKILL.md     ← BUG 修复唯一编排入口
├── buc-orchestrator/SKILL.md     ← BSP + Review 闭环
├── code-review/SKILL.md
├── coder/SKILL.md
├── bsp-large-system/SKILL.md     ← 已废弃，重定向 bsp-orchestrator
├── commands/                     ← /bs /bsp /buc 等快捷键
├── templates/
└── for-agents/
    ├── AGENTS.snippet.md         ← Codex / Workbuddy / 通用 Agent
    └── CLAUDE.snippet.md         ← Claude Code
```

---

## 给其他 Agent（Codex / Workbuddy）同步安装

### 方式 A：本机用户级（最快）

```powershell
git pull   # 或 clone iot-sre-delivery-sops
cd skills
.\install.ps1 -Force
```

装到 `%USERPROFILE%\.cursor\skills\` 和 `commands\`。

### 方式 B：业务仓库项目级（团队共享）

```powershell
.\install.ps1 -ProjectRoot "D:\gerrit\iot-server"
```

将 `.cursor/skills/` + `.cursor/commands/` 提交到业务仓 git，同事 pull 即用。

### 方式 C：无 Cursor 快捷键的 Agent

1. 执行方式 A 或 B 安装 skill 文件  
2. 把 [`for-agents/AGENTS.snippet.md`](for-agents/AGENTS.snippet.md) **合并进** 仓库根 `AGENTS.md`  
3. 每次会话开场：

   ```text
   按 buc-orchestrator 执行，Read .cursor/skills/buc-orchestrator/SKILL.md 全文。
   我的需求：BUG …
   ```

---

## 更新 Skills

维护者更新本目录后，同事重新执行：

```powershell
.\install.ps1 -Force
```

---

## 相关文档

- 本仓 Cursor 话术：[`docs/Cursor指令.md`](../docs/Cursor指令.md)
- 现网只读约束：[`docs/现网仓库只读约束.md`](../docs/现网仓库只读约束.md)
