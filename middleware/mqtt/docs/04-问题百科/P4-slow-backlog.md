# P4 消息积压 / 消费慢

> 深度：已深化 | Mosquitto 开发 + EMQX 生产

## 现象

- 设备上报正常，业务 **延迟分钟级** 才入库。
- EMQX 规则/桥接 **队列长度** 持续上升。
- Mosquitto `mosquitto_sub` 打印明显 **滞后**；CPU 不高。
- Pulsar **backlog** 告警同时出现。

## 常见原因

| 原因 | 说明 |
|------|------|
| 下游慢 | Pulsar/DB/HTTP 写入瓶颈 |
| 消费者少 | partition 多但 consumer 实例少 |
| 单条处理重 | JSON 解析、同步 RPC |
| 规则复杂 | EMQX SQL 全量解析大 Payload |
| 慢订阅 | 客户端 `messageArrived` 阻塞 |
| max_queued_messages | 将压力堆在 Broker |

## 排查步骤

1. 分段：**MQTT 入站 TPS** vs **规则 out** vs **Pulsar lag**（[C5](../03-运维篇/C5-monitoring.md)）。
2. 临时 **绕过规则** 直 sub，判断是否规则层。
3. 看消费者线程池、GC、DB 慢查询。
4. 检查是否 **热点主题** 单 topic 百万 TPS。
5. Mosquitto：`mosquitto_sub -v` 对比 pub 时间戳。

## 解决

- 扩容 **Pulsar consumer** 或 EMQX 规则动作并行度（在支持范围内）。
- 非关键数据 **降采样**、聚合后转发。
- 优化规则：缩小 FROM、WHERE 前置过滤。
- 客户端 **异步 ack**、批量写库。
- 临时扩容 Broker 仅当 `messages_out` 也堆积（[C10](../03-运维篇/C10-failure-runbook.md) 故障2）。

## 预防

- 容量规划含 **端到端 lag SLI**（[C2](../03-运维篇/C2-capacity.md)）。
- 压测带 Payload 与真实间隔（[C11](../03-运维篇/C11-loadtest-connections.md)）。
- 告警：规则队列 + Pulsar backlog 联合。

## 相关链接

- [C10 Runbook](../03-运维篇/C10-failure-runbook.md) | [C7 规则](../03-运维篇/C7-rule-engine.md)
- [P5 性能](P5-performance.md) | [B5 高吞吐笔记](../02-开发篇/B5-high-volume-notes.md)
