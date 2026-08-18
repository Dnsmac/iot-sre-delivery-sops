# 附录 A：面试题索引与参考答案

> 深度：批次 2 ✓ | 每题 3~6 句，可背诵后用自己的话讲  
> 详见各章：[A1](../part-a-interview/A1-Pulsar是什么.md)~[A12](../part-a-interview/A12-性能与规模.md)

---

## 架构类（1~10）

### 1. Pulsar 架构是怎样的？Broker/Bookie/ZK 各做什么？

**参考答案：** Pulsar 分三层：Metadata Store（常见 ZooKeeper 或 Oxia）存 Topic、Bundle、订阅等元数据；Broker 负责连接、协议、路由和读缓存，不把消息持久化在本地磁盘，可水平扩展；BookKeeper 集群负责消息实体存储，通过 Journal 顺序写和 Ledger 只追加保证持久化。Producer 写消息时 Broker 并行写多个 Bookie，达到 quorum 后 ACK；Consumer 读时可能命中 Broker 缓存，否则读 Bookie，消费后更新 Cursor。

### 2. Broker 为什么说无状态？

**参考答案：** 无状态指 Broker 不在本地磁盘持久化消息内容，消息在 BookKeeper。Broker 重启可从元数据和 BK 恢复服务，已 ACK 写入的数据不丢。但 Broker 仍有连接表、缓存等运行时状态，不是「零状态」。扩展时加 Broker 即可，不必迁移磁盘上的分区数据，这是与 Kafka 的核心区别。

### 3. BookKeeper 和 Broker 什么关系？

**参考答案：** Broker 是计算层客户端面向的接入点；BookKeeper 是专用存储层。Broker 把每条消息写成 BK 的 Entry，存放在 Ledger 里，由 Ensemble 多副本复制。可以换 Broker 而不动数据，也可以独立扩展 Bookie。类比：Broker 像无状态 API 服务，BookKeeper 像背后的分布式日志存储。

### 4. Managed Ledger 是什么？

**参考答案：** Managed Ledger 是 Pulsar 在 BookKeeper 之上的抽象，一个 Topic 分区对应一个 Managed Ledger。它管理多个 Ledger 的滚动创建、写入、读取和删除策略，并对接 Cursor 的 MarkDelete。对开发者暴露为 Topic，内部才映射到 BK 的 Ledger 序列。

### 5. Bundle 是什么？做什么用？

**参考答案：** Bundle 是一组 Topic 的逻辑分组，是负载均衡的单位。运维可以将整个 Bundle 从一台 Broker unload 到另一台，用于扩缩容和热点迁移。避免按单 Topic 迁移过细导致元数据抖动。面试可补充：海量 Topic 时 Bundle 策略影响 Broker 间负载是否均衡。

### 6. 一条消息写入的完整路径？

**参考答案：** Producer 连接 Broker 发送消息；Broker 找到对应 Topic 分区的 Managed Ledger；将消息并行写入 BookKeeper Ensemble 的多个 Bookie；Journal 顺序落盘，Entry 进入 Ledger；当达到配置的 Write/Ack Quorum 后，Broker 向 Producer 返回发送成功 ACK。若开启 Batching，在 Broker 或 Client 侧可能合并多条再写。

### 7. 一条消息读取的完整路径？

**参考答案：** Consumer 向 Broker 发起读取；Broker 查 Managed Ledger 读缓存，命中则直接返回，未命中则从 Bookie 拉取 Entry；消息交给 Consumer 处理；Consumer ACK 后 Broker 更新该 Subscription 的 Cursor（MarkDelete）；超过 Retention 或 Compaction 策略的旧 Entry 可被后台清理。

### 8. E-Q-W 是什么？3:3:2 什么意思？

**参考答案：** E-Q-W 是 BookKeeper 的 Ensemble Size、Write Quorum、Ack Quorum。3:3:2 表示写副本数为 3，至少 3 路写入成功，其中 2 路确认即可向上一层返回成功（具体以配置为准）。用于在可靠性和延迟之间折中。面试要说「副本和确认数可配置，不是固定 3:3:2」。

