# A4 报文与连接流程

> 优先级: **P1 面试** | 预计阅读 30 分钟 | 深度：已深化 | 学习路径：**D2 | 面试：★★★** | 主路径：[学习路径](../学习路径.md)

## 本章解决什么问题

能画出 **CONNECT → 业务 → DISCONNECT** 全流程，说清主要报文作用，以及 CONNACK 拒绝、QoS 握手报文与 [A5](A5-qos-semantics.md) 的关系。

---

## 面试常问

1. MQTT 有哪些主要报文类型？
2. CONNECT 里一般带哪些关键字段？
3. CONNACK 返回码有哪些常见值？
4. QoS1 和 QoS2 分别用到哪些报文？
5. 正常断开和异常断开对遗嘱有何影响？

---

## 核心知识

### 主要报文（3.1.1）

| 报文 | 方向 | 作用 |
|------|------|------|
| CONNECT | C→B | 建连：ClientId、Clean Session、Keep Alive、认证、遗嘱 |
| CONNACK | B→C | 接受(0)或拒绝(非0) |
| PUBLISH | 双向 | 承载 payload；含 QoS、retain |
| PUBACK | 双向 | QoS1 确认 |
| PUBREC / PUBREL / PUBCOMP | 双向 | QoS2 四步握手 |
| SUBSCRIBE / SUBACK | C→B / B→C | 订阅及结果（每 filter 一个 QoS） |
| UNSUBSCRIBE / UNSUBACK | C→B | 取消订阅 |
| PINGREQ / PINGRESP | 双向 | 保活探测 |
| DISCONNECT | C→B | 正常下线（3.1.1 部分实现弱，5.0 正式） |

### 连接生命周期

```
TCP/TLS 建立
  → CONNECT
  → CONNACK (0=成功)
  → [SUBSCRIBE → SUBACK]*
  → PUBLISH / 接收 PUBLISH
  → [QoS1: PUBACK] [QoS2: PUBREC→PUBREL→PUBCOMP]
  → 周期 PINGREQ ↔ PINGRESP（无业务报文时）
  → DISCONNECT（建议正常退出，避免误触发遗嘱）
```

### CONNECT 关键字段（概念）

| 字段 | 说明 |
|------|------|
| ClientId | 会话标识；重复常互踢 |
| Clean Session | true 断线清会话；false 可持久化 QoS1/2 状态 |
| Keep Alive | 秒；0 表示不断开检测（慎用） |
| Username/Password | 认证 |
| Will | 异常断开时 Broker 代发 |

### CONNACK 常见返回码

| 码 | 含义 |
|----|------|
| 0 | 连接已接受 |
| 1 | 不可接受的协议版本 |
| 2 | ClientId 被拒绝 |
| 3 | Broker 不可用 |
| 4 | 用户名或密码错误 |
| 5 | 未授权 |

### QoS 与报文

| QoS | 额外报文 |
|-----|----------|
| 0 | 无 |
| 1 | PUBACK |
| 2 | PUBREC → PUBREL → PUBCOMP |

---

## 面试标准答案

### 题：描述 MQTT 从连接到收消息的过程

> 客户端先建立 TCP 或 TLS，发 CONNECT 报文带上 ClientId、Clean Session、Keep Alive 和可选的账号密码、遗嘱。Broker 回复 CONNACK，返回码 0 表示成功。之后客户端可以 SUBSCRIBE 主题过滤器，Broker 用 SUBACK 确认。发布方 PUBLISH 到具体主题，Broker 路由给匹配的订阅者。若 QoS 是 1，订阅方处理前要完成 PUBACK 握手；QoS2 则四次握手。连接空闲时靠 PINGREQ/PINGRESP 保活。正常退出应发 DISCONNECT，避免遗嘱误报。

### 题：QoS2 为什么慢？

> 因为每条消息要 PUBLISH、PUBREC、PUBREL、PUBCOMP 四次交互，Broker 和客户端都要维护状态机，吞吐远低于 QoS1。海量遥测一般不用 QoS2，除非强一致且量小。

---

## 生产环境注意点

- 抓包或 Broker 日志对照报文，比猜应用日志快。
- 认证失败先看 CONNACK 码，不要只看「连不上」。
- 负载均衡后的 TLS 终止点要配好 **session stickiness**（若 Broker 集群有状态）。

---

## 易错点与反例

1. **只认 TCP 连通，不看 CONNACK** — 可能协议版本或认证失败。
2. **SUBSCRIBE 未完成就 publish** — 订阅端收不到，竞态问题。
3. **进程 kill -9 后期望不触发遗嘱** — 异常断连会触发遗嘱。
4. **Keep Alive=0** — 死连接可能长期占资源。

---

## 动手验证

```bash
# 订阅侧看 CONNACK/SUBACK（mosquitto 客户端 -d 调试）
mosquitto_sub -h localhost -t dev/trace -d -q 1
mosquitto_pub -h localhost -t dev/trace -m ping -q 1
```

---

## 相关章节

- [A5 QoS](A5-qos-semantics.md) | [A6 会话](A6-session-keepalive.md) | [A7 Retain/遗嘱](A7-retain-will.md)
