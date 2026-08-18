# B11 性能验证

> 优先级: **P2 开发** | 预计阅读 30 分钟 | 深度：已深化

## 本章解决什么问题

调优（[B10](B10-performance-tuning.md)）与排障（[B9](B9-troubleshooting.md)）需要 **可重复的度量**：什么算「够快」、什么算「够稳」、如何在 Mosquitto 开发环境与 EMQX 预发之间 **对齐指标口径**。本章给出验证分层、指标定义、工具链与通过标准，避免「感觉变快了」却无法在评审会上出示数据。

---

## 面试常问

1. MQTT 性能测试要测哪些指标？→ 连接数、msg/s、P99 消费延迟、断连率、丢消息率。
2. 为什么不能在 Mosquitto 上签字 10W 容量？→ 架构与上限不同，见 [B12](B12-environment-models.md)。
3. 如何验证 callback 线程池有效？→ 对比 messageArrived 耗时 P99 与 connectionLost 次数。
4. QoS 迁移后如何验证「更少丢」？→ 影子订阅 + 对账计数 + 闪断用例。
5. 桥接性能怎么验？→ MQTT in vs Pulsar in 计数与 lag。

---

## 核心知识

### 验证分层模型

```
L1 冒烟（分钟级）     → 单连接 publish/subscribe、CLI 计数
L2 组件（小时级）     → Java 埋点、线程池、inflight 压满复现
L3 Broker（半天级）   → EMQX 控制台、$SYS、规则引擎指标
L4 端到端（天级）     → 设备仿真 N 连接 + 下游 Pulsar 对账
L5 混沌（可选）       → 断网、Broker 滚动、Pod 漂移
```

与 B10 金字塔对应：**L1–L2 验证 L0–L3 客户端改动；L3–L4 验证 L2–L4 集群与桥接。**

### 指标定义（口径统一）

| 指标 | 定义 | 采集方式 |
|------|------|----------|
| 连接成功率 | 成功 CONNACK / 尝试连接 | EMQX 仪表盘、压测脚本日志 |
| 稳态连接数 | 持续 30min 不掉线的连接 | `$SYS` 或 EMQX connections count |
| 发布吞吐 | 每秒 PUBLISH 条数（分 QoS） | Broker `messages.received` 速率 |
| 投递延迟 | publish 时间戳 → messageArrived | 应用埋点，payload 带 `ts` |
| 消费 P99 | messageArrived 处理耗时 | Micrometer / 日志采样 |
| 断连率 | connectionLost 次数 / 设备 / 小时 | 客户端 metrics |
| 丢消息率 | 发送 seq 与接收 seq 缺口 | 测试 payload 单调 seq |
| 重复率 | 去重命中 / 总条数 | 幂等存储统计 |
| 桥接 lag | MQTT 计数 − 下游计数 | 规则命中 vs Pulsar offset |
| CPU/内存 | Broker 节点资源 | Prometheus（[C5](../03-运维篇/C5-monitoring.md)） |

### 工具链

| 工具 | 用途 |
|------|------|
| `mosquitto_pub/sub` | 冒烟、单 topic 延迟肉眼验证 |
| `mosquitto_sub -t '$SYS/#'` | Mosquitto 内置统计（需配置开启） |
| EMQX Dashboard | 连接、主题、规则、慢订阅 |
| Java 埋点 | `messageArrived` 耗时、队列深度 |
| [mqtt-loadtest](../../examples/java/mqtt-loadtest/) | 多连接本地 ≤500 冒烟 |
| [C11](../03-运维篇/C11-loadtest-connections.md) | 分布式 10W 连接压测流程 |

```bash
# L1：10 秒内收条数（QoS0 发 1000 条）
mosquitto_sub -h localhost -t 'bench/verify' -q 0 -C 1000 &
sleep 1
for i in $(seq 1 1000); do mosquitto_pub -h localhost -t 'bench/verify' -m "$i" -q 0; done
wait
```

