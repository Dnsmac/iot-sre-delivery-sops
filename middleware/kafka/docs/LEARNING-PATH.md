# Kafka 学习目标路径（主线 + 面试串讲）

> **先看本文，再看章节。** 结构对齐 [pulsar/LEARNING-PATH.md](../pulsar/docs/LEARNING-PATH.md)  
> 勾选：[STUDY-TRACKER.md](STUDY-TRACKER.md) | 索引：[INDEX.md](INDEX.md)

---

## 一、你的三个目标

| 目标 | 优先级 | 周期 | 过关标志 | 主要材料 |
|------|--------|------|----------|----------|
| **G1 面试能讲** | P1 | 约 2 周 | 3 分钟自述 + 附录 A 随机 10 题答 7 题 | Part A + 附录 A/B |
| **G2 开发能写能排** | P2 | 约 3~4 周 | Producer/Consumer 手写 + lag/丢/重/乱 各 3 步排查 | Part B + Part D |
| **G3 与 Pulsar 对照** | P2+ | 约 1 周 | 附录 B 能双向讲 5 组映射 + 现网口径 | B13 + 附录 B |

**原则：** 你现网是 **Pulsar + EventBus 设备链路** 时，Kafka 仓主要用于 **JD 防御 + 原理对照**，不必假装生产主栈是 Kafka。

---

## 二、一条知识主线

```
【定位】Kafka 是什么、和 Pulsar 差在哪           → A1 + 附录 B
【骨架】Broker、分区日志、KRaft 元数据            → A2、A3
【资源】Topic、Partition、副本、Leader           → A4、A11
【消费】Consumer Group、Rebalance、Offset         → A5
【语义】至少一次、幂等、事务（了解）              → A6
【生命周期】retention、compact、log 清理         → A7
【失败】重试、DLQ、poison message                 → A8
【契约】Schema Registry、Avro/JSON               → A9
【生态】Connect、Streams（加分）                  → A10
【规模】吞吐、分区数、lag、IoT 设备 Key           → A12
        ↓
【动手】Producer → Consumer                      → B1~B3
【协作】多服务、Topic 命名、group.id              → B4、B8
【排障】丢/重/乱/慢（lag）                        → B9 + Part D
【对照】面试说「现网 Pulsar，Kafka 概念映射」     → B13 + 附录 B
```

**记住这一句：**

> Kafka 把消息存在 **Broker 分区日志**里，消费进度在 **Consumer Group 的 Offset** 上；同一 Topic 要多套独立消费，用 **多个 Consumer Group**；设备有序靠 **同一 Key 进同一分区**。

---

## 三、面试怎么讲

### 3.1 30 秒开场

> 我系统学过 Kafka，它是基于 **Topic 分区日志** 的分布式消息平台，Broker 存算一体，元数据现在多用 **KRaft**。消费靠 **Consumer Group + Offset**，分区内有序。我们现网设备主链路是 **EventBus + ES/MySQL**，消息中间件是 **Pulsar**；Kafka 和 Pulsar 在 **订阅/存储模型** 上不同，但 **积压、至少一次、分区有序** 这些排查思路可以对照讲。

### 3.2 3 分钟结构

| 分钟 | 讲什么 | 章节 |
|------|--------|------|
| 0~1 | 是什么 + 分区日志图 | A1、A2 |
| 1~2 | Topic/分区/CG/Offset/至少一次 | A4、A5、A6 |
| 2~3 | 与 Pulsar 对比 + **现网口径** | 附录 B、B13 |

### 3.3 追问映射

| 面试官问 | 先答一句 | 文档 |
|----------|----------|------|
| 架构 | Broker 持分区日志，KRaft 管元数据 | A2、A3 |
| 为什么重复 | 至少一次 + 自动提交 offset | A6、P2 |
| 怎么保证顺序 | 同 Key → 同分区；单分区内单 Consumer | A4、A5 |
| 消息会丢吗 | acks、min.insync.replicas、消费先处理后提交 | A6、A11、P1 |
| 积压怎么看 | **Consumer Lag** | P4、A12 |
| 你们用什么 | 现网 **Pulsar**；Kafka 为 JD/对照 | 附录 B |

---

## 四、按天路径（第 1~2 周 · G1）

| 天 | 今日学 | 明日学 | 过关 |
|----|--------|--------|------|
| D1 | A1、A2 | A3、A4 | 能画 Broker+分区 |
| D2 | A3、A4 | A5 | 分区只增不减（KRaft 概念） |
| D3 | A5 | A6、A7 | CG + rebalance |
| D4 | A6、A7 | A8 | acks + retention |
| D5 | A8、A11 浏览 | A12 | ISR 概念 |
| D6 | A12、**附录 B** | 复习 | lag + Pulsar 对照 5 点 |
| D7 | 附录 A 25 题 | B1 | G1 错题列表 |

---

## 五、与 iot-sre-delivery-sops 计划对齐

| 本仓章节 | 主仓周 | 用途 |
|----------|--------|------|
| A1、附录 B | W6 前 | JD 写 Kafka 时的 30 秒对照 |
| P4 积压 | W3/W6 | 与 pulsar P4 同一套排查思维 |
| B1~B3 | 选修 | 有时间再动手 |

---

## 六、相关文档

| 用途 | 文档 |
|------|------|
| Pulsar 侧对照 | [pulsar/附录 B](../pulsar/docs/appendices/B-Kafka对照.md) |
| 本仓对照 | [附录 B](appendices/B-Pulsar对照.md) |
| 积压 | [P4](part-d-problems/P4-积压.md) |
