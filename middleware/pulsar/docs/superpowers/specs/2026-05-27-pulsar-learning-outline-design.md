# Apache Pulsar 完整学习大纲 — 设计文档 v0.6

> 创建日期：2026-05-27  
> 状态：已确认  
> 技术栈：Java 为主，多服务、大数据量场景  
> 学习优先级：**面试 P1 → 开发 P2 → 扩展 P3**

---

## 1. 目标与原则

### 1.1 目标

构建 Apache Pulsar 完整知识体系，服务于：

1. **面试（P1）**：能讲清原理、画架构图、对比 Kafka、回答高频题
2. **开发（P2）**：Java 多服务日常开发、排障、性能调优（含影响排序）
3. **扩展（P3）**：部署运维、压测实战、源码（有余力再学）

### 1.2 设计原则

| 原则 | 说明 |
|------|------|
| 知识体系完整 | 知识点不删，按优先级分层呈现 |
| 面试第一 | 每章标注面试问法，附录 50+ 题索引 |
| 开发 = 写代码 + 排障 + 调优 | 三者同在 Part B，不拆散 |
| 环境正交 | Standalone / Cluster / K8s 差异独立成章（B12） |
| 问题可索引 | Part D 问题百科 + 附录反向链接 |
| 实战项目后置 | 10W 设备压测等综合项目放 Part C，不压缩知识体系 |

### 1.3 学习路径

```
Week 1-2   Part A 全部（面试核心）→ 刷附录 A 面试题
Week 3-5   Part B 全部（Java 开发 + 排障 + 调优 + 环境差异）
Week 6+    Part C 按需（扩展）
全阶段     Part D + 附录 随时查阅
```

---

## 2. 知识体系结构

```
                    ┌─────────────────────┐
                    │  附录：面试题索引     │
                    └──────────┬──────────┘
                               │
┌──────────────┬───────────────┼───────────────┬──────────────┐
│  Part A      │  Part B       │  Part C       │  Part D      │
│  面试核心 P1  │  Java开发 P2  │  架构扩展 P3  │  问题百科     │
└──────────────┴───────────────┴───────────────┴──────────────┘
```

---

## 3. Part A：面试核心（P1）

> 目标：Pulsar 面试题能讲清原理、对比 Kafka、画架构图。

### A1. Pulsar 是什么 & 为什么存在

**面试常问：**
- Pulsar 和 Kafka 有什么区别？什么场景选 Pulsar？
- Pulsar 的核心设计思想是什么？

**必答对比表：**

| 维度 | Pulsar | Kafka |
|------|--------|-------|
| 架构 | 存储计算分离（Broker + BookKeeper） | 存储计算一体 |
| 消费模型 | 多订阅独立 Cursor | Consumer Group Offset |
| 消息保留 | Retention 独立于消费进度 | 取决于 Consumer Group |
| 多租户 | 原生 Tenant/Namespace | 弱 |
| 订阅模式 | 4 种 | 主要是 Consumer Group |
| Geo 复制 | 原生 | MirrorMaker |
| 协议扩展 | MQTT/AMQP/KoP | 仅 Kafka 协议 |

---

### A2. 核心架构（最高频画图题）

**面试常问：**
- 说说 Pulsar 架构？Broker 为什么说无状态？
- BookKeeper 是什么？Managed Ledger 是什么？
- 一条消息从 Producer 到 Consumer 经历了什么？

**必答架构：**

```
                    ┌────────── Metadata Store (ZK/Oxia) ──────────┐
                    │  Topic / Bundle / Cursor 元数据              │
                    └──────────────────────────────────────────────┘
                                          │
    Producer ──→ Broker (无状态) ──→ BookKeeper Cluster (有状态)
                    │    ↑                    │
                    │    │  Journal + Ledger  │
                    │    └────────────────────┘
                    ↓
               Consumer (ACK → Cursor MarkDelete)
```

**组件一句话：**

| 组件 | 职责 | 面试关键词 |
|------|------|-----------|
| Broker | 连接、路由、协议、读缓存 | **无状态**（不持久化消息） |
| BookKeeper | Journal + Ledger 多副本存储 | **E-Q-W** |
| Metadata Store | Topic/Bundle/Cursor 元数据 | ZK → Oxia 演进 |
| Managed Ledger | Topic 在 BK 上的抽象 | 1 Topic-Partition ≈ 1 Managed Ledger |
| Bundle | Topic 逻辑分组 | 负载均衡基本单元 |
| Proxy | 连接接入代理 | 大规模连接（10W+） |