### 9. Journal 和 Ledger 区别？

**参考答案：** Journal 是 Bookie 上的预写日志，顺序写、通常放 SSD，保证持久化和恢复。Ledger 是只追加的 Entry 序列，存储实际消息数据，可达到很大容量。写入时先写 Journal 再组织进 Ledger。Journal 保护崩溃恢复，Ledger 是长期存储单元。

### 10. Metadata Store 用什么？ZK 和 Oxia 区别？

**参考答案：** 传统 Pulsar 用 ZooKeeper 存元数据和部分协调信息。Pulsar 3.x 方向是 Oxia 等替代，目标降低 ZK 运维成本、提高扩展性。对应用透明，主要影响部署架构。面试说「了解 ZK，知道团队在去 ZK 化即可」。

---

## 对比类（11~15）

### 11. Pulsar 和 Kafka 核心区别？

**参考答案：** 架构上 Pulsar 存储计算分离（Broker+BookKeeper），Kafka 日志在 Broker 本地。消费模型上 Pulsar 多 Subscription 独立 Cursor，Kafka 以 Consumer Group Offset 为主。Pulsar 原生多租户、Geo-Replication、多订阅模式（含 Key_Shared）。Kafka 生态更成熟。选型：要强多租户、多消费组独立进度、统一队列流，偏 Pulsar；纯 Kafka 生态且团队熟悉，可继续 Kafka 或用 KoP。

### 12. Pulsar 和 RocketMQ 区别？

**参考答案：** 两者都支持多种消费语义，RocketMQ 国内生态强、顺序消息、事务成熟。Pulsar 底层是 BookKeeper，存储扩展和跨机房复制模型不同，订阅模式更丰富（Key_Shared 等），多租户原生。RocketMQ 运维组件多已国产化文档丰富；Pulsar 适合已统一用 BK、需要与 Flink/Pulsar Functions 深度结合的场景。

### 13. 什么场景选 Pulsar 不选 Kafka？

**参考答案：** 需要强多租户隔离；同一 Topic 多套独立消费进度；设备/用户级有序且要并行（Key_Shared）；跨机房多活复制要原生方案；希望计算层无状态快速扩 Broker。若团队只有 Kafka 经验且无上述强需求，迁移成本需权衡，可用 KoP 过渡。

### 14. Cursor 和 Kafka Offset 区别？

**参考答案：** Cursor 绑定在 Subscription 上，每个订阅各自维护消费位置（MarkDelete 点）。Kafka Offset 绑定 Consumer Group 与 Partition。Pulsar 同一 Topic 上多个 Subscription 互不影响；Kafka 多 Group 各自 offset。Pulsar 还可 Seek 到 MessageId。语义类似「消费进度」，绑定粒度不同。

### 15. Key_Shared 和 Kafka Consumer Group 区别？

**参考答案：** Kafka 以 Partition 为并行和有序边界，一个 Partition 同一时刻通常给一个 Consumer。Pulsar Key_Shared 以 Message Key 为边界，同 Key 进同一 Consumer，与分区数有关但模型更灵活。Partition 数决定写并行；Key_Shared 在读侧按 Key 分配。 rebalance 时两者都可能短暂重复或乱序，都要幂等。

---

## Topic 类（16~20）→ 详见 [A4](../part-a-interview/A4-Topic体系.md)

### 16. Persistent 和 Non-Persistent 区别？

**参考答案：** Persistent 消息写入 BookKeeper，持久化，Broker 重启不丢，生产默认。Non-Persistent 只在 Broker 内存转发，可能丢，适合可丢的实时指标。选错会导致核心业务丢消息。看 URL 前缀 `persistent://` vs `non-persistent://`。

### 17. 分区 Topic 和非分区 Topic 区别？

