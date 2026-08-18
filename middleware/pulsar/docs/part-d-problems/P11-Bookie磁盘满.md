# P11 Bookie 磁盘满

> 优先级: **P3 运维** | 深度：批次 3 ✓  
> 链接: [A7 Retention](../part-a-interview/A7-保留与清理策略.md) | [P4 积压](P4-积压.md) | Part C

---

## 典型现象

- Bookie 节点磁盘 **>90%**，写入失败。
- Broker 生产报错：`NotEnoughBookiesException`、`BookKeeperException`。
- 集群整体可用但**部分 Topic 不可写**。
- 运维收到 ledger 目录暴涨告警。

---

## 原因（按概率排序）

| # | 原因 | 说明 |
|---|------|------|
| 1 | **Retention 过长 + 流量大** | 历史数据占满 |
| 2 | **Backlog 极大** | 未消费数据长期保留 |
| 3 | **副本数 × 写入放大** | ensemble 3 份 |
| 4 | **未开 Tiered Storage** | 冷数据仍在 Bookie |
| 5 | **Compaction 未跑** | Key 类 Topic 膨胀 |
| 6 | **测试数据未清理** | TTL 未设 |
| 7 | **Bookie 单盘** | 无独立 journal/ledger 盘 |
| 8 | **异常大消息** | 单条 MB 级 |

---

## 排查步骤

### 1. 磁盘与目录

```bash
df -h
du -sh /pulsar/data/bookkeeper/ledgers/*
```

### 2. 集群 Bookie 状态

```bash
pulsar-admin bookies list-bookies
pulsar-admin bookies list-bookies -rw
```

### 3. Namespace / Topic 占用（间接）

- 找最大流量 Topic：`topics stats` 比较 `storageSize`
- 租户级监控：Prometheus `pulsar_storage_size`

### 4. 策略

```bash
pulsar-admin namespaces get-retention persistent://company/production
pulsar-admin namespaces get-message-ttl persistent://company/production
```

### 5. 是否可删测试 Tenant

```bash
pulsar-admin tenants delete my-test-tenant  # 需评估影响
```

---

## 解决方案（紧急 → 长期）

| 阶段 | 动作 |
|------|------|
| **紧急** | 扩 Bookie 磁盘；加 Bookie 节点；临时缩短 Retention（需业务确认） |
| **消积压** | 扩 Consumer、修慢消费，见 [P4](P4-积压.md) |
| **策略** | 合理 Retention/TTL；测试 NS 短保留 |
| **架构** | Tiered Storage  offload 冷数据到 S3/HDFS |
| **Compaction** | 对状态类 Topic 定期 compact |
| **容量规划** | `日增量 × 保留天数 × 副本数 × 1.2` 余量 |

### 禁止（除非明确审批）

- 手动删 ledger 文件（损坏元数据）
- `consumer_backlog_eviction` 当长期方案

---

## 监控告警

- Bookie 磁盘使用率 > 75% 预警，> 85% 紧急
- `pulsar_storage_logical_size` 增长率
- 单 Namespace `backlog` 与 `storageSize` Top N

---

## 面试一句话

> Bookie 满通常是 Retention 太长加消费慢导致数据堆在 BookKeeper；先扩盘和加 Bookie，同时降 Retention 或提速消费，长期用 Tiered Storage 和容量公式规划，不要手删 ledger 目录。
