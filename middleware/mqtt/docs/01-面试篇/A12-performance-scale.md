# A12 性能与规模

> 优先级: **P1 面试** | 预计阅读 25 分钟 | 深度：已深化 | 学习路径：**D6 | 面试：★★★** | 主路径：[学习路径](../学习路径.md)

## 本章解决什么问题

回答 **能撑多少连接、消息速率受什么限制**；能把优化层次说到 **L0 设计（Topic/QoS/频率）** 而不只调参数。

---

## 面试常问

1. MQTT 单机大概能多少连接？
2. 影响吞吐的因素有哪些？
3. 10W 设备架构怎么画？
4. QoS 对性能影响？
5. 如何压测 MQTT？

---

## 核心知识

### 瓶颈层次

```
L0 Topic/QoS/上报频率/Payload 设计  ← 最大头
L1 聚合、压缩
L2 连接分布、Broker 集群
L3 客户端库参数
L4 Broker 配置
L5 网络与硬件
```

### 粗算带宽

```
带宽 ≈ 设备数 × (1/上报间隔) × (MQTT头 + payload)
例：10W × 0.1 msg/s × 500B ≈ 50MB/s（再加协议与 ACK 开销）
```

### 10W 连接架构（概念）

```
设备 → LB → EMQX 集群 → 规则引擎 → Pulsar
         ↑
    多节点水平扩展，非 Mosquitto 单机
```

### QoS 与性能

| QoS | 性能 |
|-----|------|
| 0 | 最高 |
| 1 | 中等，有 ACK |
| 2 | 最低，四步握手 |

---

## 面试标准答案

### 题：如何支撑 10W 设备在线？

> 接入层用 EMQX 等集群 Broker，前面负载均衡，会话与消息水平扩展。设计上遥测用 QoS0 或 1、控制面用 QoS1，上报间隔和 payload 要控小，避免每秒大 JSON。后端通过桥接或规则进 Pulsar 做存储和计算。压测要分连接数、消息速率、QoS 组合测，见 C11 和 ConnectionLoadTest。

### 题：连接数够但 CPU 高怎么办？

> 先看是否 QoS2 滥用、payload 过大、规则引擎同步阻塞、或 `#` 订阅导致 fan-out 爆炸。再调 Broker 线程与持久化；最后才加机器。

---

## 生产环境注意点

- 压测环境 **≈ 生产 Broker 类型**。
- 监控连接数、inflight、堆积、桥接延迟。

---

## 易错点与反例

1. **只压连接不压消息** — 上线后消息路径先垮。
2. **忽略上行+下行双向流量**。
3. **callback 同步重处理** — 占满 CPU 似 Broker 慢。

---

## 动手验证

```bash
cd examples/java/mqtt-loadtest
mvn -q exec:java "-Dexec.mainClass=com.demo.mqtt.loadtest.ConnectionLoadTest" "-Dexec.args=100 10"
```

---

## 相关章节

- [B10 调优](../02-开发篇/B10-performance-tuning.md) | [C11 压测](../03-运维篇/C11-loadtest-connections.md)
