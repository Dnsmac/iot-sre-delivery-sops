# C11 十万连接压测

> 优先级: **P3 运维** | 预计阅读 40 分钟 | 深度：已深化

## 本章解决什么问题

定义 **大规模 MQTT 连接压测** 的方法论：为何必须 EMQX 集群、如何阶梯加压、观测哪些指标、本仓 Java 工具如何用；避免在 Mosquitto 开发机上得出「MQTT 只能 500 连接」的错误结论。

---

## 面试常问

1. 为什么 10W 连接不能用 Mosquitto 单机验证？
2. 压测 ClientID 为什么要唯一？
3. Keep Alive 对压测结果有什么影响？
4. 如何模拟真实设备上报而不仅是空连接？
5. 压测通过标准如何定义？

---

## 核心知识

### 前置条件

| 项 | 要求 |
|----|------|
| Broker | EMQX 集群 ≥3 节点，[C2](C2-capacity.md) 规格 |
| 压测机 | 多台，足够 CPU/FD；分布式压测工具（emqtt-bench、MQTT-Benchmark 等） |
| 网络 | 与生产同 Region，避免跨洋 RTT |
| 本仓工具 | [ConnectionLoadTest.java](../../examples/java/mqtt-loadtest/) **仅冒烟** |

### 阶梯模型

```text
1K → 10K → 50K → 100K
每阶稳定 15~30min，记录：连接成功率、P99 连接耗时、TPS、CPU、内存、fd、丢包
```

### 参数矩阵

| 参数 | 典型范围 | 说明 |
|------|----------|------|
| QoS | 0 / 1 | 生产关键流用 1 复测 |
| Keep Alive | 60~300s | 过短心跳 CPU 高 |
| Payload | 100B~1KB | 全链路带宽 |
| 上报间隔 | 1s~60s | 决定有效 TPS |
| Clean Session | true/false | 影响会话内存 |

### 指标与门槛（示例，项目自定）

- 连接成功率 **≥99.9%**
- 稳态 CPU **<70%**（单节点）
- 发布 P99 **<200ms**（同 Region）
- 无 OOM、无 `too many open files`

### 本仓冒烟

```powershell
cd examples\java\mqtt-loadtest
mvn -q package
# 本地 Mosquitto 建议 <=500
java -jar target\mqtt-loadtest-*.jar 200 60
# 环境变量 MQTT_BROKER=tcp://emqx-lb:1883
```

---

## 生产环境注意点

- 压测主题用 **`loadtest/`** 前缀，ACL 与生产隔离。
- **禁止** 对生产未授权压测；独立 VPC 或影子集群。
- 压测后清理会话与 retain，避免污染监控。
- 结果归档供 [C2](C2-capacity.md) 与采购评审使用。
- 结合 **发布压测**：空连接只验证一半容量。

---

## 易错点与反例

1. **单机笔记本 10W 连接** — 压测机先崩。
2. **ClientID 重复** — 互踢，成功率虚假低。
3. **未开 time_wait 复用** — 客户端端口耗尽。
4. **只用 QoS0** — 生产 QoS1 内存模型不同。
5. **无预热直接 100K** — SYN flood 误判 Broker 故障。

---

## 动手验证

```powershell
cd docker; docker compose -f docker-compose-mosquitto.yml up -d
mvn -f examples\java\mqtt-loadtest\pom.xml -q exec:java `
  -Dexec.mainClass=com.demo.mqtt.loadtest.ConnectionLoadTest `
  -Dexec.args="50 10"
```

观察 `ok=` 与 `elapsed=` 输出；Docker `stats` 看 Mosquitto 内存。

---

## 相关章节

- [C2 容量](C2-capacity.md) | [C3 调优](C3-broker-tuning.md) | [C8 HA](C8-ha-cluster.md)
- [B11 性能验证](../02-开发篇/B11-performance-verification.md) | [P5 吞吐](../04-问题百科/P5-performance.md)
