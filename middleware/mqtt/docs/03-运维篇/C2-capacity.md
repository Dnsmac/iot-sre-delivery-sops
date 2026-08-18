# C2 容量规划与硬件

> 优先级: **P3 运维** | 预计阅读 35 分钟 | 深度：已深化

## 本章解决什么问题

在立项或扩容前，能根据 **连接数、消息 TPS、Payload 大小、QoS 比例** 估算 CPU/内存/网卡/磁盘，并区分 Mosquitto（开发基准）与 EMQX（生产）的资源模型，避免「上线一周就 OOM」或「为 1K 连接买了 32 核」。

---

## 面试常问

1. 10 万 MQTT 连接需要多少内存？如何粗算？
2. 连接数和消息 TPS 哪个更吃 CPU？
3. QoS1 与 QoS0 对 Broker 磁盘有什么影响？
4. 文件句柄 `ulimit` 为什么要提前调？
5. 容量压测通过标准是什么？

---

## 核心知识

### 容量维度

| 维度 | 说明 | 主导资源 |
|------|------|----------|
| 并发连接 | 长连接 + 心跳 | 内存、文件句柄 |
| 连接速率 | 每秒新建 CONNECT | CPU、SYN 队列 |
| 消息 TPS | PUBLISH 入+出 | CPU、网卡带宽 |
| Payload | 单条大小 | 内存峰值、带宽 |
| QoS1/2 比例 | 持久化与 ACK | 磁盘 IOPS、内存 |
| 规则/桥接 | EMQX 规则引擎 | CPU、下游 RTT |

### 粗算公式（经验值，需压测校准）

- **内存（连接）**：EMQX 单连接约 10～50 KB（视插件、会话、飞行窗口而定）；10W 连接仅会话常需 **数 GB～十余 GB**，再加 OS 页缓存与 JVM/BEAM 堆。
- **带宽**：`TPS × 平均报文字节 × 8`；别忘了 Broker ** fan-out**（同一主题 N 个订阅者 = N 倍出口）。
- **磁盘**：QoS1/2 持久会话、`retain`、规则 offset；Mosquitto `persistence_location` 在异常断电时需可恢复。
- **文件句柄**：每连接 1～2 个 fd + 监听套接字；`ulimit -n` 建议 **连接数 × 2 + 65536** 余量。

### Mosquitto vs EMQX

| | Mosquitto 单机 | EMQX 集群 |
|---|----------------|-----------|
| 连接上限 | 数千～万级（视硬件） | 水平扩展 |
| 扩展方式 | 垂直扩容 | 加节点 + LB |
| 适用 | 本仓开发、边缘网关 | 生产全量设备 |

### 规划流程

```text
业务输入(设备数、上报间隔、QoS)
    → 算连接峰值 & TPS & 带宽
    → 选节点规格 × 副本数
    → [C11] 阶梯压测验证
    → 留 30% 冗余 + 告警阈值
```

---

## 生产环境注意点

- **峰值 ≠ 平均**：早高峰上线、OTA 批量重连要按峰值规划。
- **Keep Alive 过短** 会放大心跳 PING 流量与 CPU。
- **大 Payload**（如图片 base64）应走对象存储 + 主题传 URL，勿默认 MQTT 传文件。
- EMQX **zone** / 监听器级限流要在容量评审时写入配置基线。
- 与 [C5 监控](C5-monitoring.md) 联动：`emqx_connections_count`、`messages_rate` 达 70% 容量触发扩容评审。

---

## 易错点与反例

1. **只按设备台数算连接，忽略网关汇聚** — 一网关下挂 500 子设备可能只占 1 个 MQTT 连接。
2. **QoS 全 2** — 吞吐骤降，CPU 用于四次握手，容量表失效。
3. **未压测连接建立速率** — 促销零点 5 万设备同时重连打满 `listener` accept 队列。
4. **容器 memory limit = request** — 无 burst 余量，GC 即 OOMKilled。
5. **忽略桥接下游** — Broker 够快但 Pulsar 写不动，表现为 [P4](../04-问题百科/P4-slow-backlog.md)。

---

## 动手验证

```powershell
# 本仓冒烟（勿在生产 Mosquitto 上大跑）
cd examples\java\mqtt-loadtest
mvn -q exec:java -Dexec.mainClass=com.demo.mqtt.loadtest.ConnectionLoadTest -Dexec.args="100 60"

# 观察句柄（Linux）
# lsof -p $(pgrep emqx) | wc -l
```

记录模板：连接数、成功数、P99 延迟、CPU%、内存 RSS、丢包率 → 写入容量评审表。

---

## 相关章节

- [C11 压测](C11-loadtest-connections.md) | [C3 调优](C3-broker-tuning.md) | [C8 HA](C8-ha-cluster.md)
- [附录 D 性能参数](../附录/D-performance-params.md) | [A12 性能规模](../01-面试篇/A12-performance-scale.md)
