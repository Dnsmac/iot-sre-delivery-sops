# A4 Topic 体系

> 优先级: **P1 面试** | 预计阅读 30 分钟 | 深度：批次 2 ✓

## 本章解决什么问题

Topic 是 Pulsar 的**核心资源对象**：类型选错会丢消息，分区选错会顶死吞吐，Compaction/Retention 混用会导致「消息怎么没了」。本章建立完整 Topic 心智模型。

---

## 面试常问

1. Persistent 和 Non-Persistent 区别？
2. 分区 Topic 和非分区 Topic 区别？分区数怎么定？
3. 分区能动态增加吗？能减少吗？
4. Compaction 是什么？和 Retention 区别？
5. 海量 Topic（十万级）会有什么问题？
6. 10W 设备要不要建 10W 个 Topic？

---

## 一、Topic 全路径与命名

```
persistent://{tenant}/{namespace}/{topic}
non-persistent://{tenant}/{namespace}/{topic}
```

| 前缀 | 含义 |
|------|------|
| `persistent://` | 消息写入 BookKeeper，Broker 重启不丢 |
| `non-persistent://` | 仅在 Broker 内存流转，适合可丢数据 |

**分区 Topic** 在逻辑上仍是一个 Topic 名，物理上展开为：

```
persistent://tenant/ns/my-topic-partition-0
persistent://tenant/ns/my-topic-partition-1
...
```

Client 通常只操作逻辑名 `persistent://tenant/ns/my-topic`，由 Client/Broker 路由到具体分区。

---

## 二、Topic 类型详解

### 2.1 Persistent（生产默认）

- 消息持久化到 BookKeeper，多副本。
- 配合 Retention、TTL、Compaction 策略（Namespace 级或 Topic 级）。
- **面试一句话：** 只要业务说「不能丢」，就用 Persistent。

### 2.2 Non-Persistent

- 不写入 BK；Broker 宕机、重启、过载可能丢消息。
- 延迟极低，适合 metrics、实时大屏旁路。
- **不能** 因为「想更快」就在核心业务上用 Non-Persistent。

### 2.3 Partitioned vs Non-Partitioned

| | Non-Partitioned | Partitioned |
|---|-----------------|-------------|
| 物理结构 | 1 个 Managed Ledger | N 个 Managed Ledger（每分区一个） |
| 写入并行 | 单流，吞吐有上限 | 多分区并行写 |
| 顺序 | 全局有序（单消费者时） | **分区内**有序；跨分区无序 |
| 扩展 Consumer | Exclusive/Failover 单活 | Shared/Key_Shared 可并行 |
| 创建 | `topics create` | `create-partitioned-topic -p N` |

**你们现状「默认创建、不分区」= Non-Partitioned：** 流量小时够用；接近日志峰值或 10W 设备上报聚合流量时，单分区 Ledger 成为瓶颈。

### 2.4 Compaction Topic（易混淆）

- **不是** 一种替代 Persistent 的类型，而是在 Persistent Topic 上开启 **Compaction 策略**。
- 机制：同一 **Message Key** 只保留**最新一条**（逻辑上），适合配置、状态快照、KV 语义。
- **与 Retention 关系：**
  - **Retention**：按时间/大小删**整段**历史，用于回溯、审计。
  - **Compaction**：在保留策略内，对同 Key **折叠**为最新值。
- 触发：Broker 后台 Compaction 任务；也可 `pulsar-admin topics compact`。

---

## 三、分区机制（面试高频）

### 3.1 生产者路由

| 路由 | 行为 | 场景 |
|------|------|------|
| **Round Robin** | 无 Key 时轮询各分区 | 均衡负载、无顺序 |
| **Key-based** | `hash(Key) % N` 固定分区 | 同 Key 进同分区 |
| 自定义 Router | 实现 `MessageRouter` | 特殊亲和 |

```java
producer.newMessage()
    .key("device-10086")   // 同 Key → 同分区（hash）
    .value(payload)
    .send();
```

**Key_Shared 消费** 要求 Producer **必须设 Key**，否则无法保证「同 ID 进同 Consumer」。

### 3.2 动态调整分区

```bash
# 只能增加
pulsar-admin topics update-partitioned-topic persistent://tenant/ns/topic -p 16
```

| 操作 | 是否支持 | 原因 |
|------|----------|------|
| **增加**分区 | ✅ | 新消息按新分区数路由；旧消息仍在旧分区 |
| **减少**分区 | ❌ | Hash 映射变化；数据迁移成本极高 |

