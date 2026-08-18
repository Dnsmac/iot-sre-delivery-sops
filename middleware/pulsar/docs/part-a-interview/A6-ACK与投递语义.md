# A6 ACK 与投递语义

> 优先级: **P1 面试** | 预计阅读 20 分钟 | 深度：批次 1

## 本章解决什么问题

弄清 **Broker 如何认为一条消息「已被消费」**，以及为什么会出现重复消费、为什么 ACK 方式影响吞吐。

---

## 三种投递语义

| 语义 | 实现方式 | 丢消息？ | 重复？ | 典型场景 |
|------|----------|----------|--------|----------|
| **At most once** | 先 ACK 再处理，或 autoAck | 可能 | 否 | 监控旁路 |
| **At least once** | 处理成功再 ACK（默认） | 否 | **可能** | **生产主流** |
| **Exactly once** | Transaction 跨 Topic 原子提交 | 否 | 否（协议层） | 金融级跨 Topic |

**面试必答：** Pulsar 默认 Consumer 是 **At least once**，不是 Exactly once；Exactly once 要开事务且代价大。

---

## Cursor 与 MarkDelete

- 每个 **Subscription** 维护独立 **Cursor**（存在 BK，元数据在 Metadata Store）。
- Consumer `acknowledge(msg)` → Broker 把 Cursor **MarkDelete** 推进到该 MessageId。
- **累积 ACK：** `acknowledgeCumulative(msg)` 表示该 MessageId 及之前全部确认。
- **多个 Subscription** 同一 Topic 各自 Cursor，互不影响（对比 Kafka 一个 Consumer Group 一条 offset 线）。

### vs Kafka Offset

| | Pulsar Cursor | Kafka Offset |
|---|---------------|--------------|
| 绑定对象 | Subscription | Consumer Group + Partition |
| 多消费组 | 多 Subscription，天然支持 | 多 Group 各自 offset |
| 回溯 | `seek(MessageId)` / earliest | reset offset |

---

## ACK 方式对比

| 方式 | 吞吐 | 风险 |
|------|------|------|
| 单条 ACK | 较低 | 精确，失败不重投整批 |
| 累积 ACK | 高 | 中间一条失败导致**整批重投** |
| 不 ACK | — | 直到 `ackTimeout` 重投 |
| negativeAcknowledge | — | 按 `negativeAckRedeliveryDelay` 重投 |

```java
consumer.acknowledge(msg);                    // 单条
consumer.acknowledgeCumulative(msg);        // 累积
consumer.negativeAcknowledge(msg);          // 立即重投
// 不 ack → ackTimeout 后重投
```

---

## 重复消费的四种常见原因

1. **处理完但 ACK 前崩溃** → 重启后重投（正常 at-least-once）。
2. **`ackTimeout` 小于处理时间** → 处理中被判超时重投。
3. **NACK 或处理异常** → redelivery。
4. **Shared 模式 rebalance** → 消息被另一 Consumer 再处理。

**生产必须：** 业务 **幂等**（messageId / businessKey 去重表）。

---

## 面试标准答案

### 题：Pulsar 怎么保证消息不丢？为什么会重复？

> 不丢靠 BookKeeper 多副本持久化加上 Consumer 处理完再 ACK。只要 ACK 了，Cursor 推进，正常情况下不会要求你再消费这条。重复是因为至少一次语义：消费者可能在 ACK 之前崩溃，或者 ackTimeout 到了还没 ACK，Broker 会认为没消费完再次投递。所以 Pulsar 要求业务做幂等。如果要跨 Topic 精确一次，需要用 Transaction，一般场景用 at-least-once 加幂等更常见。

---

## 相关章节

- [A8 Retry/DLQ](A8-重试与DLQ.md) | [B3](../part-b-java-dev/B3-消费者.md) | [P2 重复](../part-d-problems/P2-重复消费.md)
