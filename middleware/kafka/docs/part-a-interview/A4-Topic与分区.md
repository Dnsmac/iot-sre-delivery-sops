# A4 Topic 与分区

> 优先级: **P1 必学** | 预计 30 分钟  
> 上一章：[A3](A3-Cluster与KRaft.md) | 下一章：[A5](A5-ConsumerGroup与Offset.md)

## 核心概念

| 概念 | 说明 |
|------|------|
| **Topic** | 消息逻辑分类，如 `device.telemetry` |
| **Partition** | 并行度；**分区内有序** |
| **Replication Factor** | 副本数，通常 3（生产） |
| **Leader / ISR** | 在副本集合中选 Leader；ISR = 同步副本集 |

---

## 分区规划（面试 + IoT）

| 原则 | 说明 |
|------|------|
| 分区数 ≈ 峰值并行消费 | Consumer 数 ≤ 分区数才有意义 |
| **只增不减** | 增加分区会破坏 Key 级顺序（旧 Key 可能换分区） |
| 设备有序 | `key = deviceId`，同 Key 始终进同一分区 |
| 热点 Key | 单分区成为瓶颈 → 类似 Pulsar Key 热点 |

---

## 与 Pulsar 对照

| Kafka | Pulsar |
|-------|--------|
| Topic + N Partition | 分区 Topic 的 partition 数 |
| 非分区 Topic | Pulsar 非分区 Topic（Kafka 至少 1 分区） |

---

## 命令速查

```bash
kafka-topics.sh --describe --topic dev.events --bootstrap-server localhost:9092
```

---

## 自检

- [ ] 为什么分区数不能随意减
- [ ] IoT 设备 Key 如何选

**下一章：** [A5](A5-ConsumerGroup与Offset.md)