**生产建议：** 初始按 **峰值 × 1.3~2** 估算，避免频繁扩容带来消费侧 rebalance 与运维噪音。

### 3.3 分区数估算（可背公式）

```
目标写入吞吐(MB/s) ÷ 单分区安全能力(5~10 MB/s) = 建议分区数（向上取整）

例1：10W 设备 × 1 条/10s × 512B ≈ 5 MB/s  → 1~2 分区
例2：10W 设备 × 1 条/s × 512B   ≈ 50 MB/s → 8~16 分区
```

单分区能力受 Bookie 磁盘、副本、消息大小影响，**必须以压测为准**。

### 3.4 海量 Topic 问题（≠ 海量设备）

| 问题 | 原因 |
|------|------|
| Metadata 压力大 | 每 Topic-Partition ≈ 1 Managed Ledger 元数据 |
| Lookup 变慢 | 路由、加载 Bundle 开销 |
| GC / Compaction 成本高 | Ledger 数量多 |
| 运维难 | 策略、监控、ACL 难统一 |

**正确做法（10W 设备）：**

```
❌ 10W 个 Topic（每设备一个）
✅ 少量 Topic（如 telemetry / command）+ MessageKey = deviceId + Key_Shared 消费
```

---

## 四、Namespace 策略（与 Topic 强相关）

在 Namespace 上配置（影响其下 Topic）：

| 策略 | 作用 |
|------|------|
| `retentionTime` / `retentionSize` | 消息保留多久/多大（可独立于消费） |
| `ttl` | 消息存活时间（未消费也会过期） |
| `backlogQuota` | 积压超限动作（丢弃/阻塞） |
| `schemaCompatibilityStrategy` | Schema 演进 |
| `compressionType` | LZ4/ZSTD 等 |

---

## 五、面试标准答案

### 题：Persistent 和 Non-Persistent 区别？

> Persistent 消息会写到 BookKeeper，多副本持久化，Broker 重启不丢，适合业务数据。Non-Persistent 只在 Broker 内存里转发，不落地，延迟低但可能丢，适合监控旁路。生产核心业务必须用 Persistent，并配置 Retention 和监控 backlog。

### 题：分区数怎么定？能减少吗？

> 分区数按目标写入吞吐除以单分区能力估算，一般每分区按 5 到 10 MB/s 留余量，并结合压测调整。分区只能增加不能减少，因为 Producer 按 Key 哈希到分区，减少会导致路由混乱和数据迁移。扩容分区后新消息走新分区，旧消息仍在旧分区，Consumer 会消费全部分区。

### 题：Compaction 和 Retention 区别？

> Retention 控制消息在集群里保留多久或多大，过期整段删除，用于审计和回溯。Compaction 是在保留策略内，对相同 Message Key 只保留最新一条，适合配置下发和状态快照。两者可以同时开：Retention 管生命周期，Compaction 管 Key 级别折叠。

---

## 六、生产注意点

- 生产禁用随意 Auto-Create；Topic 用脚本/IaC 预建（见 [B13](../part-b-java-dev/B13-推动策略改造.md)）。
- 分区 Topic 创建时写清 `-p`，避免事后扩容麻烦。
- 大消息开 Chunking，不是无限加大单条 Entry。
- 监控每个分区的 `msgRateIn` 是否均衡，防止 Key 热点单分区打满。

---

## 七、易错点

1. **10W Topic = 10W 设备** → 应少量 Topic + Key。
2. **非分区 + 多 Consumer + 要顺序** → 只有单活 Consumer 有序，或改 Key_Shared + 分区。
3. **以为 Compaction 等于删除历史** → 错；Retention 才管时间线删除。
4. **扩容分区后期望 Consumer 数任意加** → Key 分布和分区数仍约束并行度。

---

## 八、动手验证

```bash
# 创建 4 分区 Topic
docker exec pulsar-standalone bin/pulsar-admin topics create-partitioned-topic \
  persistent://dev/test/part-demo -p 4

# 查看分区
docker exec pulsar-standalone bin/pulsar-admin topics list dev/test

# 发到各分区（无 Key 时轮询）
# 带 Key 时观察始终进同一 partition-N
docker exec pulsar-standalone bin/pulsar-admin topics stats persistent://dev/test/part-demo
```

---

## 相关章节

- [A5 订阅](A5-订阅模式.md) | [B2 Producer](../part-b-java-dev/B2-生产者.md) | [B10 分区估算](../part-b-java-dev/B10-性能调优.md) | [B13 改造](../part-b-java-dev/B13-推动策略改造.md)