**参考答案：** 非分区只有一个 Managed Ledger，写入串行，吞吐有上限，适合低频强顺序。分区 Topic 有 N 个 Ledger，写入可并行，分区内有序、全局无序，适合高吞吐。Consumer 并行能力在分区 Topic 上更好。你们「不分区」= 非分区模型。

### 18. 分区数怎么定？能动态改吗？

**参考答案：** 按目标吞吐除以单分区能力（约 5~10 MB/s）估算，压测校准。可以动态**增加**分区：`update-partitioned-topic -p N`。**不能减少**，因为 Hash 路由和存量数据迁移复杂。宜预留 30%~100% 余量。

### 19. Compaction 是什么？和 Retention 区别？

**参考答案：** Compaction 对相同 Message Key 只保留最新一条，适合配置/状态类 Topic。Retention 按时间或大小删除历史消息，与是否消费无关。Compaction 不替代 Retention；两者可同时配置。Compaction 触发 compact 任务，不是实时删旧 Key 的每一条历史。

### 20. 海量 Topic 有什么问题？

**参考答案：** 每个 Topic-分区对应 Managed Ledger，元数据、Lookup、GC 压力增大。十万 Topic 会导致 Broker 和元数据服务吃力。正确做法是少量 Topic + Message Key 区分设备/业务，而不是每设备一个 Topic。与「10W 连接」不同，Topic 数是命名空间资源问题。

---

## 订阅与消费（21~28）

### 21. 四种订阅模式分别什么场景？

**参考答案：** Exclusive 单 Consumer，强顺序。Failover 主备单活，容灾。Shared 多 Consumer 并行、无序，吞吐最高。Key_Shared 多 Consumer、同 Key 有序，订单/设备场景常用。选错 Shared 会导致要顺序的业务乱序。

### 22. Exclusive 和 Failover 区别？

**参考答案：** 都保证同一时刻只有一个 active Consumer。Exclusive 第二个连不上；Failover 多个 standby，主挂切换。Failover 适合 HA；Exclusive 适合明确只要一个实例。切换时 Failover 有短暂停顿，可能重复投递要幂等。

### 23. Shared 为什么无序？

**参考答案：** Shared 把消息轮询或随机分给多个 Consumer，不维护 Key 亲和，所以全局无序。提高并行度。若业务要同 Key 顺序，必须用 Key_Shared 并发送时带 Key。

### 24. Key_Shared 的 AUTO_SPLIT 和 STICKY 区别？

**参考答案：** AUTO_SPLIT 由 Broker 自动分配 Key 范围给 Consumer，扩缩容时 rebalance 积极。STICKY 尽量让 Key 粘性绑定 Consumer，减少迁移时乱序窗口。高 Key 基数用 AUTO_SPLIT；要稳定亲和用 STICKY。 rebalance 期间都可能短暂乱序。

### 25. At least once 怎么实现？重复消费怎么办？

**参考答案：** 默认 Consumer 处理完再 ACK，处理前崩溃则 Broker 重投，即至少一次。重复靠业务幂等：数据库唯一键、Redis 去重、messageId 记录。还可调 ackTimeout 避免处理中被误判超时。不能单靠 Broker 消灭重复（除非 Transaction）。

### 26. Exactly once 怎么实现？

**参考答案：** 使用 Pulsar Transaction：跨 Topic 原子提交，性能开销大，一般用于金融级跨 Topic 场景。单 Topic 大多数用 at-least-once + 幂等。Kafka 的 EOS 类似要事务 + 合作存储；Pulsar 有原生 Transaction API 但运维和调优成本高。

### 27. 单条 ACK 和累积 ACK 区别？

**参考答案：** 单条 ACK 只确认当前 MessageId，精确，开销大。累积 ACK 确认该 Id 及之前全部，吞吐高，但若中间某条实际处理失败会导致一批重投。高吞吐且可幂等可用累积；不能重复必须用单条。

### 28. Cursor 存在哪？

**参考答案：** Cursor 逻辑上属于 Subscription，元数据在 Metadata Store，持久化状态与 BookKeeper 中 MarkDelete 位置关联。每个 Subscription 独立，所以多服务消费同一 Topic 互不影响进度。

