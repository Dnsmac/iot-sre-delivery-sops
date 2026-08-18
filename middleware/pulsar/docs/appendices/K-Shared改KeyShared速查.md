# 附录：Shared + 非分区 → Key_Shared + 分区（迁移速查）

> 与 [附录 K 方案一页纸](K-方案一页纸模板.md) 不同：本文是**技术迁移步骤**；对外评审用一页纸模板。

---

## 何时要改

| 信号 | 建议 |
|------|------|
| 同设备/订单乱序 | 改 Key_Shared + Producer Key |
| 加 Consumer 吞吐不涨 | 加分区 Topic |
| 生产 Auto-Create | 先治理（[P4 阶段 1](../projects/P4-订阅与Topic改造.md)） |

**可不改：** 埋点/日志、无顺序要求、极低 QPS。

---

## 改造四件套

1. **Topic**：`create-partitioned-topic -p N`（N 按压测，非设备数）
2. **Producer**：`.key(businessId)` 每条消息
3. **Consumer**：`SubscriptionType.Key_Shared` + `stickyHashRange()`
4. **治理**：关 Auto-Create、脚本预建 Topic

---

## 代码片段

```java
// Producer
producer.newMessage().key(deviceId).value(payload).send();

// Consumer
.subscriptionType(SubscriptionType.Key_Shared)
.keySharedPolicy(KeySharedPolicy.stickyHashRange())
```

---

## 灰度与验证

- 跑 [SharedOrderingDemo](../../examples/java/pulsar-troubleshooting/src/main/java/com/demo/pulsar/trouble/SharedOrderingDemo.java) 对比
- 对照 [P3 乱序](../part-d-problems/P3-消息乱序.md) 排查表
- 完整步骤：[P4 项目](../projects/P4-订阅与Topic改造.md)
- 说服与排期：[B13](../part-b-java-dev/B13-推动策略改造.md)、[附录 K 一页纸](K-方案一页纸模板.md)

---

## 相关

- [A5 订阅模式](../part-a-interview/A5-订阅模式.md) | [B3 Consumer](../part-b-java-dev/B3-消费者.md) | [B2 Producer](../part-b-java-dev/B2-生产者.md)
