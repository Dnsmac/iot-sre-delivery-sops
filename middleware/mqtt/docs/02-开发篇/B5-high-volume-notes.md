# B5 高并发与大数据量场景注意点

> 优先级: **P2 开发** | 预计阅读 35 分钟 | 深度：已深化

## 本章解决什么问题

当连接数、消息速率或 payload 体积上来之后，**QoS 选型、聚合上报、callback 线程池、背压、Broker 集群** 如何一起设计，避免「能连上但很快全员掉线」或「Broker CPU 100%」。本章不替代 [B10](B10-performance-tuning.md) 调优手册，但给出开发阶段就要遵守的 **默认策略**。

---

## 面试常问

1. 每秒上万条小报文，QoS 怎么选？
2. 10 万长连接对 Broker 意味着什么？
3. MQTT payload 最大能多大？
4. callback 慢导致断连，如何量化与修复？
5. 如何做遥测聚合而不丢告警？

---

## 核心知识

### 场景矩阵

| 场景 | 建议 | 避免 |
|------|------|------|
| 高频小报文（温湿度 1Hz） | QoS0 + 边缘/端侧 **聚合** 后 10s 一条 | 每条 QoS1 |
| 必达告警 / 固件结果 | QoS1 + 幂等 + 独立 topic | 与遥测混在同一 flood |
| 10W 长连接 | EMQX/HiveMQ 集群；统一 Keep Alive | 单节点 Mosquitto 硬扛 |
| 大 JSON / 图片 | 压缩、字段裁剪；超大走对象存储 | 单条 1MB MQTT |
| 消费慢 | 有界队列 + 线程池 + 监控丢弃 | callback 里 JDBC |

### 聚合（Aggregation）

设备或边缘网关 **本地缓冲** N 条或 T 秒，打包一次 publish：

```json
{
  "deviceId": "device001",
  "seq": 12045,
  "batch": [
    {"ts": 1716883200, "temp": 25.1},
    {"ts": 1716883201, "temp": 25.2}
  ]
}
```

效果：

- 连接数不变，**publish 次数 ÷ N**。
- Broker 主题匹配次数下降。
- 代价：秒级延迟；**告警流应独立 topic + QoS1**，不要等聚合批次。

与 [QoSDemo.java](../../examples/java/mqtt-basics/src/main/java/com/demo/mqtt/QoSDemo.java) 对照：QoS0 适合聚合后的批量，QoS1 适合 batch 里携带的 `critical` 标志或单独告警主题。

### Payload 设计

- 二进制优先于臃肿 JSON（Protobuf、CBOR）。
- 字段名在生产可用短 key 或数字 tag。
- **message_size_limit**：Mosquitto 等可配置，超限直接拒连或丢弃。
- 单条超大包会阻塞共享消费线程（[B3](B3-subscribe.md)）。

### 速率与 inflight

发布端 QoS1/2 有 **inflight 窗口**（`maxInflight`，默认 10）：

- 发太快而 Broker ACK 慢 → 阻塞或内存涨。
- 解决：降速、QoS0、聚合、或调大 maxInflight（理解内存代价）。

订阅端 inflight 同样受限于 **处理速度**；处理慢 → 堆积 → 内存 ↑ → OOM 或断连。

### callback 线程池与背压

```java
BlockingQueue<Runnable> q = new ArrayBlockingQueue<>(1000);
ExecutorService workers = new ThreadPoolExecutor(
    4, 8, 60, TimeUnit.SECONDS, q,
    new ThreadPoolExecutor.CallerRunsPolicy()); // 背压到网络线程，慎用
```

更稳妥：

- 队列满时 **记录 metric + 丢弃可丢数据**（QoS0 遥测），或
- 暂停处理并触发 **降级**，绝不在 `messageArrived` 里 sleep。

监控指标：`queue_size`、`reject_count`、`connection_lost_rate`、`publish_latency_p99`。

### 连接规模（10W 级）

- **OS**：文件描述符、TCP 参数、`somaxconn`。
- **Broker**：集群分片、连接均衡、TLS 终结在 LB。
- **Keep Alive**：过长占连接表，过短误杀弱网设备；全平台统一。
- **ClientId**：稳定、可追踪；禁止每心跳 new client。

