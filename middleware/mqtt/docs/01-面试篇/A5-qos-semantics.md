# A5 QoS 与投递语义

> 优先级: **P1 面试** | 预计阅读 35 分钟 | 深度：已深化 | 学习路径：**D3 | 面试：★★★★★ 最高频** | 主路径：[学习路径](../学习路径.md)

## 面试常问

1. QoS0/1/2 区别与选型？
2. 发布 QoS2 订阅 QoS0 会怎样？
3. QoS1 为什么会重复？如何应对？
4. Clean Session 和 QoS 如何配合？
5. 桥接时 QoS 要注意什么？

## 本章解决什么问题

> **今日（D3）下一步：** 默画 QoS 表 → 跑 QoSDemo → 明日 [A6](A6-session-keepalive.md)（与 QoS 强相关）。

MQTT 的可靠性**不是一套默认值**，而是由 **QoS 等级 + 会话 + Broker 实现** 共同决定。搞不清 QoS，会出现「以为不丢其实全丢（QoS0）」或「重复消息不会处理（QoS1）」。

---

## 三级 QoS 详解

| QoS | 名称 | Broker 行为 | 报文流 | 丢 | 重 |
|-----|------|-------------|--------|----|----|
| **0** | 最多一次 | 收到即转发，不确认 | PUBLISH | ✅可能 | ❌ |
| **1** | 至少一次 | 持久化到会话后 PUBACK | PUBLISH ↔ PUBACK | ❌ | ✅可能 |
| **2** | 恰好一次 | 四次握手 | PUBLISH → PUBREC → PUBREL → PUBCOMP | ❌ | ❌协议层 |

### QoS 0：发完即忘

- 适合：环境传感器每秒采样、丢一两帧无影响。
- **不适合：** 告警、计费、固件升级指令。
- 网络闪断时**静默丢失**，应用层无回调失败（除非 TCP 断连）。

### QoS 1：至少一次（工业默认）

- Publisher 收 **PUBACK** 才认为发送成功（Client 库层）。
- Subscriber 处理前应视为「未确认」；Paho 在 `messageArrived` 返回后由库发 PUBACK（取决于配置和手动 ack 模式）。
- **必须幂等：** 同一温度上报处理两次可能写库两次。

### QoS 2：恰好一次

- 四次握手，开销最大，吞吐显著低于 QoS1。
- 高并发设备上报**慎用**；计费、关键控制可用。

### 发布与订阅 QoS 的最终生效值

- CONNECT 后，**PUBLISH** 和 **SUBSCRIBE** 都可带 QoS。
- 常见规则：实际 QoS = **min(发布 QoS, 订阅 QoS)**（以 Broker 文档为准，面试提一句即可）。
- **反例：** 发布 QoS2、订阅 QoS0 → 可能降为 0，以为很安全实际可丢。

---

## 与 Clean Session 的交互

| Clean Session | QoS1/2 离线消息 |
|---------------|-----------------|
| `true` | 断线后会话清空，**离线期间消息不缓存**（未送达的 QoS1/2） |
| `false` | Broker 可为会话缓存 QoS1/2 离线消息（受 Broker 配置与限制） |

**面试点：** 「QoS1 就不丢」在 Clean Session=true + 断线场景下仍可能丢**离线窗口**的消息。

---

## 与 Pulsar / Kafka 对照

| | MQTT QoS | Pulsar/Kafka |
|---|----------|--------------|
| 粒度 | 单条消息协议 ACK | Batch + offset/cursor |
| 重复 | QoS1 常见 | at-least-once 常见 |
| 接入 | 设备侧 | 数据中心 |

典型架构：**设备 MQTT QoS1 → 网关聚合 → Pulsar 批量写入**。

---

## 面试标准答案

### 题：MQTT QoS0/1/2 区别？怎么选？

> QoS0 最多一次，不发确认，可能丢，适合可丢的遥测。QoS1 至少一次，有 PUBACK，不丢但可能重复，需要业务幂等，是大多数业务默认。QoS2 四次握手，协议层恰好一次，开销大，适合关键指令但不适合海量高频。选型还要看 Clean Session：如果设备要离线必达，需要持久会话加 QoS1，不能开 Clean Session true 却指望离线消息。我们还会看订阅端 QoS，实际生效取发布和订阅的较小值。

### 题：QoS1 重复消息怎么处理？

> 协议层保证至少一次，所以应用必须幂等：用设备 ID 加消息序号或业务唯一键做去重，数据库唯一索引，或 Redis set。不要试图只靠 MQTT 消灭重复，那是 QoS2 的职责且代价高。

---

## 生产注意点

- 关键链路：**QoS1 + 幂等 + 规范 topic**。
- 全网 QoS0 只在「可丢 + 可降采样」成立。
- 桥接到 Pulsar 时，桥接规则要指定 QoS，避免降级。

---

## 易错点

1. 全 QoS0 却业务说「不能丢」。
2. QoS1 不做幂等。
3. 忽略 min(pub, sub) 导致降级。

---

## 动手验证

```bash
# 终端1
mosquitto_sub -h localhost -t dev/qos/test -q 1 -v
# 终端2
mosquitto_pub -h localhost -t dev/qos/test -m "hello" -q 1
```

Java：[QoSDemo.java](../../examples/java/mqtt-basics/src/main/java/com/demo/mqtt/QoSDemo.java)

---

## 相关

- [A6 会话](A6-session-keepalive.md) | [B2 发布](../02-开发篇/B2-publish.md) | [P2 重复](../04-问题百科/P2-duplicate.md)
