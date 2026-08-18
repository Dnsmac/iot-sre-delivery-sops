# B13 推动迁移与 Pulsar 对照（面试/JD）

> 对齐 pulsar [B13](../../pulsar/docs/part-b-java-dev/B13-推动策略改造.md) · 附录 [B](../appendices/B-Pulsar对照.md)

## 适用场景

- JD 写 **Kafka**，现网 **Pulsar** 或设备链路 **EventBus**
- 面试官问「为什么不用 Kafka」

## 30 秒口径（模板）

> 我们选型是 **Pulsar + 平台 EventBus**，设备 MQTT 不进 Kafka。Kafka 的 **Consumer Group、分区有序、lag 排查** 我学过，和 Pulsar 的 Subscription、Key_Shared、backlog **可以对照讲**。若新服务要上 Kafka，我会看 **多订阅是否必要、团队运维栈、是否已有 Connect 生态**。

## 对照表（必背 5 组）

1. Consumer Group ↔ Subscription  
2. Offset ↔ Cursor  
3. Partition ↔ 分区 Topic 的分区  
4. Lag ↔ Backlog  
5. Key → Partition ↔ Key_Shared  

## 一页纸

- [附录 K 方案模板](../appendices/K-方案一页纸模板.md)（待写）
