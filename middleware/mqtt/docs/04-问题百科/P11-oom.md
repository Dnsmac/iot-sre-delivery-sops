# P11 Broker / 客户端 OOM

> 深度：已深化 | 链 [P5 性能](P5-performance.md)、[C10 Runbook](../03-运维篇/C10-failure-runbook.md)

## 现象

- Broker 或 Java 接入服务 **内存持续上涨** 后进程被 kill（`OOMKilled`）。
- 连接数正常但 **heap/GC 频繁**，Full GC 后仍高。
- Mosquitto 容器退出码 137；EMQX 节点反复重启。

## 常见原因

| 原因 | 说明 |
|------|------|
| 连接过多 | 每连接会话、订阅树、inflight 占内存 |
| 离线队列堆积 | Clean Session false + QoS1 且消费慢 |
| 超大 Payload | 单条消息 MB 级 |
| `#` 订阅 fan-out | 单条消息复制上万份 |
| Java callback 队列无界 | 业务线程池 `LinkedBlockingQueue` 无上限 |
| retained 海量 | 每主题 retain 虽一条，主题数爆炸 |
| 持久化缓冲 | autosave、桥接堆积 |

## 排查步骤

1. 区分 **Broker OOM** vs **Java 接入 OOM**（容器/Pod 名称、进程）。
2. 看连接数、订阅数、**inflight/queue** 指标（EMQX Dashboard / `$SYS`）。
3. Java：`jmap -heap`、MAT 看是否 **byte[]/MqttMessage** 堆积。
4. 查是否有 **无界队列**、同步阻塞导致消息在内存积压。
5. 临时：**限连接数、限 max_queued_messages、缩 Payload**。

## 解决

- Broker：调 `max_connections`、`max_queued_messages`、队列策略；水平扩容 EMQX。
- Java：`ThreadPoolExecutor` 有界队列 + 拒绝策略；减小 payload；异步化 callback。
- 设计：热点 topic 拆分、禁止全网 `#`、可丢数据改 QoS0。

## 预防

- 容量规划含 **每连接内存粗算**（[C2](../03-运维篇/C2-capacity.md)）。
- 压测同时打 **连接 + 消息**（[C11](../03-运维篇/C11-loadtest-connections.md)）。
- 告警：堆内存 >80%、队列深度、连接增长率。

## 相关

- [B9 场景4 callback](../02-开发篇/B9-troubleshooting.md) | [B10 L1](../02-开发篇/B10-performance-tuning.md) | [P10 K8s](P10-k8s.md)
