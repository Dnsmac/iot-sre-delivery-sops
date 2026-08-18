# 附录 B：MQTT 与相关协议对照

> 用于架构选型评审与面试「为什么不用 XXX」。

---

## 总览对照表

| 维度 | MQTT 3.1.1/5 | HTTP/1.1 | WebSocket | CoAP | gRPC |
|------|----------------|----------|-----------|------|------|
| 传输 | TCP（常见 TLS） | TCP/TLS | TCP 升级 | UDP | HTTP/2 |
| 模式 | Pub/Sub | 请求/响应 | 双向帧 | 请求/响应 + Observe | RPC 流 |
| 头部开销 | 2 字节起 | 数百字节级 | 帧封装 | 极简 | 二进制+HTTP/2 |
| 实时下发 | Broker 推送 | 需轮询/Webhook | 同 WS | Observe 通知 | 服务端流 |
| 可靠语义 | QoS 0/1/2 | 依赖 TCP | 依赖 TCP | CON/NON/ACK | 依赖 HTTP/2 |
| 状态 | 会话、订阅持久 | 无状态为主 | 有连接 | 无连接 UDP | 有连接 |
| 典型场景 | IoT 海量设备 | API、OSS | 浏览器实时 | 窄带传感器 | 微服务内部 |
| 生态 | EMQX、Paho | 通用 | 浏览器+MQTT over WS | libcoap | 云原生 |

---

## 选型决策树

```
需要浏览器直连 Broker？
├─ 是 → MQTT over WebSocket（或 HTTP 轮询作备选）
└─ 否 → 继续

设备是否极窄带、UDP 仅可用？
├─ 是 → CoAP（或 LwM2M）
└─ 否 → 继续

是否海量长连接 + 双向、小报文？
├─ 是 → MQTT（主流 IoT）
└─ 否 → HTTP/gRPC 更简单

是否微服务间强类型 RPC、低延迟？
├─ 是 → gRPC（非替代 MQTT 设备接入）
└─ 否 → 按团队栈
```

---

## 与 Kafka / Pulsar 的关系

| | MQTT | Kafka/Pulsar |
|---|------|----------------|
| 定位 | 设备接入、最后一跳 | 数据中心总线、持久日志 |
| 消息模型 | Topic 路由、无内置长期日志消费组 | Partition、offset、保留策略 |
| 常见集成 | EMQX 规则引擎桥接 | MQTT → Pulsar 再流处理 |

**实践：** 设备 → MQTT Broker → 规则引擎 → Pulsar；应用侧复杂计算在 Pulsar，不在 MQTT callback 内完成（[C4](../03-运维篇/C4-bridge.md)）。

---

## 面试一句话

- **实时双向、百万设备、小报文** → MQTT。  
- **偶发配置、无长连接** → HTTP。  
- **浏览器** → WebSocket 承载 MQTT 或 REST。  
- **UDP 超低功耗局域网** → CoAP。  
- **服务间 RPC** → gRPC，与 MQTT 设备层互补。

---

## 相关

- [A1](../01-面试篇/A1-what-is-mqtt.md) | [A2](../01-面试篇/A2-architecture.md) | [C4 桥接](../03-运维篇/C4-bridge.md)
