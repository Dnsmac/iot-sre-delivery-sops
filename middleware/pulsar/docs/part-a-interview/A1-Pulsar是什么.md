# A1 Pulsar 是什么

> 优先级: **P1 必学（G1 面试）** | 预计 25 分钟 | 学习顺序：**第 1 天第 1 章**  
> 路径：[LEARNING-PATH](../LEARNING-PATH.md) | 明天学：[A2 核心架构](A2-核心架构.md)

## 本章解决什么问题

建立 Pulsar 的**定位**：它解决什么问题、和 Kafka 等有什么不同、什么场景该选、什么场景不必强行迁移。  
学完应能说出 [30 秒面试开场](../LEARNING-PATH.md#31-30-秒开场背熟再改写) 的第一段。

---

## 面试开场（学完本章就能说）

**30 秒版本（背熟后改成自己的话）：**

> Pulsar 是 Apache 的分布式消息与流平台，核心特点是**存算分离**——消息存在 BookKeeper，Broker 负责接入。和 Kafka 比，它更适合**多租户、同一 Topic 多套独立消费**，以及按 Key 有序并行消费的 Key_Shared 模式。

完整结构（3 分钟、追问往哪引）：[LEARNING-PATH §三](../LEARNING-PATH.md#三面试怎么讲开场--深入--结合项目)

**今日作业：** 用 1 句话写「我们项目为什么用 Pulsar / 和 Kafka 比还差什么认知」。

---

## 一、Pulsar 是什么

**Apache Pulsar** 是开源的**分布式消息与流平台**（Messaging + Streaming），由 Yahoo 开源，现由 Apache 基金会维护，StreamNative 等公司提供商业支持。

**一句话：** 像 Kafka 一样收发海量消息，但把**消息存储**（BookKeeper）和**消息计算/接入**（Broker）拆开，并原生支持**多租户、多订阅、Geo 复制**。

**不是：** 数据库、RPC 框架、MQTT Broker 本身（虽然可协议扩展）。设备场景常见 **MQTT → 网关 → Pulsar**。

---

## 二、核心设计思想（面试必讲）

### 2.1 存储与计算分离

| | Kafka 传统模型 | Pulsar |
|---|----------------|--------|
| 消息存在哪 | Broker 本地磁盘分区日志 | BookKeeper 集群 |
| 扩 Broker | 往往伴随数据再均衡 | 可加 Broker，不搬数据 |
| 扩存储 | 加 Broker 或分区 | 加 Bookie |

带来的结果：**Broker 无状态（不持久化消息体）**、存储层可独立扩容、故障域更清晰。

### 2.2 统一消息与流

- 同一套系统既可做**队列**（竞争消费、ACK），也可做**流**（回溯、保留、Compaction）。
- 延迟消息、函数计算（Pulsar Functions）在同一生态。

### 2.3 多租户原生

- `Tenant / Namespace / Topic` 三级，策略（Retention、Quota、ACL）在 Namespace 级统一治理。
- 适合 SaaS、集团多事业部共用集群。

### 2.4 消费模型灵活

- 同一 Topic 上多个 **Subscription**，各自 **Cursor**，互不影响。
- 四种订阅模式：Exclusive / Failover / Shared / **Key_Shared**（设备/用户级有序 + 并行）。

---

## 三、与 Kafka / RocketMQ / RabbitMQ 对比

### 3.1 Pulsar vs Kafka（最常考）

| 维度 | Pulsar | Kafka |
|------|--------|-------|
| 架构 | Broker + BookKeeper | Broker 存算一体 |
| 消费进度 | 每 Subscription 一个 Cursor | Consumer Group Offset |
| 同一 Topic 多消费方 | 多 Subscription，天然独立 | 多 Consumer Group |
| 消息保留 | Retention 独立于是否消费 | 与 Group 消费进度耦合（compact 除外） |
| 多租户 | Tenant/Namespace 原生 | 主要靠命名与运维规范 |
| 订阅语义 | 4 种模式 | 主要是分区 + CG |
| Geo | 内置 Geo-Replication | MirrorMaker 等 |
| 生态成熟度 | 快速增长，KoP 兼容 Kafka 协议 | 最成熟 |

**何时选 Pulsar：** 多租户、多独立消费组、Key 级有序并行、跨机房复制、希望存储计算分离运维。  
**何时留 Kafka：** 团队深度 Kafka 生态、现有链路迁移成本极高、无上述强需求。

**过渡方案：** **KoP**（Kafka on Pulsar）让 Kafka 客户端连 Pulsar，渐进迁移。

### 3.2 Pulsar vs RocketMQ

| 维度 | Pulsar | RocketMQ |
|------|--------|----------|
| 存储 | BookKeeper | 自研 CommitLog |
| 顺序消息 | 分区 / Key_Shared | 分区顺序成熟 |
| 国内文档运维 | 相对少 | 非常丰富 |
| 事务 | Transaction API | 事务消息成熟 |

### 3.3 Pulsar vs RabbitMQ

| 维度 | Pulsar | RabbitMQ |
|------|--------|----------|
| 定位 | 分布式日志型、高吞吐 | AMQP、灵活路由、低延迟 |
| 吞吐与扩展 | 水平扩展 TB 级 | 集群复杂，超大流量常迁 Kafka/Pulsar |
| 协议 | 自有 + MQTT/KoP 等 | AMQP |

RabbitMQ 适合复杂路由、中等流量；Pulsar 适合大数据量、流式、多订阅。

---

## 四、典型应用场景

| 场景 | 为什么适合 Pulsar |
|------|-------------------|
| 微服务异步解耦 | 多服务独立 Subscription |
| 订单/支付事件流 | Key_Shared + 持久化 + DLQ |
| 物联网设备上报 | 海量连接经 MQTT 接入后入 Pulsar |
| 日志/埋点管道 | Shared 高吞吐 + Tiered Storage 降成本 |
| 跨机房灾备 | Geo-Replication |
| 多团队共用集群 | 多租户隔离 |

---

## 五、版本与部署形态（了解）

| 版本 | 说明 |
|------|------|
| 2.10 / 2.11 | 生产常用 LTS 线 |
| 3.x | 新特性、Oxia 元数据等，关注发行说明 |

| 形态 | 用途 |
|------|------|
| Standalone | 开发测试 |
| Cluster | 生产 |
| K8s / Helm | 云原生部署 |

---

## 六、面试标准答案

### 题：Pulsar 的核心设计思想是什么？

> 第一是存储计算分离，消息存在 BookKeeper，Broker 负责接入和路由，Broker 可以水平扩展而不迁移分区数据。第二是多租户和多订阅，一个 Topic 可以有多个独立订阅，每个订阅有自己的消费进度。第三是统一的队列和流模型，支持回溯、保留、Compaction 和 Geo 复制。第四是灵活的订阅模式，特别是 Key_Shared，可以在并行消费的同时保证同一个 Key 有序，适合订单和设备场景。

### 题：什么场景选 Pulsar 不选 Kafka？

> 需要强多租户隔离、同一 Topic 多套独立消费进度、设备或用户级有序且要多个 Consumer 并行、或者要原生跨机房复制时，Pulsar 更合适。如果团队已经 All-in Kafka、生态绑定很深、没有这些强需求，继续 Kafka 或先用 KoP 迁移更现实。我们项目如果当前是 Shared 加非分区，其实是在用 Pulsar 但没用它的核心优势，应该评估 Key_Shared 和分区设计。

---

## 七、易错点

1. **「Pulsar 完全优于 Kafka」** → 错，生态与团队经验是选型一部分。
2. **把 Pulsar 当 MQTT Broker** → 设备接入常用 MQTT Broker + 桥接 Pulsar。
3. **只用 Shared + 非分区** → 能跑，但没发挥 Key_Shared、多订阅、存储分离优势（见 [B13](../part-b-java-dev/B13-推动策略改造.md)）。

---

## 八、相关章节

- **明日**：[A2 核心架构](A2-核心架构.md)
- [LEARNING-PATH 主线](../LEARNING-PATH.md) | [附录 B](../appendices/B-Kafka对照.md) | [A3 多租户](A3-多租户层级.md)