**写入路径：** Producer → Broker → 并行写 BK Ensemble (E-Q-W) → ack quorum → Producer ACK

**读取路径：** Consumer → Broker (Cache?) → Bookie Read → ACK → Cursor MarkDelete

---

### A3. 逻辑层级 & 多租户

- 全路径：`persistent://tenant/namespace/topic`
- Tenant = 组织；Namespace = 策略单元；Topic = 消息通道
- 隔离：Namespace 策略 + Isolation Policy

---

### A4. Topic 体系

| 类型 | 特点 | 一句话 |
|------|------|--------|
| Persistent | 落盘 | 生产默认 |
| Non-Persistent | 内存 | 容忍丢失 |
| Partitioned | N 分区并行 | 高吞吐 |
| Non-Partitioned | 单 Ledger 有序 | 吞吐受限 |
| Compaction | Key 级保留最新 | 配置同步 |

- 分区只能增不能减；过多分区 → 元数据/GC 压力
- 路由：RoundRobin / KeyBased

---

### A5. 四种订阅模式（最高频）

| 模式 | Active Consumer | 顺序 | 吞吐 | 场景 |
|------|----------------|------|------|------|
| Exclusive | 1 | 分区内有序 | 低 | 单实例任务 |
| Failover | 1（N standby） | 分区内有序 | 低 | 主备 HA |
| Shared | 全部 | **无序** | 最高 | 并行计算 |
| Key_Shared | 全部 | **Key 内有序** | 高 | 设备/用户级有序 |

- Key_Shared：`AUTO_SPLIT` / `STICKY`
- vs Kafka：Kafka Partition 绑定 Consumer；Pulsar Key 绑定 Consumer

---

### A6. 消息投递语义 & ACK

| 语义 | 实现 | 场景 |
|------|------|------|
| At most once | 先 ACK 再处理 | 日志旁路 |
| At least once | 处理完再 ACK（默认） | **生产最常用** |
| Exactly once | Transaction | 跨 Topic 原子 |

- 单条 ACK：精确，开销大
- 累积 ACK：吞吐高，一条失败 = 一批重投
- Cursor vs Kafka Offset：每 Subscription 独立 Cursor

---

### A7. 消息保留 & 清理

| 策略 | 触发 | 一句话 |
|------|------|--------|
| TTL | 消息存活时间 | 消息活多久 |
| Retention | 保留策略 | 能不能回溯 |
| Compaction | Key 重复 | KV 快照 |
| Backlog Quota | 积压超限 | 消费太慢怎么办 |

---

### A8. 异常处理：Retry & DLQ

```
消费失败 → NACK/超时 → Redelivery → maxRedeliverCount
        → Retry Topic → 仍失败 → DLQ → 人工介入
```

---

### A9. Schema 体系

- 类型：None / String / JSON / AVRO / Protobuf
- 兼容：ALWAYS / BACKWARD / FORWARD / FULL

---

### A10. 高级特性（加分项）

| 特性 | 核心答法 |
|------|---------|
| Transaction | Transaction Log + ACK 原子提交 |
| Delayed Message | deliverAt / deliverAfter |
| Deduplication | sequenceId + Broker 去重窗口 |
| Geo-Replication | 异步复制，最终一致 |
| Tiered Storage | 热 BK + 冷 S3/GCS |
| Pulsar Functions | 轻量单消息处理 |
| KoP | Kafka 协议兼容层 |

---

### A11. BookKeeper 深入

- E-Q-W：Ensemble : Write Quorum : Ack Quorum（如 3:3:2）
- Journal：预写日志，SSD 顺序写
- Ledger：只追加不可变，Entry 是最小单元
- Managed Ledger 滚动 → 新 Ledger → 旧的可 Offload/GC

---

### A12. 性能 & 海量数据

- 写入瓶颈 → Bookie Journal IO
- 读取瓶颈 → Broker Cache / Bookie Read
- 提吞吐 → Batching + 压缩 + 分区 + Bookie
- 海量 Topic → 合并 Topic + Key 路由
- 大量连接 → Pulsar Proxy

