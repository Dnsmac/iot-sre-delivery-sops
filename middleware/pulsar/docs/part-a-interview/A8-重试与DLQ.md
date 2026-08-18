# A8 Retry 与 DLQ

> 优先级: **P1 面试** | 预计阅读 25 分钟 | 深度：批次 4 ✓

## 本章解决什么问题

消费失败后的**重试链路**是什么、Retry Topic 与 DLQ 各干什么、如何在 Java 里配置，以及如何避免无限重投拖垮系统。

---

## 面试常问

1. 消费失败后消息去哪了？
2. NACK 和 negativeAcknowledge 会发生什么？
3. DLQ 和 Retry Topic 区别？
4. maxRedeliverCount 谁控制？
5. 死信里的消息怎么恢复？

---

## 一、失败处理全链路

```
消费失败
    │
    ├─ negativeAcknowledge / ackTimeout
    │       └─► Redelivery（重新投递，至少一次）
    │
    ├─ redeliveryCount < maxRedeliverCount
    │       └─► 继续重试（可经 Retry Topic 延迟）
    │
    └─ redeliveryCount ≥ maxRedeliverCount
            └─► Dead Letter Topic（DLQ）→ 人工/批处理/回放
```

| 环节 | 说明 |
|------|------|
| **Redelivery** | Broker 将未 ACK 消息再次投递，可能换 Consumer |
| **Retry Topic** | 可选，Broker 自动创建，支持**阶梯延迟**再投主 Topic |
| **DLQ** | 最终归宿，避免毒消息无限循环 |

---

## 二、触发重投的方式

| 方式 | 场景 |
|------|------|
| `negativeAcknowledge(msg)` | 业务判定不可立即成功 |
| 未 ACK + 进程崩溃 | 重启后重投 |
| `ackTimeout` | 处理时间超过配置，Broker 自动重投 |
| Shared rebalance | 未 ACK 消息可能被其他实例拉取 |

详见 [A6](A6-ACK与投递语义.md)、[P2](../part-d-problems/P2-重复消费.md)。

---

## 三、Java 配置 DLQ

```java
consumer.newConsumer()
    .topic("persistent://dev/test/events")
    .subscriptionName("order-service")
    .deadLetterPolicy(DeadLetterPolicy.builder()
        .maxRedeliverCount(3)
        .deadLetterTopic("persistent://dev/test/events-dlq")
        .retryLetterTopic("persistent://dev/test/events-retry") // 可选
        .build())
    .subscribe();
```

| 参数 | 建议 |
|------|------|
| maxRedeliverCount | 3~5，结合业务可重试性 |
| deadLetterTopic | 独立 Topic，独立 Subscription 消费 |
| retryLetterTopic | 需要延迟退避时启用 |

Namespace 级也可配置 `deadLetterPolicy`（集群统一治理）。

---

## 四、Retry Topic 延迟（概念）

- Broker 将失败消息先写到 **Retry Topic**，到期后再写回主 Topic。
- 支持多级延迟（如 1min → 5min → 30min），减轻瞬时故障压力。
- 面试答法：**Retry 是「还会再试」的缓冲；DLQ 是「放弃自动重试」的隔离区**。

---

## 五、DLQ 运维与回放

1. **监控 DLQ backlog**，告警阈值 > 0 持续 N 分钟。
2. 单独 Consumer 读 DLQ，人工修复数据或修 bug。
3. 回放：修复后作为 **新 Producer** 发到主 Topic（带原业务 id 幂等）。
4. 不要直接在 DLQ 上 ACK 就当「已处理」而无业务记录。

```powershell
docker exec pulsar-standalone bin/pulsar-admin topics stats persistent://dev/test/events-dlq
```

---

## 六、生产环境注意点

- 可重试异常（超时、下游 503）→ NACK；不可重试（校验失败）→ **直接 ACK + 记审计** 或送 DLQ，避免无意义重试。
- DLQ 消息保留 Retention 要够长，便于追查。
- 与 [P2 重复消费](../part-d-problems/P2-重复消费.md) 配合：**重试必然可能重复，必须幂等**。

---

## 七、易错点

1. 不设 maxRedeliverCount，毒消息无限 NACK。
2. DLQ 与主 Topic 共用 subscriptionName。
3. 所有异常都 NACK，包括参数错误。
4. 以为进了 DLQ 就会自动修复——需人工或批任务。

---

## 面试标准答案

> 消费失败可以先 NACK 或 ack 超时触发 redelivery。超过 maxRedeliverCount 后进入死信队列 DLQ，由运维或批处理单独消费。Retry Topic 是 Broker 在重试前做的延迟队列，减轻瞬时故障。DLQ 是最终归宿，Retry 是延迟再试。生产必须配 DLQ 和幂等，避免毒消息打满 CPU。

---

## 相关章节

- [B3 Consumer](../part-b-java-dev/B3-消费者.md) | [A6 ACK](A6-ACK与投递语义.md) | [P1](../part-d-problems/P1-消息丢失.md)