---

## 保留与清理（29~31）

### 29. TTL 和 Retention 区别？

**参考答案：** TTL 是消息存活时间，到期可删，不管是否被消费。Retention 是集群保留策略，即使已 ACK 也可保留一段时间供回溯。TTL 管「活多久」；Retention 管「删不删已消费的历史」。都在 Namespace 可配。

### 30. Backlog Quota 是什么？

**参考答案：** 当 Subscription 积压超过阈值（大小或时间），触发策略：丢弃旧消息、阻塞生产者或告警。防止磁盘被慢消费者拖垮。生产应对核心 Topic 配置并监控 backlog。

### 31. Compaction 触发条件？

**参考答案：** Namespace/Topic 开启 compaction 策略后，Broker 后台扫描或手动 `topics compact`。对带 Key 的消息折叠为最新值。需要 Retention 仍保留足够窗口供 compact 读取历史。无 Key 的消息 compact 意义不大。

---

## 异常处理（32~34）

### 32. 消费失败怎么处理？

**参考答案：** 处理失败可不 ACK 或 negativeAcknowledge，触发 redelivery。配置 ackTimeout 自动重投。超过 maxRedeliverCount 进入 Retry Topic 或 Dead Letter Queue。DLQ 消息需人工或工具回放。业务必须幂等。

### 33. DLQ 是什么？怎么用？

**参考答案：** Dead Letter Queue 是失败消息的独立 Topic，保存无法再重试成功的消息。配置 deadLetterPolicy 指定 DLQ 名和最大重试次数。运维可 peek、分析、修复后重新发送。避免毒消息阻塞主队列。

### 34. Retry Topic 机制？

**参考答案：** 开启 deadLetterPolicy 后，Broker 自动创建 retry 和 DLQ 相关 Topic，失败消息先进入 retry 延迟重投，阶梯延迟可配。仍失败则进 DLQ。对业务透明，但 Topic 数量会增加，需治理命名。

---

## Schema（35~36）

### 35. Schema Registry 做什么？

**参考答案：** Pulsar 内置 Schema 存储与兼容性检查，Producer/Consumer 注册 Schema 版本。反序列化时校验，不兼容则拒绝，避免脏数据。支持 Avro、JSON、Protobuf 等。多服务应共用 Schema 定义（如 Maven 模块）。

### 36. Schema 兼容策略有哪些？

**参考答案：** ALWAYS 不检查；BACKWARD 新 Schema 可读旧数据（先升 Consumer）；FORWARD 旧 Consumer 可读新数据；FULL 双向。常用 BACKWARD：先部署能读新格式的 Consumer，再部署发新格式的 Producer。

---

## 高级特性（37~43）

### 37. Transaction 原理？

**参考答案：** Transaction 将一批消息写入 Transaction Log，提交时原子更新各 Topic 的可见性和 ACK 状态，失败则回滚。用于跨 Topic exactly-once。涉及 Transaction Coordinator 和额外存储开销，适合关键金融链路，不适合极高吞吐全链路。

### 38. Delayed Message 怎么做？

**参考答案：** Producer 设置 deliverAt 时间戳或 deliverAfter 延迟，Broker 到点再投递。内部有定时调度机制。适合订单超时取消、延迟通知。注意时钟和集群负载，大量延迟消息要压测。

### 39. Deduplication 原理？

**参考答案：** Broker 端为 Producer 维护近期 sequenceId 窗口，重复 sequence 的 PUBLISH 会被丢弃。需在 Broker 和 Producer 同时开启，Producer 必须为每条消息设递增 sequenceId。适合防止网络重试导致重复发，不替代 Consumer 幂等。

### 40. Geo-Replication 原理和限制？

**参考答案：** 跨集群异步复制 Topic 数据，各集群可本地生产消费。最终一致，有延迟。冲突解决依赖策略（通常最后写入或业务层）。适合灾备和多活读，不适合强一致跨区写。要评估带宽和延迟。

