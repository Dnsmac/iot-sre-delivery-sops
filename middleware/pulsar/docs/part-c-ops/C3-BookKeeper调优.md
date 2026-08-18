# C3 BookKeeper 调优

> 优先级: **P3 运维** | 深度：批次 4 ✓

## 本章解决什么问题

配置 E-Q-W、Journal 刷盘、Compaction/GC，并通过指标判断 Bookie 是否成为瓶颈。

---

## 一、E-Q-W 配置

Namespace 级 `persistence` 或 Broker 默认：

| 配置 | 场景 |
|------|------|
| 3:3:2 | 常见生产，容忍 1 Bookie 慢 |
| 3:3:3 | 更强持久，写延迟更高 |
| 3:2:2 | 省写带宽，容错需评估 |

```bash
pulsar-admin namespaces set-persistence persistent://company/production \
  --bookkeeper-ensemble 3 \
  --bookkeeper-write-quorum 3 \
  --bookkeeper-ack-quorum 2
```

原理见 [A11](../part-a-interview/A11-BookKeeper深入.md)。

---

## 二、Journal 调优

| 参数方向 | 说明 |
|----------|------|
| Journal 盘 | 必须 SSD |
| `journalSyncData` | true 更安全；false 更快但有断电风险 |
| 单 Bookie 磁盘数 | Journal 与 Ledger 分离 |

---

## 三、Ledger GC / Compaction

- `majorCompactionThreshold`：磁盘占用触发 major compaction。
- 定期监控 ledger 目录增长。
- Tiered offload 后 Bookie 空间应下降（[C8](C8-分层存储.md)）。

---

## 四、关键指标

| 指标 | 告警参考 |
|------|----------|
| `bookkeeper_server_ADD_ENTRY` P99 | > 10ms 查 Journal/磁盘 |
| Bookie 磁盘使用率 | > 75% 预警 |
| 只读 Bookie 数量 | 应为 0（`-rw` 列表） |

```bash
pulsar-admin bookies list-bookies
pulsar-admin bookies list-bookies -rw
```

---

## 五、故障信号 → 动作

| 信号 | 动作 |
|------|------|
| ADD_ENTRY P99 高 | 查 SSD、网络、是否混部重 IO |
| 单 Bookie 磁盘满 | 扩盘、offload、缩短 retention |
| NotEnoughBookies | 恢复挂掉的 Bookie，检查 ensemble |

---

## 相关章节

- [C2](C2-硬件规划.md) | [C5](C5-监控告警.md) | [P11](../part-d-problems/P11-Bookie磁盘满.md)
