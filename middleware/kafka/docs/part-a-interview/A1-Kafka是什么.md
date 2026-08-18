# A1 Kafka 是什么

> 优先级: **P1 必学（G1 面试）** | 预计 25 分钟 | **第 1 天第 1 章**  
> 路径：[LEARNING-PATH](../LEARNING-PATH.md) | 明天学：[A2 核心架构](A2-核心架构.md)

## 本章解决什么问题

建立 Kafka 的**定位**：分布式**分区日志**、和 Pulsar/RabbitMQ 的差异、JD 常问点。  
学完应能说出 [30 秒开场](../LEARNING-PATH.md#31-30-秒开场)。

---

## 面试开场（30 秒）

> Kafka 是 Apache 的分布式**流式消息平台**，核心是 **Topic 分区 append-only 日志**，Producer 追加、Consumer 按 **Consumer Group + Offset** 拉取。Broker **存算一体**，元数据现多用 **KRaft**。和 Pulsar 比，Kafka **生态最成熟**；多消费方用 **多个 Consumer Group**。我们现网设备链路走 EventBus，中间件是 Pulsar，Kafka 我用于 **概念对照和 JD 防御**。

**今日作业：** 写 1 句「现网不是 Kafka，但 lag/分区/至少一次怎么对应 Pulsar」。

---

## 一、Kafka 是什么

**Apache Kafka** 是开源的**分布式事件流平台**（Messaging + Streaming），LinkedIn 开源，现由 Apache 维护。

**一句话：** 高吞吐、可持久化的 **Topic 分区日志**，通过 **Consumer Group** 实现发布订阅与队列语义。

**不是：** 数据库、RPC、MQTT Broker（IoT 设备 MQTT 通常在网关，消息进 Kafka/Pulsar/EventBus 是下一跳）。

---

## 二、核心设计思想

### 2.1 分区日志（Partition Log）

- 每个 **Topic** 拆成多个 **Partition**，每条消息 append 到某分区末尾。
- **分区内有序**；跨分区无全局顺序。
- 顺序消费 / 设备有序：**同一 Key 进同一分区**。

### 2.2 存算一体

- 消息存在 **Broker 本地磁盘**（分段 log segment）。
- 扩容 Broker 常涉及 **分区副本迁移**（与 Pulsar BookKeeper 分离存储不同）。

### 2.3 Consumer Group

- 一个 Group 内多个 Consumer **分摊分区**（一个分区同一时刻只给一个 Consumer）。
- **Offset** 记录消费进度，存在 `__consumer_offsets` 或外部存储。

### 2.4 持久化与回溯

- 消息按 **retention** 保留，Consumer 可 **seek** 到历史 offset 重放。

---

## 三、与 Pulsar / RabbitMQ 对比

| 维度 | Kafka | Pulsar |
|------|-------|--------|
| 存储 | Broker 本地 log | BookKeeper |
| 多消费方 | 多 Consumer Group | 多 Subscription |
| 多租户 | 命名规范为主 | Tenant/Namespace 原生 |
| 设备 Key 有序 | 分区 + Key | Key_Shared |
| 生态 | Connect/Streams 最丰富 | KoP、Functions |

详见 [附录 B](../appendices/B-Pulsar对照.md)。

---

## 四、典型架构（口述用）

```text
Producer → Broker(Leader 分区) → Follower 副本
              ↓
Consumer Group ← fetch ← 各 Partition
```

---

## 五、IoT 场景怎么用 Kafka（概念）

| 场景 | Kafka 常见做法 |
|------|----------------|
| 设备上报 | 网关聚合后 **Producer** 写 Topic；按 **deviceId 作 Key** 保序 |
| 多服务消费 | 规则引擎、存储、告警各一个 **Consumer Group** |
| 积压 | 看 **Consumer Lag** |
| 与 MQTT 关系 | MQTT 在接入层；Kafka 在 **平台消息层**（你现网是 EventBus，不是 Kafka） |

---

## 六、本章自检

- [ ] 能画 Topic → Partition → Leader/Follower
- [ ] 能说出 Consumer Group 与 Offset 各是什么
- [ ] 能 1 句话对比 Pulsar Subscription

**下一章：** [A2 核心架构](A2-核心架构.md)
