# A1 MQTT 是什么

> 优先级: **P1 面试** | 预计阅读 25 分钟 | 深度：已深化 | 学习路径：**D1 | 面试：★★★ 开场必背** | 主路径：[学习路径](../学习路径.md)

## 本章解决什么问题

> **今日（D1）下一步：** 读完本章 + [A2](A2-architecture.md) → 画架构图 → 背 [30 秒开场](../学习路径.md#四面试开场30-秒--2-分钟--5-分钟)。

弄清 MQTT **不是某个产品**，而是物联网常用的 **发布/订阅消息协议**；能回答「为什么设备侧用 MQTT 而不是 HTTP」，以及版本选型（3.1.1 vs 5.0）。

---

## 面试常问

1. MQTT 和 HTTP/WebSocket 有什么区别？为什么 IoT 用 MQTT？
2. MQTT 是标准吗？有哪些版本？
3. MQTT 能保证消息不丢吗？
4. MQTT 和 Kafka/Pulsar 是什么关系？
5. 什么场景不适合 MQTT？

---

## 核心知识

**MQTT**（Message Queuing Telemetry Transport）= 轻量 **发布/订阅** 协议，面向 **低带宽、不稳定网络、嵌入式资源少** 的设备。

| 维度 | MQTT | HTTP/REST | WebSocket |
|------|------|-----------|-----------|
| 模式 | Pub/Sub，解耦 | 请求/响应 | 全双工，常仍应用层自定 |
| 连接 | 长连接 | 短连接为主 | 长连接 |
| 报文开销 | 小（固定头 2 字节起） | 头、Cookie 大 | 依赖上层帧 |
| 服务端推送 | Broker 按主题推送 | 需轮询或另建 WS | 可推，无主题路由语义 |
| 适用 | 遥测、指令、状态 | API、页面 | 实时 Web、游戏 |

### 版本

| 版本 | 地位 |
|------|------|
| **3.1.1** | 工业主流，本仓主线，面试默认 |
| **5.0** | 原因码、用户属性、共享订阅、会话过期等 — 见 [A10](A10-mqtt5-advanced.md) |

### 生态角色

```
设备/边缘 --MQTT--> Broker(Mosquitto/EMQX) --桥接/规则--> Pulsar/Kafka/DB
```

- **协议**：规定 CONNECT、PUBLISH、QoS 等。
- **Broker**：实现协议的服务（Mosquitto、EMQX、HiveMQ 等）。
- **客户端库**：Paho、各语言 SDK。

---

## 面试标准答案

### 题：MQTT 和 HTTP 有什么区别？为什么 IoT 常用 MQTT？

> MQTT 是发布订阅、长连接、报文头很小的协议，适合设备频繁上报小数据、服务端主动下发指令。HTTP 是请求响应，每次交互开销大，设备要收推送往往要轮询或另建 WebSocket，耗电和流量都不如 MQTT。所以物联网遥测、在线状态、下行控制常用 MQTT 连 Broker，再由 Broker 桥接到数据中心的消息系统。

### 题：MQTT 能保证不丢消息吗？

> 不能笼统说保证。MQTT 有 QoS0/1/2 三档：QoS0 可能丢，QoS1 至少一次但可能重复，QoS2 协议层恰好一次但开销大。还要结合 Clean Session、Broker 配置、网络断线。业务上关键链路一般用 QoS1 加幂等，不能默认「用了 MQTT 就不丢」。

---

## 生产环境注意点

- 选型先定 **3.1.1 还是 5.0**（设备固件与 Broker 要一致）。
- 接入层 MQTT，分析层 Kafka/Pulsar，**不要**让设备直连 Kafka。
- 监控按 **连接数、发布速率、主题前缀** 分租户。

---

## 与 Pulsar/Kafka 的差异

| | MQTT | Pulsar/Kafka |
|---|------|----------------|
| 主要场景 | 设备接入 | 数据中心流处理 |
| 消息模型 | 主题路由、无内置长期日志 | 分区日志、消费位点 |
| 关系 | 常作为 **上游协议** | **下游存储与计算** |

---

## 易错点与反例

1. **把 MQTT 当 MQ 产品名** — 错；EMQX 是产品，MQTT 是协议。
2. **全 QoS0 却业务要求必达** — 协议层已允许丢包。
3. **设备直连 Kafka** — 协议、证书、资源都不匹配，应经 Broker/网关。
4. **用 HTTP 轮询模拟推送** — 耗电、延迟差，非 MQTT 优势场景。

---

## 动手验证

```powershell
cd docker; docker compose -f docker-compose-mosquitto.yml up -d
mosquitto_pub -h localhost -t dev/test -m "hello"
mosquitto_sub -h localhost -t dev/test -C 1
```

Java：[HelloMqtt.java](../../examples/java/mqtt-basics/src/main/java/com/demo/mqtt/HelloMqtt.java)

---

## 相关章节

- [A2 架构](A2-architecture.md) | [A5 QoS](A5-qos-semantics.md) | [附录 B](../附录/B-protocol-comparison.md)
