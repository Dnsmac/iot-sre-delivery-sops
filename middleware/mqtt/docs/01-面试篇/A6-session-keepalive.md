# A6 会话 Clean Session 与保活

> 优先级: **P1 面试** | 预计阅读 30 分钟 | 深度：已深化 | 学习路径：**D4 | 面试：★★★★★** | 主路径：[学习路径](../学习路径.md)

## 本章解决什么问题

理解 **会话** 在 Broker 上存什么、**Clean Session** 对离线消息的影响，以及 **Keep Alive** 与断连、遗嘱的关系。避免「QoS1 却不持久会话」的配置矛盾。

---

## 面试常问

1. Clean Session true 和 false 区别？
2. 设备离线期间的消息能收到吗？取决于什么？
3. Keep Alive 是什么？设太短/太长会怎样？
4. 同 ClientId 两个连接会怎样？
5. MQTT 5.0 会话和 3.1.1 有何不同？

---

## 核心知识

### 会话里有什么（概念）

- 订阅关系（Clean Session=false 时可能恢复）
- QoS1/2 **未确认** 的 inflight 消息
- **离线队列**（QoS1/2，受 Broker 配额限制）

### Clean Session（3.1.1）

| 值 | 断线后 |
|----|--------|
| **true** | 会话清除；未送达的 QoS1/2 离线消息**不保留**；重连需重新 SUBSCRIBE |
| **false** | 持久会话；Broker 可为该 ClientId 缓存 QoS1/2 离线消息（有上限） |

### 与 QoS 的组合（必记）

| 配置 | 离线窗口消息 |
|------|----------------|
| Clean=true + QoS1 | **可能丢**离线期间消息 |
| Clean=false + QoS1 | 有机会送达，仍受 Broker 限制 |
| 任意 + QoS0 | 不缓存离线 |

### Keep Alive

- CONNECT 声明秒数；连接上**无任何控制报文**超过 1.5×Keep Alive，Broker 可断开。
- PUBLISH、PINGREQ 等均算活动。
- **过短**：弱网/NAT 易误判死连接。
- **过长**：僵死连接占用资源。

### ClientId 冲突

- 同一 Broker 上 **相同 ClientId** 新连接通常 **踢掉** 旧连接（视 Broker 配置）。
- 多实例部署**禁止**共用同一 ClientId。

### MQTT 5.0

- **Clean Start** + **Session Expiry Interval** 替代 Clean Session，可设会话过期时间（秒），更灵活。

---

## 面试标准答案

### 题：Clean Session 怎么选？

> 如果设备需要离线后补发关键数据，应该用 Clean Session false 加 QoS1，并保证 ClientId 稳定。如果每次都是临时连接、不需要历史，用 true 更简单。很多网关用 true 因为状态在云端。不能 Clean Session true 却指望 Broker 无限缓存离线消息，这和协议语义矛盾。

### 题：设备经常断连怎么排查？

> 先看 Keep Alive 是否小于 NAT 或负载均衡的空闲超时，再看是否有相同 ClientId 互踢，再看 callback 是否阻塞导致无法及时响应 PING。结合 Broker 日志和 [B9](../02-开发篇/B9-troubleshooting.md) 场景 4、6。

---

## 生产环境注意点

- 设备：**稳定 ClientId** + 合理 Keep Alive（常 60~300s，视网络调）。
- Broker：配置 **max_inflight_messages**、**max_queued_messages** 防止单客户端拖垮。
- K8s 滚动发布时注意会话迁移（集群 Broker 要一致会话存储）。

---

## 易错点与反例

1. **Clean=true 却要求离线必达** — 语义冲突。
2. **每次连接随机 ClientId 却要持久会话** — 会话对不上。
3. **Keep Alive 5s 走 4G** — 频繁断连。
4. **微服务多副本共用一个 ClientId** — 互相踢下线。

---

## 动手验证

```bash
# 终端1：持久会话订阅
mosquitto_sub -h localhost -t dev/session -q 1 -i device001 --clean-session false
# 终端1 Ctrl+C 断开，终端2 发布，再终端1 同 ClientId 重连
mosquitto_pub -h localhost -t dev/session -m offline-test -q 1
```

---

## 相关章节

- [A5 QoS](A5-qos-semantics.md) | [P7 离线消息](../04-问题百科/P7-offline-message.md) | [P6 断连](../04-问题百科/P6-disconnect.md)
