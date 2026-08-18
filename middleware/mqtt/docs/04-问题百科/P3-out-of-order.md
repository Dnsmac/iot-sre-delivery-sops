# P3 消息乱序

> 深度：已深化 | Mosquitto 开发 + EMQX 生产

## 现象

- 同一设备事件在下游 **时间戳倒挂**（先收到关机再收到开机）。
- 指令执行顺序错误（先 `#reset` 后 `#config` 却先执行 reset）。
- 多订阅者看到的顺序 **不一致**。

## 常见原因

| 原因 | 说明 |
|------|------|
| 多连接多线程 | 设备双连接或应用多线程 publish |
| QoS 与并发 | 不同 Packet ID 并行 inflight |
| 共享订阅 | `$share` 多消费者并行 |
| 桥接无 Key | 写 Pulsar 未按 deviceId 分区 |
| 跨主题 | 状态与事件分 topic，消费合并错序 |
| Broker 集群 | 极少见实现差异，多以客户端/下游为主 |

## 排查步骤

1. 确认是否 **单连接单线程** 发布；查 ClientID 是否重复。
2. 订阅端是否 **共享订阅** 或 Kafka 多 partition 无序消费。
3. Pulsar/Kafka **MessageKey** 是否为 deviceId（[C4](../03-运维篇/C4-bridge.md)）。
4. 抓包看同 topic 的 **发布顺序** 与 Broker 出站顺序。
5. 检查 Payload 内 **seq** 是否连续。

## 解决

- 单设备 **单连接**；应用层串行 publish 队列。
- 需要并行消费时：Payload 带 **version/seq**，下游排序缓冲。
- Pulsar 生产指定 **Key=deviceId**；单分区 topic 仅用于全局序要求极高的控制流。
- 控制类主题与遥测 **分 topic**，控制流 QoS1 单消费者。
- 避免多规则重复写同一下游。

## 预防

- 主题设计文档注明 **有序性要求** 与分区策略。
- 集成测试：连续发 N 条 seq，断言消费顺序。
- MQTT 5.0 **流控** 与 inflight=1 用于强序场景（权衡吞吐）。

## 相关链接

- [A5 QoS](../01-面试篇/A5-qos-semantics.md) | [C4 桥接](../03-运维篇/C4-bridge.md)
- [B4 多服务规范](../02-开发篇/B4-multi-service-conventions.md) | [P2 重复](P2-duplicate.md)
