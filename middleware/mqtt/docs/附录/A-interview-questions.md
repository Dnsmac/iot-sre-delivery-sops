# 附录 A：MQTT 面试题精选（Top 15）

> **路径：** D7~D8 集中刷 | **配合：** [学习路径 §四 面试开场](../学习路径.md#四面试开场30-秒--2-分钟--5-分钟)  
> 每题 3~5 句答法；先读 Part A 对应章再背，避免只会背题不会追问。

---

## 面试开场（先背这个，再刷 15 题）

完整模板见 **[学习路径 · 第四节](../学习路径.md#四面试开场30-秒--2-分钟--5-分钟)**。

| 版本 | 何时用 | 要点 |
|------|--------|------|
| **30 秒** | 自我介绍 | MQTT 3.1.1、Pub/Sub、Paho、QoS1+幂等、Mosquitto/EMQX、排障划界 |
| **2 分钟** | 「做过 MQTT 吗」 | 背景→架构→我做的→难点（用 P1 项目填 `{}`） |
| **5 分钟** | 架构面 | 2 分钟 + QoS 表 + 会话 + TLS + 10W 粗算 + 与 Pulsar 分工 |

**15 题与 28 天路径对应：**

| 题号 | 建议学习日 | 追问链 |
|------|------------|--------|
| 1~3 | D1 | 选型 → 架构 |
| 4~5 | D2~D3 | 报文 → QoS |
| 6~8 | D3~D4 | QoS → 幂等 → 会话 → 断连 |
| 9~10 | D4 | 遗嘱/Retain |
| 11 | D2 | 通配符 |
| 12~13 | D5 | 安全/Broker |
| 14 | D6 | 规模 |
| 15 | D22 | MQTT5 加分 |

---

## 1. MQTT 是什么？解决什么问题？

MQTT 是面向物联网的 **发布/订阅** 消息协议，运行在 TCP 之上，报文头极小，适合带宽窄、设备多的场景。它解决的是 **海量终端与云端双向通信**（遥测上报、指令下发），而不是替代 HTTP 做一次性 REST 调用。核心实体是 Broker、Publisher、Subscriber，彼此通过 **主题（Topic）** 解耦。详见 [A1](../01-面试篇/A1-what-is-mqtt.md)。

---

## 2. MQTT 和 HTTP 有什么区别？何时选 MQTT？

HTTP 是请求/响应、无状态，每次交互头部大，服务端难主动推送到设备。MQTT 长连接 + Pub/Sub，适合 **设备常在线、云端频繁下发、每秒多条小消息**。若仅是偶尔配置同步、无长连接需求，HTTP 更简单。选型见 [附录 B](B-protocol-comparison.md)、[A2](../01-面试篇/A2-architecture.md)。

---

## 3. 描述 MQTT 架构中的角色与数据流

设备或应用作为 Client 连接 **Broker**；发布者 publish 到某 topic，Broker 按订阅关系转发给所有匹配订阅者。Broker 不解析业务 payload，只做路由、会话与 QoS 状态机。多服务间通过 **约定 topic 层级** 集成，见 [A2](../01-面试篇/A2-architecture.md)、[B4](../02-开发篇/B4-multi-service-conventions.md)。

---

## 4. CONNECT 报文里哪些字段最重要？

**ClientId** 标识会话，冲突会导致互踢；**Clean Session** 决定断线后是否保留订阅与 QoS1 离线队列；**Keep Alive** 约定心跳间隔，超时 Broker 断开；**Username/Password** 或 TLS 证书用于认证。遗嘱（Will）也在 CONNECT 时注册，异常断线时 Broker 代发。详见 [A4](../01-面试篇/A4-packets-connect-flow.md)、[A6](../01-面试篇/A6-session-keepalive.md)。

---

## 5. QoS0、QoS1、QoS2 各保证什么？

QoS0 **至多一次**，可能丢，无 ACK。QoS1 **至少一次**，有 PUBACK，可能 **重复**，消费必须幂等。QoS2 **恰好一次**（在会话与实现正确前提下），四步握手，吞吐最低。生产遥测常用 QoS0，关键指令常用 QoS1+幂等，QoS2 极少整网使用。详见 [A5](../01-面试篇/A5-qos-semantics.md)、[P2](../04-问题百科/P2-duplicate.md)。

---

## 6. 为什么 QoS1 必须幂等？

因为网络闪断或 PUBACK 丢失时 Broker 会 **重传 PUBLISH**，客户端自动重连也会重投未确认消息。协议保证的是「至少送达一次」，不是「只处理一次」。幂等实现常用业务 messageId、DB 唯一键或 Redis `SET NX`。开发见 [B9 场景2](../02-开发篇/B9-troubleshooting.md)。

---

## 7. Clean Session true 和 false 区别？

`true`：连接断开时 Broker **清除** 该 ClientId 的订阅与未传递的 QoS1/2 消息（MQTT 3.1.1 语义）。`false`：会话持久，重连后恢复订阅并接收离线期间排队消息（受队列上限限制）。需要「上线必收到离线指令」应 false + 稳定 ClientId + QoS1。详见 [A6](../01-面试篇/A6-session-keepalive.md)、[P7](../04-问题百科/P7-offline-message.md)。

---

## 8. Keep Alive 设多少合适？和断连的关系？

Keep Alive 是客户端承诺在间隔内向 Broker 发 PINGREQ 的最大秒数；Broker 超时未收到则断开。过小增加流量与 CPU，过大在 NAT/LB 下 TCP 可能已死而应用不知。常见 **60–300s**，须小于负载均衡 idle 超时。callback 阻塞导致无法及时 PING 也会断连，见 [B9 场景4](../02-开发篇/B9-troubleshooting.md)。

---

## 9. 遗嘱（LWT）是什么？误触发怎么防？

遗嘱在 CONNECT 时注册，客户端 **异常断开**（未发 DISCONNECT）时 Broker 向指定 topic 发布预设消息。用于设备离线告警。误触发常因进程 kill、ClientId 冲突、测试脚本未 disconnect。正常下线应 `disconnect()`；MQTT5 可用 Will Delay。见 [A7](../01-面试篇/A7-retain-will.md)。

---

## 10. Retain 消息的作用与风险？

Retain 使 Broker 对该 topic 保留 **最后一条**，新订阅者立即收到，适合「最后已知状态」。风险是陈旧数据未清除导致误判在线。清除用 **空 payload + retain 标志** 发布。勿对高频遥测使用 retain。见 [A7](../01-面试篇/A7-retain-will.md)、[P8](../04-问题百科/P8-retain.md)。

---

## 11. 主题通配符 `+` 和 `#` 怎么用？生产忌讳什么？

`+` 匹配单层，`#` 匹配多层剩余，且 `#` 只能在过滤器末尾。生产忌讳服务订阅 `prod/#` 导致 **全量流量** 打向单消费者、Broker CPU 飙升。应按租户/类型收窄，见 [A3](../01-面试篇/A3-topics-wildcards.md)、[B9 场景10](../02-开发篇/B9-troubleshooting.md)。

---

## 12. MQTT 安全怎么做？

传输层 **TLS**（8883 或 WSS）；认证用用户名密码、JWT 或客户端证书；授权用 Broker **ACL** 按 topic 前缀限制 publish/subscribe。生产禁止匿名。MQTT5 有更细的错误码与属性。见 [A8](../01-面试篇/A8-security.md)、[C6](../03-运维篇/C6-security-ops.md)。

---

## 13. Mosquitto 和 EMQX 怎么选？

Mosquitto 轻量开源，适合 **本地开发、小规模、桥接实验**。EMQX 面向 **大规模连接、集群 HA、规则引擎、企业 ACL 与监控**。10W 长连接应 EMQX 集群而非 Mosquitto 单机。见 [A11](../01-面试篇/A11-broker-implementations.md)、[B12](../02-开发篇/B12-environment-models.md)。

---

## 14. 10 万 MQTT 连接要考虑什么？

粗算带宽 = 设备数 × 上报频率 × 报文大小；选集群 Broker + LB；统一 Keep Alive 与 NAT；遥测 QoS0+聚合，关键流 QoS1；禁止 `#` 全网订阅；压测在目标 Broker 签字。见 [A12](../01-面试篇/A12-performance-scale.md)、[B10](../02-开发篇/B10-performance-tuning.md)。

---

## 15. 共享订阅（MQTT 5 / EMQX）解决什么问题？

多个消费者订阅同一逻辑主题时，普通订阅会 **每条消息每人一份**；共享订阅把消息 **负载均衡** 到组内成员，用于水平扩展处理。需 Broker 支持。与 Kafka 消费组概念类似但语义不同。见 [A10](../01-面试篇/A10-mqtt5-advanced.md)、[B5](../02-开发篇/B5-high-volume-notes.md)。

---

## 扩展题索引（Part A）

| 范围 | 章节 |
|------|------|
| 报文与连接 | A4, A6 |
| Payload 与格式 | A9 |
| MQTT 5 | A10 |
| 桥接与运维 | A11, Part C |

**下一页：** [学习路径](../学习路径.md) · [STUDY-TRACKER](../STUDY-TRACKER.md)
