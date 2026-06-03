# Superpowers 文档约定（规划变更专用）

本仓库用 superpowers 四步流程管理 **规划类文档** 变更，规则见 [`.cursor/rules/plan-change-workflow.mdc`](../../.cursor/rules/plan-change-workflow.mdc)。

## 目录

| 路径 | 用途 | 何时写 |
|------|------|--------|
| `specs/YYYY-MM-DD-<主题>-design.md` | 设计稿（范围、方案、验收标准） | brainstorming 阶段，**用户批准设计后** |
| `plans/YYYY-MM-DD-<主题>.md` | 实施计划（改哪些文件、逐步 Task） | writing-plans 阶段，**用户批准 spec 后** |

## 命名示例

- `specs/2026-05-23-plan-2h-september-design.md`
- `plans/2026-05-23-plan-2h-september.md`

## 与 PLAN.md 的关系

- **`PLAN.md`**：学员执行的「当前生效计划」（单一真相源）
- **`specs/` + `plans/`**：变更 **历史与决策记录**；大改须先落 spec/plan，再改 PLAN

## Agent 声明话术

每个阶段开头在对话中声明（便于学员审计是否走流程）：

1. 「使用 brainstorming skill 分析规划变更。」
2. 「使用 writing-plans skill 写实施计划。」
3. （改文档阶段无需声明）
4. 「使用 verification-before-completion 做变更验收。」
