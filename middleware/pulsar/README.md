# Apache Pulsar 完整学习仓库

> **本仓索引**：[`../README.md`](../README.md) · **优先级：** 面试 P1 → 开发 P2 → 扩展 P3 | **技术栈：** Java 8+ · Pulsar Client 3.2.3

本仓库提供 **Part A~D 原理与排障**、**附录速查**、**实战项目** 与 **Java 示例**，文档已按 [DEPTH-STANDARD](docs/DEPTH-STANDARD.md) **全文深化**（见 [DEEPENING-ROADMAP](docs/DEEPENING-ROADMAP.md)）。

## 学习进度（建议阅读顺序）

1. **[学习目标路径](docs/LEARNING-PATH.md)** — **今天/明天学什么**、知识怎么串、**面试 30 秒/3 分钟怎么讲**
2. **[学习进度仪表盘](docs/STUDY-TRACKER.md)** — 38 天日程、毕业考勾选、每日日志
3. **[全局索引](docs/INDEX.md)** — 各章链接与 P1/P2/P3 优先级

- [技术学习框架（可复用）](docs/FRAMEWORK-TECH-LEARNING.md)

## 学习路线

| 阶段 | 周期 | 内容 | 入口 |
|------|------|------|------|
| Phase 1 | Week 1-2 | Part A 面试核心 | [docs/part-a-interview/](docs/part-a-interview/) |
| Phase 2 | Week 3-5 | Part B Java 开发 + 项目 P1~P4 | [docs/part-b-java-dev/](docs/part-b-java-dev/) · [projects/](docs/projects/) |
| Phase 3 | Week 6+ | Part C 运维 + 项目 P5~P7 | [docs/part-c-ops/](docs/part-c-ops/) |
| 全阶段 | 随时 | Part D 问题百科 + 附录 | [Part D](docs/part-d-problems/INDEX.md) · [附录](docs/INDEX.md#附录) |

## 快速开始

```powershell
# 启动 Standalone
.\scripts\standalone-up.ps1
# 初始化 dev tenant
.\scripts\setup-dev-tenant.ps1
# 验证示例
.\scripts\verify-examples.ps1
# Hello World
cd examples\java\pulsar-basics
mvn -q exec:java "-Dexec.mainClass=com.demo.pulsar.HelloPulsar"
```

## 推动策略改造（Shared / 非分区 / Auto-Create）

- [B13 如何说服同事与上级](docs/part-b-java-dev/B13-推动策略改造.md)
- [附录 K 方案一页纸](docs/appendices/K-方案一页纸模板.md)
- [Shared→Key_Shared 迁移速查](docs/appendices/K-Shared改KeyShared速查.md)
- [P4 迁移实战](docs/projects/P4-订阅与Topic改造.md)

## 文档与示例

| 类型 | 路径 |
|------|------|
| 面试题 50 道 | [附录 A](docs/appendices/A-面试题与参考答案.md) |
| 速查 / Runbook | [附录 B~L](docs/INDEX.md) |
| Java 示例 | [examples/java/](examples/java/) |
| 设计 Spec | [docs/superpowers/specs/](docs/superpowers/specs/) |

## 毕业建议

- 理论：Part A + 附录 A 自测 ≥ 40 题
- 开发：**P2** + B2/B3 示例跑通 + B9 排障（**P1 订单项目可跳过**）
- 工程：P3 或 P4 阶段 1+ / 环境迁移清单 [附录 I](docs/appendices/I-环境迁移清单.md)
- 运维/压测：P5 或 P6（Cluster 环境）