### 41. Tiered Storage 原理？

**参考答案：** 旧 Ledger _OFFLOAD 到 S3/GCS 等对象存储，Bookie 只留热数据。降低磁盘成本。读取冷数据延迟升高。适合历史回溯少、保留时间长的 Topic。需配置触发条件和对象存储权限。

### 42. Pulsar Functions 和 Flink 区别？

**参考答案：** Pulsar Functions 是轻量 per-message 无状态/简单状态计算，部署在 Pulsar 生态内，适合过滤、转换、路由。Flink 是重型流计算，有窗口、状态、Checkpoint，适合复杂实时分析。二者可组合：Functions 预处理 + Flink 聚合。

### 43. KoP 是什么？

**参考答案：** Kafka-on-Pulsar，在 Pulsar 上提供 Kafka 协议兼容层，Kafka 客户端可连 Pulsar。用于 Kafka 迁移平滑过渡。不是 100% 覆盖所有 Kafka 特性，需测试验证。长期可统一到 Pulsar 运维，短期降低迁移成本。

---

## 性能（44~48）

### 44. Pulsar 性能瓶颈在哪？

**参考答案：** 写入常见瓶颈在 Bookie Journal 磁盘 IO 和副本确认延迟。读取在 Broker Cache 命中率和 Bookie 读 IO。海量 Topic 时元数据和 Lookup 也是瓶颈。Client 侧未开 Batching、分区过少也会导致「应用层觉得慢」。

### 45. 怎么提高吞吐？

**参考答案：** 架构层增加分区、合理 Key；Client 开 Batching 和 LZ4 压缩；增加 Consumer 实例（Shared/Key_Shared）；扩展 Bookie 和 Broker；Bookie 用 SSD Journal。按金字塔从 L0 到 L5 逐层调，先 Client 再集群。

### 46. Batching 原理和延迟权衡？

**参考答案：** Producer 将多条消息合并成一个请求发送，减少网络和 Broker 处理次数。batchingMaxPublishDelay 越大，凑批越多，吞吐越高，但单条 P99 延迟增加。延迟敏感调小 delay 或减小 batch 大小；吞吐优先调大。

### 47. 海量连接怎么处理？

**参考答案：** 使用 Pulsar Proxy 终结 TCP 连接，Broker 专注消息。Proxy 可水平扩展。调连接超时和心跳。10W 设备场景还要 Topic/分区/QoS（若 MQTT 接入）统一规划。Standalone 不能压连接数上限。

### 48. Standalone 和 Cluster 区别？

**参考答案：** Standalone 单进程 all-in-one，开发测试用，不能代表生产性能和 HA。Cluster 分离 Broker、Bookie、元数据，可扩缩容、容错。性能压测、Failover、Geo 必须在 Cluster 上做。上线前对照 [B12](../part-b-java-dev/B12-环境模型.md) 迁移清单。

---

## 多租户（49~50）

### 49. Tenant/Namespace/Topic 关系？

**参考答案：** Tenant 是顶层租户，Namespace 是策略和配额单元（Retention、ACL、Schema 等），Topic 是消息通道，全路径 `persistent://tenant/namespace/topic`。类似「公司/部门/项目队列」。隔离和计费常按 Tenant/Namespace 做。

### 50. 多租户怎么隔离？

**参考答案：** 逻辑隔离靠 Tenant/Namespace 权限和配额；物理隔离可用 Isolation Policy 将 Bundle 绑定到指定 Broker/Bookie 集合。策略在 Namespace 级配置。不是默认每租户独立机器，需显式配置隔离策略。

---

## 使用建议

- 面试前：按类每天 10 题，**遮住答案自讲**
- 结合你们项目：每题补一句「我们目前是 Shared + 非分区…」
- 深化章节：[A2](../part-a-interview/A2-核心架构.md) [A4](../part-a-interview/A4-Topic体系.md) [A5](../part-a-interview/A5-订阅模式.md) [B13](../part-b-java-dev/B13-推动策略改造.md)
