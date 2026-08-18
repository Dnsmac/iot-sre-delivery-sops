# C12 协议深读与实现对照

> 优先级: **P3 运维** | 预计阅读 45 分钟 | 深度：已深化

## 本章解决什么问题

从 **报文与状态机** 角度理解 MQTT 3.1.1/5.0，能对照 Mosquitto/EMQX 日志与 Wireshark 定位异常 CONNECT、QoS 重传、会话问题；支撑面试深挖与 [C10](C10-failure-runbook.md) 根因分析，而非只会调 API。

---

## 面试常问

1. MQTT 固定头包含哪些字段？
2. QoS1 的 PUBACK 谁发给谁？
3. Clean Session 在 3.1.1 和 5.0 有何不同？
4. 遗嘱消息在哪个报文里携带？
5. 如何从抓包判断是 Broker 还是客户端问题？

---

## 核心知识

### 报文类型（3.1.1 常用）

| 类型 | 值 | 场景 |
|------|-----|------|
| CONNECT | 1 | 建连，含 ClientID、Keep Alive、Will |
| CONNACK | 2 | 返回码 0=成功 |
| PUBLISH | 3 | 业务消息，含 Topic、Packet ID(QoS>0) |
| PUBACK/PUBREC/PUBREL/PUBCOMP | 4~7 | QoS 握手 |
| SUBSCRIBE/SUBACK | 8~9 | 订阅 |
| PINGREQ/PINGRESP | 12~13 | 心跳 |
| DISCONNECT | 14 | 正常断开（5.0 常用） |

### 固定头（2 字节起）

```text
Byte1: 类型(高4bit) + DUP + QoS + RETAIN
Byte2+: 剩余长度（变长编码）
```

### QoS1 时序（记面试图）

```text
Publisher --PUBLISH(id)--> Broker --PUBLISH(id)--> Subscriber
Publisher <--PUBACK(id)--- Broker <--PUBACK(id)--- Subscriber
```

- **DUP 标志**：重传时置 1；消费端需幂等。
- **Packet ID**：QoS>0 唯一；inflight 窗口满则阻塞。

### 会话（3.1.1）

- **Clean Session=true**：断线后会话与订阅状态清除（Broker 侧）。
- **false**：可恢复订阅与 QoS1/2 未确认消息（受 `max_mqueue` 等限制）。

### MQTT 5.0 差异摘要

- **原因码** 替代部分返回码；**Session Expiry** 替代 Clean Session 语义细分。
- **User Properties**、**Topic Alias** 降带宽。
- 本仓主线 3.1.1，生产若混合版本见 [A10](../01-面试篇/A10-mqtt5-advanced.md)。

### 实现对照

| 现象 | 可能报文层原因 |
|------|----------------|
| 连接秒断 | CONNACK 0x04/0x05 用户名或 ACL |
| 消息重复 | QoS1 DUP=1 重传 |
| 订阅无消息 | SUBACK 失败或 Topic 不匹配 |
| 假在线 | 无 PINGREQ，NAT 超时 |

---

## 生产环境注意点

- 排障抓包 **注意合规**，生产 Payload 可能含隐私；优先 **采样** 或测试环境复现。
- TLS 场景用 Wireshark **解密密钥日志** 或 Broker 侧 debug 日志，而非明文口。
- EMQX 可开 **慢订阅**、**追踪** 功能（限时）；Mosquitto 提高 `log_type all` 仅开发。
- 固件与 Broker **协议版本** 不一致时 CONNACK 非 0，先查协议级别字段。

---

## 易错点与反例

1. **把 TCP 断开当 MQTT DISCONNECT** — Will 会触发。
2. **QoS0 也期待 Packet ID** — 无 ID，无法确认重传。
3. **订阅 QoS0 发布 QoS1** — 生效 QoS 取 min，仍可能丢。
4. **忽略 ClientID 长度** — 超 23 字符部分老 Broker 拒绝。
5. **UTF-8 主题非法** — CONNACK 或 SUBACK 失败。

---

## 动手验证

```powershell
# Mosquitto 详细日志（临时）
# log_type all

mosquitto_pub -h localhost -t dev/proto/qos1 -m "id-test" -q 1 -d
mosquitto_sub -h localhost -t dev/proto/qos1 -q 1 -d -C 1
```

Wireshark 过滤器：`mqtt.msgtype == 1`（CONNECT）、`mqtt.msgtype == 3`（PUBLISH）。

阅读源码路径建议：Mosquitto `lib/mqtt_packet.c`；EMQX 文档「设计」章节。

---

## 相关章节

- [A4 报文流程](../01-面试篇/A4-packets-connect-flow.md) | [A5 QoS](../01-面试篇/A5-qos-semantics.md) | [A10 MQTT5](../01-面试篇/A10-mqtt5-advanced.md)
- [附录 B 协议对比](../附录/B-protocol-comparison.md) | [C3 调优](C3-broker-tuning.md)
