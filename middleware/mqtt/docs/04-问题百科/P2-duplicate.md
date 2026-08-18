# P2 消息重复

> 深度：已深化 | Mosquitto 开发 + EMQX 生产

## 现象

- 同一条业务数据在 DB/下游 **出现多次**（相同 messageId 或时间戳）。
- 日志里 **DUP flag=1** 的 PUBLISH 增多。
- 消费端计数大于 Broker 发布计数（桥接重复写 Pulsar）。

## 常见原因

| 原因 | 说明 |
|------|------|
| QoS1 语义 | 至少一次，重传正常 |
| 发布端重试 | 未收到 PUBACK 再次发送 |
| 消费者处理慢 | PUBACK 滞后导致 Broker 重投 |
| 桥接/规则双写 | 两条规则命中同一消息 |
| 客户端重复订阅 | 同 Client 多连接或逻辑订阅两次 |
| 幂等缺失 | 业务未按 deviceId+seq 去重 |

## 排查步骤

1. 确认 **QoS 等级**；若 QoS0 仍重复，查应用层重复 publish。
2. Wireshark/日志看 **DUP 位** 与 Packet ID 是否同一 ID 重传。
3. 检查 **规则引擎** 是否重复动作（[C7](../03-运维篇/C7-rule-engine.md)）。
4. Pulsar 是否 **at-least-once** + 消费重平衡导致重复读。
5. 核对 ClientID 是否被多实例共用导致 **会话交错**。

## 解决

- 业务 **幂等**：主键 `(deviceId, eventTime, seq)` 或 Redis setnx。
- 能容忍则用 QoS1；确需协议去重才 QoS2（慎用，见 [A5](../01-面试篇/A5-qos-semantics.md)）。
- 合并重复规则；桥接启用 **单出口** 主题。
- 优化消费者：加快处理、调 `maxInflight`、异步 ack。
- Pulsar 侧 **Key_Shared** 或去重表（若版本支持）。

## 预防

- 设计文档明确：**MQTT 不保证恰好一次**（除非 QoS2 且全链路支持）。
- 代码模板：消息带 **单调 seq**，DB upsert。
- 压测观察重传率（[C11](../03-运维篇/C11-loadtest-connections.md)）。
- 告警：单位时间重复率超阈值。

## 相关链接

- [A5 QoS](../01-面试篇/A5-qos-semantics.md) | [P1 丢失](P1-message-loss.md) | [P3 乱序](P3-out-of-order.md)
- [C7 规则引擎](../03-运维篇/C7-rule-engine.md) | [C4 桥接](../03-运维篇/C4-bridge.md)
