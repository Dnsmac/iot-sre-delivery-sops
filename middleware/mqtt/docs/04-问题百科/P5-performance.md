# P5 吞吐不够 / 性能差

> 深度：已深化 | Mosquitto 开发 + EMQX 生产

## 现象

- CPU 飙高、延迟上升、TPS **达不到容量目标**。
- 连接能建立但 **发布超时** 或频繁断开。
- 单机 Mosquitto 到 **千级 TPS** 即瓶颈（预期行为）。
- EMQX 集群扩容后 TPS **线性不佳**。

## 常见原因

| 原因 | 说明 |
|------|------|
| QoS2 过多 | 四次握手开销 |
| Payload 过大 | 带宽与 GC |
| TLS 卸载不当 | CPU 花在加解密 |
| 规则/桥接同步 | 阻塞投递路径 |
| 磁盘 IO | persistence/autosave |
| 压测方法错 | 单机 Client 瓶颈 |
| 热点 fan-out | 单 topic 上万订阅 |

## 排查步骤

1. 区分 **连接瓶颈** vs **消息瓶颈**（[C11](../03-运维篇/C11-loadtest-connections.md)）。
2. `top`/Prometheus 看 **user/sys/wait**；是否 iowait 高。
3. 对比 QoS0 vs QoS1 TPS；调 `max_inflight`（[C3](../03-运维篇/C3-broker-tuning.md)）。
4. 检查 **TLS 会话复用**、cipher 套件。
5. 减少 Dashboard 刷新与 debug 日志。

## 解决

- 遥测默认 **QoS0**；关键用小 topic QoS1。
- 缩 Payload、启用 **Topic Alias**（MQTT 5.0）。
- 水平扩 EMQX；Pulsar 增加 partition。
- 调 OS 参数、`ulimit`（[C3](../03-运维篇/C3-broker-tuning.md)）。
- 拆分热点主题；共享订阅平衡消费者。

## 预防

- 上线前 **阶梯压测** 归档基线。
- 架构评审禁止 **大图传 MQTT**。
- 监控 TPS/连接数/CPU 三角关系。

## 相关链接

- [C2 容量](../03-运维篇/C2-capacity.md) | [C3 调优](../03-运维篇/C3-broker-tuning.md) | [C11 压测](../03-运维篇/C11-loadtest-connections.md)
- [A12 性能](../01-面试篇/A12-performance-scale.md) | [B10 调优](../02-开发篇/B10-performance-tuning.md)
