# 附录 D：MQTT 性能参数速查

> 与 [B10](../02-开发篇/B10-performance-tuning.md) 金字塔 L0–L5 对应。

---

## 业务层（L0–L1）

| 参数 | 典型值 | 影响 |
|------|--------|------|
| 上报间隔 | 10–300s 遥测 | 线性决定 msg/s |
| QoS | 0 / 1 / 2 | 可靠性 vs 吞吐 |
| payload 大小 | <1KB | Broker CPU、带宽 |
| 聚合 batch 条数 N | 10–100 | publish 次数 ÷N |
| topic 层级深度 | 4–6 | 略影响匹配 |
| retain 使用面 | 仅状态类 | 误用增存储 |

---

## Paho 客户端（L3）

| 参数 | API | 说明 |
|------|-----|------|
| maxInflight | `setMaxInflight(10–100)` | QoS1 未 PUBACK 窗口；满则 publish 阻塞 |
| keepAlive | `setKeepAliveInterval(60–300)` | 与 NAT/LB idle 协调 |
| connectionTimeout | `setConnectionTimeout(30)` | 建连超时秒 |
| cleanSession | `setCleanSession` | false 增 Broker 队列 |
| automaticReconnect | `setAutomaticReconnect(true)` | 闪断恢复 |
| maxReconnectDelay | `setMaxReconnectDelay(ms)` | 退避上限 |
| persistence | `MqttDefaultPersistence` 目录 | 断线缓存未发消息 |

---

## Mosquitto（L4 开发）

| 配置项 | 说明 |
|--------|------|
| `max_connections` | 最大连接 |
| `message_size_limit` | 单条上限 |
| `max_queued_messages` | 每客户端队列，满则丢 |
| `persistence` / `autosave_interval` | 磁盘持久化频率 |
| `listener` / `allow_anonymous` | 端口与认证 |

---

## EMQX（L4 生产）

| 类别 | 参数方向 |
|------|----------|
| 连接 | 节点最大连接、监听器 |
| 会话 | 过期时间、最大订阅数 |
| 性能 | 飞行窗口、队列长度 |
| 规则引擎 | worker 数、缓冲、重试 |
| 桥接 | QoS 映射、批量 |

详见 [C3](../03-运维篇/C3-broker-tuning.md)、厂商文档。

---

## 10W 设备粗算公式

```
带宽 ≈ N_devices × (1/interval_sec) × (header + topic + payload)
连接数规划 ≈ ceil(N_devices / 单节点安全连接数)
```

例：100000 × 0.1 msg/s × 500B ≈ 5 MB/s（再加 TLS/QoS1 余量）。

---

## 调参顺序（勿跳层）

1. 降频 / 聚合 / QoS0 遥测  
2. 缩 payload  
3. 收窄 `#` 订阅  
4. maxInflight、线程池  
5. Broker 集群与节点规格  
6. 网络 TLS 卸载  

---

## 相关

- [B10](../02-开发篇/B10-performance-tuning.md) | [B11 验证](../02-开发篇/B11-performance-verification.md) | [附录 E](E-troubleshooting-decision-tree.md)
