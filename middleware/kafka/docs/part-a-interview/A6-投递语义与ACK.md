# A6 投递语义与 ACK

> P1 必学 | [A5](A5-ConsumerGroup与Offset.md) → [A7](A7-保留与清理策略.md)

## 三种语义

| 语义 | Producer | Consumer |
|------|----------|----------|
| 最多一次 | 发后即忘 | 先提交 offset 再处理 |
| **至少一次**（默认常见） | acks≥1 | 先处理再提交；**可能重复** |
| 精确一次 | 事务 + 幂等 Producer | 事务消费（复杂） |

## Producer 关键参数

| 参数 | 含义 |
|------|------|
| `acks=0/1/all` | 0 不等待；1 Leader 写盘；all ISR 全确认 |
| `enable.idempotence` | 幂等 Producer，防重发重复 |
| `min.insync.replicas` | 与 acks=all 配合 |

## Consumer

- **手动提交** `commitSync` / `commitAsync`：处理成功后再提交
- **自动提交** `enable.auto.commit=true`：可能丢或重复，生产慎用

## 面试句

> 我们按至少一次设计，**消费端幂等**；和 Pulsar 手动 ACK 思路一样。

## 相关

- [P1 消息丢失](../part-d-problems/P1-消息丢失.md) | [P2 重复消费](../part-d-problems/P2-重复消费.md)