---

## 4. Part B：Java 开发实战（P2）

> 目标：多服务、大数据量下能写代码、排障、调性能。  
> P2 = 写代码 + 解决问题 + 性能调优

### B1. Java Client 基础

```xml
<dependency>
  <groupId>org.apache.pulsar</groupId>
  <artifactId>pulsar-client</artifactId>
</dependency>
```

- 一个 JVM 一个 `PulsarClient`，多 Producer/Consumer 共享

### B2. Producer 开发

- 同步 `send()` vs 异步 `sendAsync()` + Callback（高吞吐必用）
- Batching + 压缩 + Key 路由 + Typed Producer（Schema）
- 详见 B10 L1

### B3. Consumer 开发

- MessageListener 模式（推荐）
- 四种订阅模式选型
- ACK / NACK / DLQ / Retry 配置
- Key_Shared 策略选择

### B4. 多服务协作规范

- Topic 命名：`persistent://{tenant}/{namespace}/{service}-{action}`
- 订阅名 = 服务名
- 多服务独立 Subscription，各自 Cursor
- Schema 协作：公共 Maven 模块 + CI 兼容性检查

### B5. 大数据量 Java 注意点

| 场景 | 配置 |
|------|------|
| 小消息高吞吐 | Batching + LZ4 |
| 大消息 | chunkingEnabled |
| 消费慢 | receiverQueueSize + 扩容 |
| 长任务 | 调大 ackTimeout |
| 背压 | blockIfQueueFull=true |
| 幂等 | 业务层设计 |

### B6. 本地开发（Standalone）

```bash
bin/pulsar standalone
# Broker: localhost:6650  Admin: localhost:8080
```

- 常用：`topics stats` / `peek-messages` / `unsubscribe`
- Testcontainers Embedded Pulsar 做单元测试

### B7. Spring 集成

- Spring Boot 3.2+ `@PulsarListener`
- 配置外置：`spring.pulsar.client.service-url`

### B8. 配置管理

- dev / staging / prod 多环境 YAML
- 生产：关闭 Auto-Create，Topic/Schema 预创建

---

### B9. 开发中解决问题

#### B9.1 排查方法论（五步）

```
确认现象 → 划界（Producer/Broker/Consumer） → 拿证据 → 缩小范围 → 验证修复
```

#### B9.2 诊断工具

| 工具 | 用途 |
|------|------|
| `topics stats` | rate_in/out、backlog |
| `topics stats-internal` | Cursor、Ledger 详情 |
| `peek-messages` | 确认消息内容 |
| `unsubscribe` | 重置订阅 |
| `consumer.seek()` | 回放 |
| jstack | 线程卡死 |
| Grafana | 趋势监控 |

#### B9.3 场景手册（12 场景）

| # | 场景 | 高频原因 | 解决 |
|---|------|---------|------|
| 1 | 发送了收不到 | 异步没处理异常 / 订阅名错 / TTL 过期 | exceptionally + 核对 subscription |
| 2 | 重复消费 | ackTimeout 太短 / 崩溃重启 | 调 timeout + 幂等 |
| 3 | 消息乱序 | 用了 Shared | 改 Key_Shared |
| 4 | Backlog 积压 | Consumer 慢 / 实例不够 | 优化逻辑 + 扩容 |
| 5 | 性能突然下降 | 集群/配置/消息大小变化 | → B10 决策树 |
| 6 | 连接频繁断开 | LB 超时 / Broker OOM | keepAlive + 共享 Client |
| 7 | Schema 报错 | 不兼容 | 走演进流程 |
| 8 | OOM | 队列/预取太大 | blockIfQueueFull + 减小 receiverQueueSize |
| 9 | 本地 OK 集群不行 | Tenant 不存在 / Auto-Create 关 / 权限 | → B12.4 清单 |
| 10 | Cluster 有时收不到 | Bundle 迁移 / Broker 切换 | Client 自动重连 |
| 11 | 集群性能低于预期 | Standalone 没开 Batching | 开发时就按 Cluster 配置 |
| 12 | Failover 不生效 | Standalone 只有 1 Broker | 必须 Cluster 验证 |

---

### B10. 性能调优

#### B10.1 调优金字塔（影响排序）

