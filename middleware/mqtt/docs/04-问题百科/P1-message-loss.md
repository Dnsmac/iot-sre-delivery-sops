# P1 消息丢失

> 深度：已深化 | Mosquitto 开发 + EMQX 生产

## 现象

- 发布端显示成功（或 QoS0 无反馈），订阅端 **长期收不到**。
- 间歇性丢：网络切换、休眠唤醒后 **缺口**。
- 桥接侧 Pulsar **条数少于** MQTT 入站计数。
- 仅部分设备丢，其他正常。

## 常见原因

| 原因 | 说明 |
|------|------|
| QoS0 | 协议允许丢，无 ACK |
| 主题/订阅错误 | 多/少一层、大小写、前缀环境不一致 |
| Clean Session=true 断线 | 离线窗口 QoS1 未缓存 |
| ACL 拒绝 | 发布成功但 Broker 未转发（或 CONNACK 后 pub 被拒） |
| 慢消费者队列满 | `max_queued_messages` 丢弃 |
| 桥接/规则失败 | EMQX 动作错误未重试成功 |
| 通配符误用 | 订阅 `prod/device/#` 实际发到 `prod/devices/...` |

## 排查步骤

1. **确认 QoS**：发布与订阅是否 ≥1；是否被降为 0（见 [A5](../01-面试篇/A5-qos-semantics.md)）。
2. **同源验证**：`mosquitto_sub -h <broker> -t <精确主题> -q 1 -v`（开发 Mosquitto）；生产用 **影子 Client** 同 ACL。
3. **查 ACL/认证日志**：EMQX Dashboard 鉴权失败；Mosquitto `acl` 拒绝。
4. **会话**：ClientID 是否被抢连；Clean Session 与离线时长。
5. **桥接**：规则命中计数、Pulsar producer 错误率（[C4](../03-运维篇/C4-bridge.md)）。
6. **抓包/调试**：`-d` 或协议日志看 PUBLISH 是否到达 Broker。

## 解决

- 关键链路改 **QoS1 + 幂等消费**；必要时 QoS2 仅用于极少数控制 topic。
- 统一 **主题规范**（[B4](../02-开发篇/B4-multi-service-conventions.md)）；发布前集成测试断言 topic。
- 需离线必达：`cleanSession=false` + Broker 队列上限调优 + 设备重连退避。
- 修 ACL/证书；桥接失败修 Pulsar 并 **补偿重放**（按时间窗口）。
- 调大或监控 `max_queued_messages`；加速消费者（[P4](P4-slow-backlog.md)）。

## 预防

- 代码评审检查 **QoS 默认值**（Paho 常为 0）。
- CI 用 Mosquitto 跑 **pub/sub 集成测试**；上生产前 EMQX 影子主题对账。
- 监控：订阅端业务 ACK 与 Broker `messages_out` 比率。
- 文档化 retain/遗嘱 与 普通消息 边界（[P8](P8-retain.md)）。

## 相关链接

- [A5 QoS](../01-面试篇/A5-qos-semantics.md) | [B9 排障](../02-开发篇/B9-troubleshooting.md)
- [C4 桥接](../03-运维篇/C4-bridge.md) | [C10 Runbook](../03-运维篇/C10-failure-runbook.md) | [P7 离线](P7-offline-message.md)