### 与示例代码的关系

[HelloMqtt.java](../../examples/java/mqtt-basics/src/main/java/com/demo/mqtt/HelloMqtt.java) 与 [SubscribeDemo.java](../../examples/java/mqtt-basics/src/main/java/com/demo/mqtt/SubscribeDemo.java) 是 **功能正确性** 示范，不是压测基准。压测见 [B11](B11-performance-verification.md)、[C11](../03-运维篇/C11-loadtest-connections.md)。

---

## 面试标准答案

### 题：高频遥测为什么常用 QoS0？

> 因为遥测具有「下一帧覆盖上一帧」的特性，丢一两帧对趋势图影响小，而 QoS1 每条都要 PUBACK，Broker 和客户端的 CPU、磁盘持久化开销成倍增加。10 万设备每秒一条 QoS1，就是 10 万次确认往返，极易成为瓶颈。实践是 QoS0 上报，必要时边缘聚合；只有告警、抄表、指令用 QoS1。若业务说「一条都不能丢」，要追问是「不能丢」还是「不能错」，后者用 QoS1+幂等，前者还要考虑 Broker 持久化与会话，而不是单纯升 QoS。

### 题：messageArrived 慢为什么会导致全员掉线？

> 单 client 不会「全员」，但本实例会 connectionLost；若多个服务都在 callback 里阻塞，会表现为大面积延迟和随机掉线。根因是 MQTT 客户端读线程被占，心跳和读包饿死。解决办法是有界线程池、监控队列、可丢数据降级，以及水平扩展 ingress + MQ，而不是无限加线程。量化上可看 Keep Alive 间隔内 callback 最大耗时是否超过间隔的 1/3。

---

## 生产环境注意点

- 上线前定义 **每连接 publish TPS 上限** 与 **payload P99 大小**。
- 遥测与指令 **分 topic、分 QoS、分消费者**。
- Broker 开启持久化时评估 **磁盘 IOPS**（QoS1 洪峰）。
- 桥接 Pulsar 时注意 **MQTT 入站速率 vs Pulsar 写入能力**。
- 演练：单设备异常高频 publish 的 ACL 限流（EMQX 规则 / 插件）。

---

## 易错点与反例（≥3）

1. **全链路 QoS1「求稳」** — Broker 磁盘打满；反例：采样也 QoS1。
2. **无界 LinkedBlockingQueue** — OOM；反例：`new LinkedBlockingQueue<>()` 默认 Integer.MAX_VALUE。
3. **聚合批次里塞未压缩大图** — 单包超限；反例：1MB Base64 进 MQTT。
4. **10W 连接不改 OS ulimit** — 随机 accept 失败；反例：只调 Java 堆内存。
5. **压测只测 publish 不测 subscribe 处理** — 生产在消费侧崩；反例：只跑 mosquitto_pub  flood。

---

## 动手验证

1. 本地 Broker：[B6](B6-local-dev.md)。
2. 对比 QoS flood（注意勿对共享开发 Broker 长时间压测）：

```bash
# 短_burst：观察 CPU
for /L %i in (1,1,500) do @mosquitto_pub -h localhost -t dev/test/flood -m x -q 0
```

3. 运行 QoSDemo 后订阅对比延迟：`mosquitto_sub -h localhost -t dev/test/qos-demo -v`。
4. 在 SubscribeDemo 的 callback 中加 **有界队列版** 线程池（自练），对比 sleep 30s 与投递任务 的差异。
5. 阅读 [附录 D 性能参数](../附录/D-performance-params.md)、[B10](B10-performance-tuning.md)。

---

## 相关章节

- [B2 发布](B2-publish.md) · [B3 订阅](B3-subscribe.md) · [B4 Topic 规范](B4-multi-service-conventions.md)
- [A12 性能与规模](../01-面试篇/A12-performance-scale.md) · [B10 性能调优](B10-performance-tuning.md) · [B11 性能验证](B11-performance-verification.md)
