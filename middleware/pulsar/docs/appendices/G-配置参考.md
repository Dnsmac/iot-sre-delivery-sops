# 附录 G：配置参数参考（精选）

> 深度：全文加深 ✓ | 完整项以官方 `conf/broker.conf`、`conf/bookkeeper.conf` 为准

---

## 一、Broker（broker.conf / Helm values）

| 参数 | 说明 | 调优提示 |
|------|------|----------|
| `managedLedgerCacheSize` | ManagedLedger 读缓存 | 读多加大，受堆内存限制 |
| `managedLedgerCacheEvictionWatermark` | 缓存驱逐水位 | 与 cacheSize 配合 |
| `loadBalancerEnabled` | Bundle 自动均衡 | 生产建议开 |
| `allowAutoTopicCreation` | 自动建 Topic | **生产 false** |
| `allowAutoSubscriptionCreation` | 自动建订阅 | 生产建议 false |
| `brokerDeleteInactiveTopicsEnabled` | 删除不活跃 Topic | 谨慎 |
| `maxMessageSize` | 单条消息上限 | 与大消息 chunk 对齐 |
| `clusterName` | 集群名 | 与元数据一致 |
| `zookeeperServers` / `metadataStoreUrl` | 元数据地址 | |
| `brokerServicePort` / `webServicePort` | 6650 / 8080 | |
| `brokerServicePortTls` | 6651 | 生产 TLS |

**TLS / 认证：** `tlsEnabled`、`authenticationEnabled`、`authorizationEnabled` — 见 [C6](../part-c-ops/C6-安全.md)。

---

## 二、BookKeeper（bookkeeper.conf）

| 参数 | 说明 |
|------|------|
| `journalDirectory` | Journal 路径（**SSD**） |
| `ledgerDirectories` | Ledger 存储路径 |
| `journalMaxGroupWaitMSec` | 刷盘批次等待 |
| `journalSyncData` | true=更安全，false=更快 |
| `ensembleSize` / `writeQuorum` / `ackQuorum` | 默认 E-Q-W |
| `majorCompactionThreshold` | 磁盘占用触发 major compaction |
| `minorCompactionInterval` | minor compaction 间隔 |

Namespace 可覆盖 persistence：`pulsar-admin namespaces set-persistence`。

---

## 三、Java Client — Producer

见 [附录 D](D-性能参数速查.md)，常用：

- `enableBatching`、`batchingMaxPublishDelay`
- `compressionType`、`blockIfQueueFull`、`maxPendingMessages`
- `sendTimeout`、`chunkingEnabled`

---

## 四、Java Client — Consumer

- `receiverQueueSize`、`ackTimeoutMillis`
- `maxUnackedMessages`、`subscriptionType`
- `deadLetterPolicy`（Builder）

---

## 五、Namespace Policy（运维向）

| Policy | 命令 |
|--------|------|
| retention | `namespaces set-retention --time --size` |
| TTL | `namespaces set-message-ttl` |
| backlogQuota | `namespaces set-backlog-quota` |
| deduplication | `namespaces set-deduplication` |
| schemaCompatibility | `set-schema-compatibility-strategy` |
| replication | `set-clusters`（Geo） |
| persistence | `set-persistence`（E-Q-W） |

```bash
pulsar-admin namespaces policies persistent://dev/test
```

---

## 六、环境变量（Docker/K8s 常见）

| 变量 | 作用 |
|------|------|
| `PULSAR_MEM` | Broker JVM 堆 |
| `BOOKIE_MEM` | Bookie JVM 堆 |
| `PULSAR_PREFIX_*` | 覆盖 broker.conf 项 |

---

## 七、应用配置（Spring）

```yaml
spring.pulsar.client.service-url: ${PULSAR_URL}
spring.pulsar.client.authentication.token: ${PULSAR_TOKEN}
app.pulsar.tenant: company
app.pulsar.namespace: production
```

见 [B8](../part-b-java-dev/B8-配置管理.md)。

---

## 相关

- [C3](../part-c-ops/C3-BookKeeper调优.md) | [C4](../part-c-ops/C4-Broker调优.md) | [附录 D](D-性能参数速查.md)
