# A3 Cluster 与 KRaft

> P1 强荐 | 预计 25 分钟 | [A2](A2-核心架构.md) → [A4](A4-Topic与分区.md)

## 要点

- **KRaft**（Kafka 3.x+）：用内置 Raft  quorum 管元数据，**逐步替代 ZooKeeper**。
- **Controller / Quorum Leader**：负责分区 Leader 选举、Broker 注册。
- 面试说：「新集群用 KRaft；老集群可能还有 ZK，我知道在迁。」

## 与 Pulsar

- Pulsar 元数据：ZK/Oxia；Kafka：KRaft/ZK。

## 自检

- [ ] KRaft 解决什么问题（元数据、Controller 单点）

**待深化：** Broker 配置、`process.roles=broker,controller` 本地 Docker 示例见 [README](../../README.md)
