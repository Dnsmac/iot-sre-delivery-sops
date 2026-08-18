# C4 桥接：MQTT → Pulsar / Kafka

> 优先级: **P3 运维** | 预计阅读 40 分钟 | 深度：已深化

## 本章解决什么问题

设计 **设备 MQTT 接入层** 与 **数据中心流平台** 的边界：消息如何从 `sensor/+/telemetry` 进入 `persistent://tenant/ns/topic`，并处理 QoS 降级、主题映射、背压与幂等，避免「双写不一致」或「桥接断了静默丢数」。

---

## 面试常问

1. MQTT 桥接和 Kafka Connect 有什么区别？
2. 桥接时 QoS 如何映射？QoS2 能原样到 Pulsar 吗？
3. EMQX 规则引擎和独立网关服务各适合什么场景？
4. 主题通配符如何映射到 Pulsar 分区？
5. 桥接失败如何告警与重放？

---

## 核心知识

### 数据流

```text
设备 --MQTT QoS1--> EMQX --规则/桥接--> Pulsar Producer
                         │
                         └── 可选：独立 Java 网关 (Paho sub + Pulsar send)
```

### 三种实现

| 方式 | 优点 | 注意 |
|------|------|------|
| EMQX 规则引擎 SQL | 运维配置快、少代码 | 复杂转换需测试；版本升级查兼容性 |
| EMQX MQTT Bridge | 连远端 Broker | 勿成环；主题 remap |
| 自研网关服务 | 业务逻辑完全可控 | 需 HA、监控、offset 管理 |

### 主题映射示例

| MQTT | Pulsar |
|------|--------|
| `prod/{tenant}/{deviceId}/event` | `persistent://iot/telemetry/event` + Key=`deviceId` |
| `prod/+/alarm` | 单独 namespace，高优先级订阅 |

- **分区键**：用 `deviceId` 保证同设备有序（对齐 [P3](../04-问题百科/P3-out-of-order.md)）。
- **Payload**：JSON 透传或 Schema Registry；避免 Broker 侧解析超大 JSON。

### QoS 与语义

- MQTT **QoS1 至少一次** → Pulsar 生产通常 **幂等写**（Key + 去重表或业务 upsert）。
- MQTT QoS2 ** rarely 桥接保留**；多数方案在桥接层降为 QoS1，由下游 exactly-once 策略承担。
- **Retain** 消息：桥接策略需显式「是否转发 retain」，避免启动风暴灌入 Pulsar。

### 背压

- Pulsar 写入慢 → EMQX 规则队列涨 → 触发 [C5](C5-monitoring.md) 告警。
- 网关模式：有界队列 + 丢弃策略（仅非关键主题）或 暂停 MQTT ACK（慎用）。

---

## 生产环境注意点

- 桥接账号 **最小权限**：仅允许订阅前缀 `prod/bridge/#`。
- 跨机房桥接走 **专线/VPN**，TLS 双向认证。
- 与 Pulsar 租户命名 **文档化**（见本仓 `docs/实战项目/P4-migrate-qos-topic.md`）。
- 灾备：记录 **最后成功 offset/时间戳**，支持按时间窗口重放 MQTT（若 EMQX 有保留）或从 Pulsar 补偿。
- Mosquitto **无原生企业桥到 Pulsar**；开发可用 `mosquitto_pub` 模拟 + 本地网关进程。

---

## 易错点与反例

1. **双向桥接主题环** — A→B→A 无限循环。
2. **通配符订阅过宽** — `prod/#` 把调试流量写入生产 Pulsar。
3. **无 Key 写 Pulsar** — 全局乱序，消费难以按设备排查。
4. **桥接 QoS0** — 网络闪断即丢，却以为 Pulsar 有日志可查。
5. **字符集/主题大小写** — Linux Broker 敏感，设备固件不一致导致订不到。

---

## 动手验证

```powershell
# Mosquitto 发，本地网关或 mosquitto_sub 消费验证主题
mosquitto_pub -h localhost -t prod/demo/bridge -m '{"v":1}' -q 1

# EMQX 规则（示例思路，以实际 Dashboard 为准）
# SELECT payload FROM "prod/demo/#" 
```

Java 参考：[B2 发布](../02-开发篇/B2-publish.md)、[B3 订阅](../02-开发篇/B3-subscribe.md)；Pulsar 侧用同仓 Pulsar 文档 B4 规范。

---

## 相关章节

- [C7 规则引擎](C7-rule-engine.md) | [C10 Runbook](C10-failure-runbook.md)
- [A5 QoS](../01-面试篇/A5-qos-semantics.md) | [P1 丢失](../04-问题百科/P1-message-loss.md) | [P2 重复](../04-问题百科/P2-duplicate.md)