```
L0 架构设计（Topic/分区/模式）     ★★★★★  影响最大
L1 Client Batching + 压缩          ★★★★★  小消息场景
L2 并发度（分区 × Consumer）        ★★★★
L3 Client 参数（队列/超时/预取）    ★★★
L4 Broker/Bookie 配置              ★★    需运维
L5 基础设施（磁盘/网络/内存）       ★★    需运维
```

#### B10.2 L0 架构设计

| 决策 | 错误 | 正确 |
|------|------|------|
| Topic 数量 | 10W Topic | 少量 Topic + Key |
| 分区数 | 1 分区 | 按吞吐算：每分区 ~5-10MB/s |
| 订阅模式 | 有序用 Shared | Key_Shared |
| 消息大小 | 10MB 单条 | <1MB 或 Chunking |

**分区数估算：**
```
分区数 = 目标吞吐(MB/s) / 每分区能力(5-10 MB/s)
例：10W设备 × 1msg/10s × 512B = 5MB/s → 1-2 分区
    10W设备 × 1msg/s × 512B = 50MB/s → 8-16 分区
```

#### B10.3 L1 Batching + 压缩

| 参数 | 推荐 | 影响 |
|------|------|------|
| batchingEnabled | true | 不开吞吐差 5-20 倍 |
| batchingMaxPublishDelay | 10-50ms | 越大吞吐越高、延迟越高 |
| compressionType | LZ4 | 带宽减 50-80% |

#### B10.4 L2 并发度

- 分区数：创建时定，只能增
- Consumer 实例：Shared 无上限；Key_Shared ≤ 分区数
- 8 分区 + 4 Consumer ✅ / 2 分区 + 4 Consumer ❌

#### B10.5 L3 Client 参数

**Producer：** maxPendingMessages(500-2000) / blockIfQueueFull(true) / sendTimeout(30s)

**Consumer：** receiverQueueSize(开发100/生产1000) / ackTimeout(P99×3) / poolMessages(高吞吐开)

**ACK 选择：** 不能重复 → 单条 ACK；高吞吐+可幂等 → 累积 ACK

#### B10.6 L4 升级信号（找运维）

| 信号 | 运维动作 |
|------|---------|
| ADD_ENTRY P99 > 10ms | Journal 换 SSD / 加 Bookie |
| Broker CPU > 80% | 加 Broker |
| Cache 命中率低 | 调 managedLedgerCacheSize |
| 单 Bookie 磁盘 > 85% | Offload / 加 Bookie |

#### B10.7 决策树

```
吞吐不够？
├── 消息<1KB → Batching 开了吗？→ 开 Batching+LZ4
│   └── 开了 → 分区够吗？Consumer 够吗？→ Client 调完看 L4
├── 消息>1MB → Chunking？压缩？拆小？
└── 全局慢 → 集群问题；单 Topic → 代码/配置

延迟太高？
├── batchingMaxPublishDelay 太大 → 调小
├── receiverQueueSize 太大 → 调小
└── Consumer 逻辑慢 → 优化代码

OOM？
├── Producer 队列 → blockIfQueueFull=true
├── Consumer 预取 → 减小 receiverQueueSize
└── 大消息 → Chunking
```

---

### B11. 性能验证

- `topics stats` 对比调优前后 msgRateIn / backlog
- Java 埋点：send latency / process latency
- 开发自测：`producer.flush()` + 计时算 TPS
- **性能数字只在 Cluster 上测**（见 B12.7）

---

### B12. 环境模型与差异

#### B12.1 三种环境

| 维度 | Standalone | Cluster | K8s |
|------|-----------|---------|-----|
| 用途 | **本地开发** | **压测/生产** | **生产主流** |
| 节点 | 1 | 3+3+3 | Pod 化 |
| HA | 无 | 有 | + Pod 自愈 |
| 连接 | localhost:6650 | broker1:6650,... | Service/Proxy URL |
| 性能 | 极低 | 线性扩展 | 同 Cluster |

#### B12.2 开发 / 压测 / 生产差异矩阵

| 维度 | 开发(Standalone) | 压测(Cluster) | 生产(Cluster/K8s) |
|------|-----------------|--------------|------------------|
| Topic | Auto-Create | 预建 | 禁 Auto-Create |
| Batching | 可关 | 与生产一致 | 必开 |
| TLS/Auth | 不开 | 可选 | 必须 |
| 监控 | 可不搭 | 完整 | 完整+告警 |
| 目标 | 逻辑正确 | 性能上限 | 稳定可靠 |

