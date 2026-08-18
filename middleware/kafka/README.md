# Apache Kafka 完整学习仓库

> **本仓索引**：[`../README.md`](../README.md) · **优先级：** 面试 P1 → 开发 P2 → 扩展 P3 | **技术栈：** Java 8+ · kafka-clients 3.x  
> **与 Pulsar 仓关系：** 本仓独立学 Kafka；现网 Pulsar 对照见 [附录 B](docs/appendices/B-Pulsar对照.md) 与 [pulsar 附录 B](../pulsar/docs/appendices/B-Kafka对照.md)

本仓库提供 **Part A~D 原理与排障**、**附录速查**、**实战项目索引** 与 **Java 示例占位**，结构对齐 [`../pulsar/README.md`](../pulsar/README.md)。

## 学习进度（建议阅读顺序）

1. **[学习目标路径](docs/LEARNING-PATH.md)** — 今天/明天学什么、面试 30 秒/3 分钟怎么讲
2. **[学习进度仪表盘](docs/STUDY-TRACKER.md)** — 日程勾选、每日日志
3. **[全局索引](docs/INDEX.md)** — 各章链接与 P1/P2/P3 优先级

## 学习路线

| 阶段 | 周期 | 内容 | 入口 |
|------|------|------|------|
| Phase 1 | Week 1-2 | Part A 面试核心 | [docs/part-a-interview/](docs/part-a-interview/) |
| Phase 2 | Week 3-5 | Part B Java 开发 + 项目 P1~P4 | [docs/part-b-java-dev/](docs/part-b-java-dev/) |
| Phase 3 | Week 6+ | Part C 运维 + 项目 P5~P7 | [docs/part-c-ops/](docs/part-c-ops/) |
| 全阶段 | 随时 | Part D 问题百科 + 附录 | [Part D](docs/part-d-problems/INDEX.md) |

## 快速开始（本地）

```powershell
# 需 Docker；首次启动后创建测试 Topic
docker run -d --name kafka-dev -p 9092:9092 `
  -e KAFKA_NODE_ID=1 `
  -e KAFKA_PROCESS_ROLES=broker,controller `
  -e KAFKA_LISTENERS=PLAINTEXT://:9092,CONTROLLER://:9093 `
  -e KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://localhost:9092 `
  -e KAFKA_CONTROLLER_LISTENER_NAMES=CONTROLLER `
  -e KAFKA_CONTROLLER_QUORUM_VOTERS=1@localhost:9093 `
  apache/kafka:latest

# 创建 Topic（容器内）
docker exec kafka-dev /opt/kafka/bin/kafka-topics.sh --create `
  --bootstrap-server localhost:9092 --topic dev.events --partitions 3 --replication-factor 1
```

Java 示例目录：`examples/java/`（与 pulsar 仓同构，按需补充）。

## JD / 面试场景

| 场景 | 读本仓 | 对照现网 Pulsar |
|------|--------|-----------------|
| JD 写 Kafka，你现网 Pulsar | 附录 B + A1 | pulsar 附录 B |
| 问积压 / lag | [P4 积压](docs/part-d-problems/P4-积压.md) | pulsar P4 |
| IoT 设备消息 | A4 分区 + A5 Consumer Group | pulsar A5 Key_Shared |

## 毕业建议

- 理论：Part A + 附录 A 自测 ≥ 30 题
- 开发：B1~B3 示例跑通 + B9 排障四类问题
- 对照：能讲清 **Kafka Consumer Group ≈ Pulsar Subscription** 等 5 组映射
