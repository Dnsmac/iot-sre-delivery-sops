# BS / BSP / BUC Skills 安装指南

> 源目录：`D:\demo\iot-sre-delivery-sops\skills`（或 git clone 后的 `skills/`）

---

## 一、Cursor（推荐）

### 方式 A：一键安装（Windows）

```powershell
cd D:\demo\iot-sre-delivery-sops\skills
.\install.ps1
```

可选参数：

```powershell
.\install.ps1 -Force                                    # 覆盖已存在文件
.\install.ps1 -ProjectRoot "D:\gerrit\iot-server"       # 同时装到业务仓库
```

安装内容：

| 类型 | 路径 |
|------|------|
| Skills（5 个） | `%USERPROFILE%\.cursor\skills\{bsp-orchestrator,buc-orchestrator,code-review,coder,bsp-large-system}\SKILL.md` |
| Commands（5 个） | `%USERPROFILE%\.cursor\commands\{bs,bsp,buc,code-review,coder}.md` |

项目级（`-ProjectRoot`）：同上路径，前缀改为 `<ProjectRoot>\.cursor\`。

**完成后**：重启 Cursor → 输入 `/buc` 应出现命令提示。

### 方式 B：手动复制

```powershell
$SRC = "D:\demo\iot-sre-delivery-sops\skills"
$SKILLS = "$env:USERPROFILE\.cursor\skills"
$CMD    = "$env:USERPROFILE\.cursor\commands"

@("bsp-orchestrator","buc-orchestrator","code-review","coder","bsp-large-system") | ForEach-Object {
  New-Item -ItemType Directory -Force -Path "$SKILLS\$_" | Out-Null
  Copy-Item "$SRC\$_\SKILL.md" "$SKILLS\$_\SKILL.md" -Force
}
@("bs","bsp","buc","code-review","coder") | ForEach-Object {
  Copy-Item "$SRC\commands\$_.md" "$CMD\$_.md" -Force
}
```

### 验证

```powershell
@(
  "$env:USERPROFILE\.cursor\skills\bsp-orchestrator\SKILL.md",
  "$env:USERPROFILE\.cursor\skills\buc-orchestrator\SKILL.md",
  "$env:USERPROFILE\.cursor\commands\buc.md"
) | ForEach-Object { Test-Path $_ }
```

在 Cursor 新开聊天：

```text
/buc

我的需求：测试安装，只输出交付包结构，不要改代码。
```

应看到 `[BUC] 已 Read buc-orchestrator，Phase A（BSP）起执行。`

---

## 二、macOS / Linux

```bash
cd /path/to/iot-sre-delivery-sops/skills
chmod +x install.sh
./install.sh
./install.sh --force
./install.sh --project /path/to/iot-server
```

---

## 三、Codex / Workbuddy / 通用 Agent

这些工具可能没有 `/bsp` 快捷键，用 **仓库级 Agent 说明 + Skill 文件** 等效：

### 步骤

1. **安装 skill 文件**（用户级或项目级）：

   ```powershell
   .\install.ps1
   # 或
   .\install.ps1 -ProjectRoot "D:\your-repo"
   ```

2. **合并 Agent 说明**：将 [`for-agents/AGENTS.snippet.md`](for-agents/AGENTS.snippet.md) 合并进仓库根 `AGENTS.md`（Codex）或项目说明文件（Workbuddy）

3. **每次会话开场白**（无快捷键时）：

   ```text
   按 buc-orchestrator 执行。
   Read .cursor/skills/buc-orchestrator/SKILL.md 和 bsp-orchestrator/SKILL.md 全文。
   我的需求：BUG 37xxx …
   ```

4. 若 Agent 支持读绝对路径，也可直接指向分发包：

   ```text
   Read D:\demo\iot-sre-delivery-sops\skills\buc-orchestrator\SKILL.md 全文
   ```

### Codex 与 Workbuddy 差异

| 工具 | 建议做法 |
|------|----------|
| **Codex** | `AGENTS.md` + 项目级 `.cursor/skills/`（可进 git） |
| **Workbuddy** | 同 Codex；或用户级 `install.ps1` + 开场白 Read SKILL |
| **Cursor** | `install.ps1` → 直接用 `/buc` 快捷键 |

---

## 四、Claude Code

1. 复制 Skill 到项目：

   ```powershell
   .\install.ps1 -ProjectRoot "D:\your-repo"
   ```

2. 将 [`for-agents/CLAUDE.snippet.md`](for-agents/CLAUDE.snippet.md) 合并进项目 `CLAUDE.md`

3. 触发：

   ```text
   使用 buc-orchestrator skill，Phase A 起执行。
   BUG 37037 …
   ```

---

## 五、团队同步建议

| 做法 | 说明 |
|------|------|
| **Git pull + install** | 本 `skills/` 进 `iot-sre-delivery-sops`，同事 pull 后 `install.ps1 -Force` |
| **业务仓项目级** | 在 `iot-server` 提交 `.cursor/skills` + `.cursor/commands`（团队统一版本） |
| **仅用户级** | 每人本机 `install.ps1`，适合快速试用 |

维护者更新 `SKILL.md` 后 bump `manifest.yaml` 的 `version`，通知同事 `install.ps1 -Force`。

---

## 六、卸载

```powershell
@("bsp-orchestrator","buc-orchestrator","code-review","coder","bsp-large-system") | ForEach-Object {
  Remove-Item -Recurse -Force "$env:USERPROFILE\.cursor\skills\$_" -ErrorAction SilentlyContinue
}
@("bs","bsp","buc","code-review","coder") | ForEach-Object {
  Remove-Item -Force "$env:USERPROFILE\.cursor\commands\$_.md" -ErrorAction SilentlyContinue
}
```

---

## 七、故障排查

| 现象 | 处理 |
|------|------|
| 输入 `/buc` 无提示 | 确认 `commands/buc.md` 路径；重启 Cursor |
| Agent 不 Read 全文 | 命令首行要求 Read SKILL.md；手动 @ 引用 skill 文件 |
| 仍多轮确认 / 自批改代码 | 对照 `SKILL.md` **授权红线**；回复「G0-8 违规」 |
| BUC 未自动 Review | 确认 `code-review/SKILL.md` 已安装；说「BUC Phase B 违规」 |
| 无文档落盘 | 确认在**可写的业务仓**而非只读学习模式 |