#### B12.3 Standalone 能/不能

**能：** 写代码、调试 ACK/DLQ/Schema、小批量功能测试

**不能：** 性能数据、Failover、连接数压测、Bundle 迁移、TLS 流程

#### B12.4 Standalone → Cluster 迁移清单（14 项）

| # | 检查项 | 后果 |
|---|--------|------|
| 1 | serviceUrl 改为 Cluster URL | 连不上 |
| 2 | Tenant/Namespace 预建 | TopicNotFound |
| 3 | 关闭 Auto-Create，手动建 Topic | 建错 Topic |
| 4 | Schema 在 Cluster 注册 | SchemaException |
| 5 | subscriptionName 统一 | 重复/收不到 |
| 6 | Batching/压缩与压测一致 | 吞吐差 5-10 倍 |
| 7 | ackTimeout 按 P99 设 | 重复消费 |
| 8 | DLQ/Retry 必配 | 失败消息丢 |
| 9 | blockIfQueueFull=true | OOM |
| 10 | TLS 配置 | 连接拒绝 |
| 11 | Auth Token | 401 |
| 12 | Retention/TTL | 磁盘/数据问题 |
| 13 | Backlog Quota | 积压撑爆 |
| 14 | 监控接入 | 出问题看不到 |

#### B12.5 只在 Cluster 才出现的问题

- 场景 9-12（见 B9.3）

#### B12.6 K8s 特有坑

| 坑 | 解决 |
|----|------|
| Pod 重启丢连接 | Client 自动重连 + graceful shutdown |
| Service 地址不对 | 用 K8s Service DNS |
| liveness 杀 Consumer | 调阈值 |
| 资源 limit 太低 OOM | 合理 memory limit |
| ConfigMap 变更不生效 | 重启 Pod |
| Helm 升级短暂不可用 | 滚动更新策略 |

#### B12.7 环境 × 性能调优

| 调优动作 | Standalone | Cluster |
|---------|-----------|---------|
| Batching 对比 | 趋势参考 | **准确数据** |
| 分区/Consumer 扩容 | ❌ | **必须** |
| 连接数压测 | ❌ | **必须** |
| DLQ/ACK 功能验证 | ✅ | ✅ |

---

## 5. Part C：架构 & 运维扩展（P3）

- C1. 集群部署（Standalone / Cluster / K8s Helm）
- C2. 硬件规划（Bookie Journal SSD、Broker 内存）
- C3. BookKeeper 调优（E-Q-W、Journal 同步、GC）
- C4. Broker 调优（Cache、Bundle 均衡）
- C5. 监控告警（Prometheus + Grafana）
- C6. 安全（TLS、JWT、RBAC）
- C7. Geo-Replication 部署
- C8. Tiered Storage 配置
- C9. 升级迁移
- C10. 故障 Runbook
- C11. **10W 设备压测实战**（综合项目，前置 L1+L2+B10+B12）
- C12. 源码阅读（ManagedLedger / Cursor）

---

## 6. Part D：问题百科

> 按现象查，反向链接到 Part A/B 章节。

| 现象 | 优先级 | 章节 |
|------|--------|------|
| 消息丢失 | P1 | A6, B9-1 |
| 重复消费 | P1 | A6, B9-2 |
| 消息乱序 | P1 | A5, B9-3 |
| Backlog 积压 | P1/P2 | A7, B9-4 |
| 性能不够 | P1/P2 | A12, B10 |
| 本地 OK 集群不行 | P2 | B12.4, B9-9 |
| 连接断 | P2 | B9-6 |
| Schema 报错 | P2 | B9-7, B4 |
| OOM | P2 | B9-8, B10 |
| Bookie 磁盘满 | P3 | C10 |
| K8s Pod 被杀 | P2/P3 | B12.6 |

---

## 7. 附录

