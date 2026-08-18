# 附录 B：Kafka ↔ Pulsar 对照表

> 深度：全文加深 ✓ | 配合 [A1](../part-a-interview/A1-Pulsar是什么.md)、[B13](../part-b-java-dev/B13-推动策略改造.md)  
> **Kafka 侧镜像文档：** [B-Pulsar对照.md](../../kafka/docs/appendices/B-Pulsar对照.md)

---

## 一、概念映射（速查）

| Kafka 概念 | Pulsar 概念 | 差异要点 |
|------------|-------------|----------|
| Cluster | Cluster | 类似 |
| Topic | Topic | Pulsar 必须带 `persistent://tenant/ns/` |
| Partition | Partition（分区 Topic） | Pulsar 还有**非分区** Topic |
| Consumer Group | **Subscription** | 名称不同，语义接近「共享进度的一组 Consumer」 |
| Group Offset | **Cursor** | 存在 Subscription 上，非 Topic 全局 |
| 第二个消费方 | 第二个 **Subscription** | 无需换 Group，天然多订阅 |
| Broker 日志 | BookKeeper Ledger | Pulsar 存算分离 |
| log.retention | **Retention**（Namespace） | 与是否消费**无关** |
| MirrorMaker | **Geo-Replication** | 原生多集群复制 |
| Kafka 协议 | **KoP** | Kafka API 连 Pulsar |

---

## 二、架构对比

```
Kafka:  Producer → Broker(分区日志本地盘) → Consumer
                扩 Broker 常伴随分区迁移

Pulsar: Producer → Broker(无状态) → BookKeeper → Consumer
                扩 Broker 不搬数据；扩 Bookie 扩存储
```

| 维度 | Kafka | Pulsar |
|------|-------|--------|
| 存储位置 | Broker 本地 | BookKeeper 集群 |
| Broker 故障 | 依赖 ISR 副本 | 换 Broker，数据在 BK |
| 元数据 | KRaft/ZK | ZK / Oxia |
| 运维重心 | 分区再均衡、磁盘 | Bookie Journal 磁盘、Bundle 均衡 |

---

## 三、消费模型对比

| 维度 | Kafka | Pulsar |
|------|-------|--------|
| 并行消费 | 分区内单 Consumer（同 CG） | Shared / Key_Shared 多 Consumer |
| 顺序 | 分区内有序 | 分区内 / **Key 内**（Key_Shared） |
| 订阅类型 | 实质一种（CG） | Exclusive / Failover / Shared / Key_Shared |
| 回溯 | offset seek | Cursor seek + Retention |
| 多应用读同一 Topic | 多个 Consumer Group | 多个 **Subscription** |

**面试句：** Kafka 用不同 Consumer Group 实现多播；Pulsar 用不同 Subscription，模型更直观。

---

## 四、功能对照

| 能力 | Kafka | Pulsar |
|------|-------|--------|
| 消息保留 | retention.bytes/ms | Retention + TTL（独立） |
| 压缩 Topic | compact | Compaction（按 Key） |
| 事务 | 事务 API | Transaction API（开销大） |
| 延迟消息 | 有限/插件 | deliverAt / deliverAfter |
| Schema Registry | Confluent Schema Registry | **内置** Schema Registry |
| 多租户 | 命名规范 | Tenant / Namespace 一等公民 |
| MQTT | 需桥接 | 原生/扩展协议 |
| 流处理 | Kafka Streams / Flink | Pulsar Functions + Flink |

---

## 五、选型决策树

```
需要强多租户 + 同一 Topic 多套独立消费进度？
  ├─ 是 → 倾向 Pulsar
  └─ 否 → 继续

需要设备/用户级有序 + 多 Consumer 并行？
  ├─ 是 → Key_Shared + 分区（Pulsar 更贴切）
  └─ 否 → 两者皆可

团队 All-in Kafka 生态（Connect、Streams、运维经验）？
  ├─ 是 → 留 Kafka 或 KoP 渐进迁移
  └─ 否 → 可评估 Pulsar

需要原生跨机房 Geo？
  ├─ 是 → Pulsar 内置；Kafka 靠 MirrorMaker
  └─ 否 → 非决定性因素
```

| 选 Pulsar | 选 Kafka | 过渡 |
|-----------|----------|------|
| 多租户 SaaS | 深度 Kafka 栈 | **KoP** |
| 一 Topic 多独立订阅 | 无特殊需求 | 双写逐步切 |
| Key 有序 + 并行 | 团队不愿学 BK | |
| Geo / 分层存储 | | |

---

## 六、迁移注意（Kafka → Pulsar）

| Kafka 习惯 | Pulsar 调整 |
|------------|-------------|
| `my-topic` 短名 | 全名 + tenant/ns |
| consumer group = 服务名 | **subscriptionName** = 服务名 |
| 分区 = 并行度 | 分区 Topic 分区数规划 |
| offset 管理 | Cursor，注意 Subscription 勿混用 |
| 运维看 broker log dir | 看 **Bookie 磁盘** + backlog |

---

## 七、易错对照

1. 以为 Pulsar Subscription = Kafka Partition（错，Subscription 是消费进度线）。
2. 在 Pulsar 只建一个 Subscription 却跑多个不相关服务（应各建 Subscription）。
3. 用 Kafka 思维设 Retention「等消费完再删」——Pulsar Retention 独立。

---

## 相关章节

- [A1](../part-a-interview/A1-Pulsar是什么.md) | [A5](../part-a-interview/A5-订阅模式.md) | [C9](../part-c-ops/C9-升级迁移.md)
