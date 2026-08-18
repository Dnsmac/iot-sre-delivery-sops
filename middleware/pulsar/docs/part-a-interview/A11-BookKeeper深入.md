# A11 BookKeeper 深入

> 优先级: **P1 面试加分** | 预计阅读 35 分钟 | 深度：批次 4 ✓

## 本章解决什么问题

解释 Pulsar **消息存在哪**、为什么写快读稳、E-Q-W 参数含义，以及 Bookie 磁盘满时背后发生了什么。

---

## 面试常问

1. BookKeeper 和 Broker 分工？
2. E-Q-W 是什么？3:3:2 表示什么？
3. Journal 和 Ledger 区别？
4. Managed Ledger 是什么？
5. Bookie 挂了消息会丢吗？

---

## 一、架构位置

```
Producer → Broker → BookKeeper (Bookie 集群) → 磁盘
                ↑
Consumer ← Broker 读 Bookie
```

- **Broker**：无状态（不持久化消息体），路由与缓存。
- **Bookie**：真正持久化 **Ledger Entry**。

见 [A2](A2-核心架构.md)。

---

## 二、E-Q-W（Ensemble / Write / Ack Quorum）

配置示例：`ensembleSize=3, writeQuorum=3, ackQuorum=2`（常简写 **3:3:2**）

| 参数 | 含义 |
|------|------|
| **E (Ensemble)** | 副本分布在几个 Bookie 上 |
| **W (Write Quorum)** | 写成功需要几个副本 |
| **A (Ack Quorum)** | 返回给 Broker「写成功」需要几个 Bookie 确认 |

**3:3:2：** 写 3 副本，任意 **2** 个确认即可 ACK Producer（容忍 1 个 Bookie 慢/挂）。

| 配置 | 特点 |
|------|------|
| 3:3:3 | 最强一致，延迟高 |
| 3:2:2 | 省副本写，容忍度需评估 |

Namespace 级 `persistence` 策略可覆盖默认值。

---

## 三、Journal vs Ledger

| | Journal | Ledger |
|---|---------|--------|
| 介质 | **SSD** 顺序写 | 多为大容量盘 |
| 作用 | 预写日志，快速落盘 | 只追加不可变 Entry |
| 生命周期 | 刷盘后可与 Ledger 分离 | 按 Topic 滚动、Offload、GC |

**写路径：** 先写 Journal（低延迟）→ 异步组织到 Ledger 文件。

**面试句：** Journal 保证写延迟，Ledger 保证持久化存储结构；Bookie Journal 必须用 SSD。

---

## 四、Managed Ledger（Broker 视角）

- Broker 上每个 Topic 分区对应 **ManagedLedger**。
- 由多个 **Ledger** 顺序组成；达到大小/时间阈值 **滚动新 Ledger**。
- 旧 Ledger 可 **Offload** 到对象存储（Tiered Storage）后从 Bookie 删除。

```
ManagedLedger: [Ledger1][Ledger2][Ledger3]...
                      ↑ 当前写入
```

Consumer Cursor 指向某个 Ledger 的 Entry 位置（MessageId）。

---

## 五、故障与持久性

| 场景 | 结果 |
|------|------|
| 1 个 Bookie 挂（3:3:2） | 仍可写可读（若 ensemble 够） |
| 超过 W-A 容忍副本挂 | 写入阻塞，Producer 超时 |
| 磁盘满 | `NotEnoughBookiesException`，见 [P11](../part-d-problems/P11-Bookie磁盘满.md) |

**不会**因为 Broker 重启丢消息（数据在 Bookie）；Broker 从 BK 恢复 ManagedLedger。

---

## 六、生产注意点

- Bookie **Journal 盘 SSD**，Ledger 盘容量规划。
- 监控 `bookkeeper_server_ADD_ENTRY` P99。
- 调优见 [C3](../part-c-ops/C3-BookKeeper调优.md)。

```bash
pulsar-admin bookies list-bookies -rw
```

---

## 七、易错点

1. 说「消息存在 Broker 磁盘」。
2. E-Q-W 随便改小导致丢副本容错。
3. Journal 放 HDD 导致写延迟飙升。
4. 手删 ledger 目录「清空间」。

---

## 面试标准答案

> BookKeeper 负责持久化，Broker 负责接入。3:3:2 表示三条副本写在三个 Bookie，写入 quorum 为 3，但只需 2 个确认就可 ACK，容忍一个 Bookie 故障。Journal 是 SSD 上的预写日志，Ledger 是只追加的存储单元。ManagedLedger 是 Broker 对多个 Ledger 的抽象，达到阈值会滚动新 Ledger。

---

## 相关章节

- [A2](A2-核心架构.md) | [C3 调优](../part-c-ops/C3-BookKeeper调优.md) | [C2 硬件](../part-c-ops/C2-硬件规划.md)
