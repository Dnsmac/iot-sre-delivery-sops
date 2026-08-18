# A2 协议架构与角色

> 优先级: **P1 面试** | 预计阅读 20 分钟 | 深度：已深化 | 学习路径：**D1 | 面试：★★★ 开场必背** | 主路径：[学习路径](../学习路径.md)

## 面试常问

1. MQTT 有哪些角色？和消息队列有什么区别？
2. 发布者和订阅者需要知道对方吗？
3. ClientId 作用是什么？
4. Broker 内部大致做什么？
5. MQTT 如何与 Kafka/Pulsar 配合？

## 本章解决什么问题

MQTT 是 **发布/订阅协议**，不是 Broker 产品名。理解三角色与长连接模型，才能和后端 MQ（Pulsar/Kafka）正确对接。

---

## 三角色模型

```
  ┌─────────────┐         PUBLISH (topic + payload)        ┌─────────────┐
  │  Publisher  │ ───────────────────────────────────────► │ MQTT Broker │
  │ (设备/服务)  │                                        │ 路由/会话/QoS │
  └─────────────┘                                        └──────┬──────┘
                                                                 │ 匹配订阅
  ┌─────────────┐         PUBLISH (推送)                         │
  │ Subscriber  │ ◄──────────────────────────────────────────────┘
  │ (服务/设备)  │
  └─────────────┘
        ▲
        │ SUBSCRIBE (topic filter + qos)
        └──────────────────────────────────────────────────────── Broker
```

- **没有「队列」抽象**：Topic 是路由键，不是存储实体名称（存储由 Broker 实现决定）。
- **一对多广播**：一条 PUBLISH 可投递给多个匹配订阅者。
- **与 HTTP 对比：** HTTP 是请求-响应、短连接；MQTT 长连接、服务端可主动推。

---

## 连接生命周期（必讲）

```
TCP 连接
  → CONNECT (ClientId, Clean Session, KeepAlive, 可选用户名密码, 可选遗嘱)
  → CONNACK (接受/拒绝)
  → [SUBSCRIBE → SUBACK]  可多次
  → PUBLISH / 接收 PUBLISH
  → PINGREQ ↔ PINGRESP（保活）
  → DISCONNECT（建议正常退出）
```

**ClientId：** 逻辑客户端身份。同 ClientId 新连接常 **踢掉** 旧连接（Broker 配置 `allow_duplicate_clientid` 等）。

---

## Broker 内部（概念层）

| 模块 | 作用 |
|------|------|
| 连接管理 | 会话、认证、Keep Alive |
| 主题路由 | 将 PUBLISH  fan-out 到订阅树 |
| QoS 状态机 | inflight、重传、离线队列 |
| 持久化 | QoS1/2、Retain、会话（视配置） |

**Mosquitto：** 轻量，单机，适合开发。  
**EMQX：** 集群、规则引擎、桥接、10W+ 连接。

---

## 面试标准答案

### 题：MQTT 架构是怎样的？

> MQTT 是发布订阅协议。发布者把消息发到某个主题，Broker 根据主题名把消息路由给所有订阅了匹配主题的客户端，发布者和订阅者解耦。客户端先通过 TCP 建立连接，发送 CONNECT 报文做认证和会话协商，之后可以订阅多个主题过滤器，也可以向主题发布消息。Broker 负责维护会话状态、QoS 确认、离线消息和 Retain 消息。和 Kafka 这类日志型 MQ 不同，MQTT 更偏物联网接入，常作为设备到云的协议，再通过桥接进数据中心的消息系统。

---

## 与 Pulsar 对接（你们场景）

```
设备 --MQTT(QoS1)--> EMQX/Mosquitto --桥接/规则--> Pulsar Topic (Key=deviceId)
```

见 [C4 桥接](../03-运维篇/C4-bridge.md)。

---

## 动手验证

```powershell
cd docker; docker compose -f docker-compose-mosquitto.yml up -d
mosquitto_sub -h localhost -t 'dev/#' -v
mosquitto_pub -h localhost -t dev/test -m hi
```

---

## 相关

- [A4 报文](A4-packets-connect-flow.md) | [A5 QoS](A5-qos-semantics.md)