```java
// L2：payload 带时间戳，统计端到端延迟
long t0 = System.currentTimeMillis();
byte[] payload = ("{\"ts\":" + t0 + ",\"seq\":" + seq + "}").getBytes();
client.publish(topic, payload, 0, false);

@Override
public void messageArrived(String topic, MqttMessage msg) {
    long t1 = System.currentTimeMillis();
    long t0 = parseTs(msg.getPayload());
    histogram.record(t1 - t0); // 端到端 ms
    handle(msg);
}
```

---

## 面试标准答案

**问：如何设计一条「通过」标准？**  
答：在需求中写明 SLO，例如：10W 连接稳态 24h、断连率 <0.1%/设备/天、遥测 QoS0 丢包率 <0.01%（或关键流 QoS1 零缺口）、消费 P99 <200ms、桥接 lag <5s。验证时在 **预发 EMQX** 用与生产同构的 ACL/TLS，跑 L4 端到端 4–8 小时，输出仪表盘截图与脚本原始 CSV，开发 Mosquitto 仅作 L1–L2 回归。

**问：闪断重连怎么测？**  
答：压测进程运行中，对客户端网卡做 30s 断网或 iptables DROP 1883，恢复后检查：连接自动恢复、QoS1 重复率是否在幂等可接受范围、遗嘱是否误触发（[B9 场景11](B9-troubleshooting.md)）。重复率应用 dedup 指标记录，而非人工看日志。

---

## 生产环境注意点

- 压测 ClientId、topic 前缀使用 **`loadtest/`** 隔离，避免污染生产 retain 与规则。
- 禁止对生产 Broker 无审批全量 `#` 压测；在独立 namespace/集群做 L4。
- 下游 Pulsar/Kafka 也需压测，否则 MQTT 瓶颈转移后仍整体失败。
- 结果归档进 [附录 K](../附录/K-one-page-proposal-template.md)「证据」栏，支撑 [B13](B13-advocacy-change-strategy.md) 改造评审。

---

## 与 HTTP 压测的差异

| 维度 | HTTP 压测 | MQTT 验证 |
|------|-----------|-----------|
| 连接模型 | 短连接为主 | **长连接** 占主导，需 24h 稳态 |
| 语义 | 请求-响应延迟 | 发布/订阅双指标 + 订阅匹配成本 |
| 状态 | 无会话 | Clean Session、离线队列、retain |
| 工具 | ab、wrk | mqtt-loadtest、EMQX bench、自定义 Paho |

---

## 易错点与反例

1. **只测 publish 不测 subscribe** → 慢消费者导致 Broker 丢消息未被发现。
2. **QoS0 用条数对账期望零缺口** → 协议允许丢，应改 QoS1 或接受 SLO。
3. **单机笔记本 1 万连接 extrapolate 10W** → FD、CPU、网卡不满足。
4. **无预热** → 冷启动连接风暴误判 Broker 容量。
5. **忽略 TLS** → 预发裸 TCP 与生产 8883 CPU 差一倍可能。

---

## 动手验证（Checklist）

| # | 项 | 通过标准 |
|---|-----|----------|
| 1 | L1 CLI 往返 | 1000 条 QoS0 无人工中断下收齐（允许少量 QoS0 丢则标注） |
| 2 | QoS1 闪断 | 断网 30s 恢复，重复率 < 配置阈值且业务幂等 |
| 3 | 线程池 | P99 处理 <200ms，connectionLost 不随 msg/s 线性恶化 |
| 4 | inflight | 满窗口时 publish 阻塞可观测，调 maxInflight 后改善 |
| 5 | EMQX 预发 | 目标连接数 50% 稳态 4h，CPU <70% |
| 6 | 桥接 | MQTT in == Pulsar in（±幂等）持续 1h |
| 7 | `#` 订阅 | 无未审批全网 wildcard |
| 8 | 报告 | 输出 CSV + 截图，链到 Part D 对应现象 |

---

## 相关章节

- [B10 调优](B10-performance-tuning.md) | [B9 排障](B9-troubleshooting.md) | [B12 环境](B12-environment-models.md)
- [C11 连接压测](../03-运维篇/C11-loadtest-connections.md) | [附录 D](../附录/D-performance-params.md)
- [Part D P5](../04-问题百科/P5-performance.md) | [P4 积压](../04-问题百科/P4-slow-backlog.md)
