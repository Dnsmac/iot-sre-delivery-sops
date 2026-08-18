# 附录 D：性能参数速查

> 深度：全文加深 ✓ | 决策树见 [B10](../part-b-java-dev/B10-性能调优.md)

---

## 一、调优金字塔（影响排序）

```
1. 架构：分区数、Key_Shared、消息大小
2. Producer：Batching + 压缩
3. Consumer：实例数、receiverQueueSize
4. 集群：Bookie 磁盘、Broker 数
5. JVM 微优化
```

---

## 二、Producer 参数

| 参数 | 开发 | 生产高吞吐 | 低延迟 | 影响 |
|------|------|------------|--------|------|
| `enableBatching` | 可关 | **true** | false | 吞吐 ★★★★★ |
| `batchingMaxPublishDelay` | — | 10~50ms | 0~1ms | 延迟 vs 吞吐 |
| `batchingMaxMessages` | — | 1000 | 小 | batch 大小 |
| `compressionType` | NONE | **LZ4** | LZ4/ZSTD | 带宽 |
| `blockIfQueueFull` | true | **true** | true | 防丢+背压 |
| `maxPendingMessages` | 500 | 1000~2000 | 小 | 异步队列 |
| `sendTimeout` | 30s | 30s | 10s | 超时失败 |

```java
.enableBatching(true)
.batchingMaxPublishDelay(10, TimeUnit.MILLISECONDS)
.compressionType(CompressionType.LZ4)
.blockIfQueueFull(true)
.maxPendingMessages(1000)
```

**大消息（>1MB）：** `enableChunking(true)`，并确认 Broker `maxMessageSize`。

---

## 三、Consumer 参数

| 参数 | 开发 | 生产 | 说明 |
|------|------|------|------|
| `receiverQueueSize` | 100~500 | 1000~5000 | × 消息大小 = 内存 |
| `ackTimeout` | 60s | **P99处理×3** | 过短→重复 |
| `maxUnackedMessages` | 默认 | 按内存调 | 背压 |
| `poolMessages` | false | 高吞吐可 true | 减 GC |

---

## 四、分区与并行度

```
Consumer 有效并行度 ≤ 分区数（分区 Topic）
Key_Shared 并行度 ≤ Consumer 实例数（受 Key 分布限制）
```

| 症状 | 调参 |
|------|------|
| 加 Consumer 吞吐不变 | 加分区或热点 Key |
| backlog 涨 | 先 msgRateOut，再扩 Consumer |
| OOM | 降 receiverQueue、加快 ACK |

---

## 五、环境差异

| 参数 | Standalone | Cluster 签字 |
|------|-----------|--------------|
| Batching 对比 | 看趋势 | **准确数字** |
| 连接数压测 | ❌ | ✅ |

见 [B11](../part-b-java-dev/B11-性能验证.md)、[附录 J](J-环境差异矩阵.md)。

---

## 六、快速实验

```powershell
cd examples\java\pulsar-producer-tuning
mvn -q exec:java -Dexec.mainClass="com.demo.pulsar.tuning.BatchCompareBenchmark"
```

---

## 相关

- [B10](../part-b-java-dev/B10-性能调优.md) | [P5](../part-d-problems/P5-性能不足.md) | [附录 G](G-配置参考.md)
