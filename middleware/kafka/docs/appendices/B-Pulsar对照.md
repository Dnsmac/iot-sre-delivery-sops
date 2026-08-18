# 附录 B：Pulsar ↔ Kafka 对照表

> 深度：面试 P1 | 与 [pulsar/附录 B](../../pulsar/docs/appendices/B-Kafka对照.md) **互为镜像**  
> 现网口径：设备 MQTT → **EventBus**；中间件若用 **Pulsar**，本表用于 **JD 写 Kafka 时的 30 秒防御**

---

## 一、概念映射（速查）

| Pulsar 概念 | Kafka 概念 | 差异要点 |
|-------------|------------|----------|
| Cluster | Cluster | 类似 |
| `persistent://tenant/ns/topic` | Topic 名（常 `cluster.topic` 或纯名） | Kafka 无 Tenant/NS 一等公民 |
| Partition（分区 Topic） | **Partition** | Pulsar 还有**非分区** Topic |
| **Subscription** | **Consumer Group** | 名称不同；都是「消费进度线」 |
| **Cursor** | **Offset**（按 partition） | 存在 Group 上 |
| 第二个消费方 | 第二个 **Consumer Group** | Kafka 需换 group.id |
| BookKeeper Ledger | **Broker 分区日志** | Pulsar 存算分离 |
| Retention + TTL | `retention.ms` / `retention.bytes` | Kafka retention 与消费进度耦合更紧 |
| Geo-Replication | MirrorMaker / Cluster Link | |
| 内置 Schema Registry | Confluent Schema Registry 等 | |
| Key_Shared | **同 Key → 同分区** + 单分区内顺序 | 实现方式不同，目标类似 |
| Shared | 同 CG 多 Consumer 抢分区 | |
| Exclusive / Failover | 较少用；可用单 Consumer 或自定义 | |
| Backlog / msgBacklog | **Consumer Lag** | 排查思维一致 |
| KoP（Kafka 协议进 Pulsar） | 原生 Kafka 协议 | |

---

## 二、架构对比

```
Pulsar: Producer → Broker(无状态) → BookKeeper → Consumer
                扩 Broker 不搬消息体

Kafka:  Producer → Broker(分区日志本地盘) → Consumer
                扩 Broker 常伴随分区再均衡
```

| 维度 | Pulsar | Kafka |
|------|--------|-------|
| 存储 | BookKeeper | Broker 本地 log |
| Broker 角色 | 接入路由 | 接入 + **存储** |
| 元数据 | ZK / Oxia | **KRaft**（新）/ ZK（旧） |
| 运维重心 | Bookie 磁盘、Bundle | 分区再均衡、Broker 磁盘 |

---

## 三、消费模型对比

| 维度 | Pulsar | Kafka |
|------|--------|-------|
| 进度单位 | Subscription + Cursor | Consumer Group + Offset |
| 同 Topic 多应用 | 多 **Subscription** | 多 **Consumer Group** |
| 有序 + 并行 | **Key_Shared** | Key → Partition；分区内 1 Consumer（同 CG） |
| Rebalance | 订阅级 consumer 变化 | **Consumer Group Rebalance** |
| 回溯 | Cursor seek | offset seek |

**面试句（现网 Pulsar）：**

> 我们 Pulsar 上一个 Topic 多个 Subscription 互不影响；换 Kafka 就要多个 Consumer Group。设备有序我们 Pulsar 用 Key_Shared，Kafka 侧等价是 **固定 Key 哈希到分区**。

---

## 四、IoT / 现网口述模板

| 问 | 答 |
|----|-----|
| 你们用 Kafka 吗？ | 设备上报主链路是 **EventBus + ES/MySQL**；集群里消息中间件是 **Pulsar**。Kafka 概念我学过，**积压看 lag、至少一次要幂等、有序靠分区 Key**，和 Pulsar backlog / Key_Shared 可对照。 |
| 为什么不用 Kafka？ | （如实）历史选型 / 团队栈 / 多订阅模型；**不贬低现网**。 |
| Pulsar 积压怎么查？ | backlog、msgRateIn/Out → 对应 Kafka 的 **lag、end offset - committed offset**。 |

---

## 五、排查对照（Part D 互链）

| 现象 | Pulsar 文档 | Kafka 文档 |
|------|-------------|--------------|
| 积压 | [pulsar P4](../../pulsar/docs/part-d-problems/P4-积压.md) | [P4 积压](../part-d-problems/P4-积压.md) |
| 重复消费 | pulsar P2 | [P2](part-d-problems/P2-重复消费.md) |
| 消息丢失 | pulsar P1 | [P1](part-d-problems/P1-消息丢失.md) |
| 乱序 | pulsar P3 | [P3](part-d-problems/P3-消息乱序.md) |

---

## 六、易错对照

1. 以为 Kafka **Partition** = Pulsar **Subscription**（错：Partition 对应 Pulsar 的 **分区**；Subscription ≈ **Consumer Group**）。
2. 在 Kafka 多个无关服务共用一个 **group.id**（进度打架）。
3. 以为消费完才删日志——Kafka **retention** 按时间/大小删，与是否消费到无关（compact topic 除外）。

---

## 相关章节

- [A1](../part-a-interview/A1-Kafka是什么.md) | [A5](../part-a-interview/A5-ConsumerGroup与Offset.md) | [B13](../part-b-java-dev/B13-推动Pulsar对照.md)
