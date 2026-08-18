# C4 Broker 调优

> 优先级: **P3 运维** | 深度：批次 4 ✓

## 本章解决什么问题

优化 Broker 读缓存、连接与 Bundle 负载均衡，识别 Broker 侧瓶颈。

---

## 一、ManagedLedger Cache

| 配置 | 作用 |
|------|------|
| `managedLedgerCacheSize` | 读热点数据缓存，减 Bookie 读 |
| `managedLedgerCacheEvictionWatermark` | 驱逐水位 |

- 读多 Topic、重复消费场景：**加大 cache**（受 Broker 内存限制）。
- 信号：Bookie 读 IO 高但 Broker cache 命中率低。

---

## 二、连接与线程

- `maxConnectionsPerIp` / 全局连接上限：设备场景配合 **Proxy**。
- 监控 Broker 文件描述符、`numConnections`。

---

## 三、Bundle 负载均衡

- Topic 落在 Bundle，Bundle 由某 Broker 负责。
- 热点 Namespace 可导致单 Broker CPU 高。
- 运维：

```bash
pulsar-admin namespaces unload persistent://company/hot-ns
# 或调整 loadManager 策略、隔离策略
```

---

## 四、关键信号

| 信号 | 可能原因 |
|------|----------|
| Broker CPU > 80% | 热点 Bundle、解析大消息、过多 Topic |
| Full GC 频繁 | heap 过小、cache 过大 |
| 消费延迟高但 Bookie 正常 | Cache 未命中、网络、Consumer 慢 |

---

## 五、与客户端关系

Broker 再快，Consumer 慢仍 backlog（[P4](../part-d-problems/P4-积压.md)）。调 Broker 前先确认 `msgRateOut`。

---

## 相关章节

- [C5](C5-监控告警.md) | [B10](../part-b-java-dev/B10-性能调优.md) | [A12](../part-a-interview/A12-性能与规模.md)
