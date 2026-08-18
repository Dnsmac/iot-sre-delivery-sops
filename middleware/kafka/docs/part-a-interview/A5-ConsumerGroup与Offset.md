# A5 Consumer Group 与 Offset

> 优先级: **P1 必学** | 预计 35 分钟  
> 对照 Pulsar：[A5 订阅模式](../../pulsar/docs/part-a-interview/A5-订阅模式.md)

## 核心概念

| 概念 | 说明 |
|------|------|
| **Consumer Group** | 一组 Consumer 共享进度；**≈ Pulsar Subscription** |
| **group.id** | Group 唯一标识；**不同服务必须不同 group** |
| **Offset** | 某 Partition 上消费位置；**≈ Pulsar Cursor** |
| **Rebalance** | Group 内成员变化时 **重新分配 Partition** |

---

## Rebalance 触发

- Consumer 加入/离开
- 订阅 Topic 变化
- Partition 数量变化

**影响：** 短暂停消费、重复消费风险上升 → 要 **幂等**。

---

## 分配策略（了解）

- Range、RoundRobin、Sticky、Cooperative（增量 rebalance）

---

## 与 Pulsar 对照

| Pulsar | Kafka |
|--------|-------|
| Subscription 名 | `group.id` |
| Cursor | Offset per partition |
| Key_Shared 多 Consumer | 同 CG 多 Consumer 各管若干分区 |
| 多 Subscription 独立 | 多 **Consumer Group** 独立 |

---

## 面试句

> 同一个 Topic，订单服务和报表服务要用 **两个 Consumer Group**，各自 Offset，互不影响——这和 Pulsar 两个 Subscription 一样。

---

## 自检

- [ ] group.id 错用的后果
- [ ] Rebalance 为什么导致重复消费

**下一章：** [A6](A6-投递语义与ACK.md)