| 附录 | 内容 | 优先级 |
|------|------|--------|
| A. 面试题索引 | 50+ 题，按主题分类 | P1 |
| B. Kafka ↔ Pulsar 对照表 | 概念/架构/消费/保留 | P1 |
| C. Java Client API 速查 | Producer/Consumer/Reader | P2 |
| D. 性能调优参数速查 | B10 精华表 | P2 |
| E. 问题排查决策树 | B9+B10 精华 | P2 |
| F. pulsar-admin 命令速查 | 开发/调试常用 | P2 |
| G. 配置参数全集 | Broker/Bookie/Client | P3 |
| H. 推荐资源 | 官方文档/论文/博客 | P3 |
| I. 环境迁移 Checklist | B12.4 十四项 | P2 |
| J. 环境差异速查 | B12.2 矩阵 | P2 |
| K. 方案一页纸模板 | B13 说服改造 | P2 |

---

## 8. 附录 A：面试题索引（50+）

### 架构类
1. Pulsar 架构是怎样的？Broker/Bookie/ZK 各做什么？
2. Broker 为什么说无状态？
3. BookKeeper 和 Broker 什么关系？
4. Managed Ledger 是什么？
5. Bundle 是什么？做什么用？
6. 一条消息写入的完整路径？
7. 一条消息读取的完整路径？
8. E-Q-W 是什么？3:3:2 什么意思？
9. Journal 和 Ledger 区别？
10. Metadata Store 用什么？ZK 和 Oxia 区别？

### 对比类
11. Pulsar 和 Kafka 核心区别？
12. Pulsar 和 RocketMQ 区别？
13. 什么场景选 Pulsar 不选 Kafka？
14. Cursor 和 Kafka Offset 区别？
15. Key_Shared 和 Kafka Consumer Group 区别？

### Topic 类
16. Persistent 和 Non-Persistent 区别？
17. 分区 Topic 和非分区 Topic 区别？
18. 分区数怎么定？能动态改吗？
19. Compaction 是什么？和 Retention 区别？
20. 海量 Topic 有什么问题？

### 订阅 & 消费类
21. 四种订阅模式分别什么场景？
22. Exclusive 和 Failover 区别？
23. Shared 为什么无序？
24. Key_Shared 的 AUTO_SPLIT 和 STICKY 区别？
25. At least once 怎么实现？重复消费怎么办？
26. Exactly once 怎么实现？
27. 单条 ACK 和累积 ACK 区别？
28. Cursor 存在哪？

### 保留 & 清理类
29. TTL 和 Retention 区别？
30. Backlog Quota 是什么？
31. Compaction 触发条件？

### 异常处理类
32. 消费失败怎么处理？
33. DLQ 是什么？怎么用？
34. Retry Topic 机制？

### Schema 类
35. Schema Registry 做什么？
36. Schema 兼容策略有哪些？

### 高级特性类
37. Transaction 原理？
38. Delayed Message 怎么做？
39. Deduplication 原理？
40. Geo-Replication 原理和限制？
41. Tiered Storage 原理？
42. Pulsar Functions 和 Flink 区别？
43. KoP 是什么？

### 性能类
44. Pulsar 性能瓶颈在哪？
45. 怎么提高吞吐？
46. Batching 原理和延迟权衡？
47. 海量连接怎么处理？
48. Standalone 和 Cluster 区别？

### 多租户类
49. Tenant/Namespace/Topic 关系？
50. 多租户怎么隔离？

---

## 9. 实战项目（Part C 综合演练）

| 项目 | 涉及模块 | 阶段 |
|------|---------|------|
| 订单系统消息改造 | B2/B3/B9 | Phase 1 |
| Schema 演进实战 | B4/B9-7 | Phase 1 |
| Standalone → Cluster 迁移 | B12.4 | Phase 1 |
| Shared/非分区/Auto-Create 迁移 | B13/K/P4 | Phase 2 |
| 10W 设备消息压测 | A12/B10/B12/C11 | Phase 2 |
| CDC 数据同步（Pulsar IO） | C + B3 | Phase 2 |
| 跨机房 Geo-Replication | C7 | Phase 2 |
| 生产故障模拟与 Runbook | C10/D | Phase 3 |

---

## 10. 版本说明

- 本大纲基于 Pulsar 2.10+ / 2.11 稳定版编写
- 3.x Oxia 元数据存储作为了解项（A2/A11 标注）
- Java Client 以 `pulsar-client` 最新稳定版为准
- Spring 集成以 Spring Boot 3.2+ 为准
