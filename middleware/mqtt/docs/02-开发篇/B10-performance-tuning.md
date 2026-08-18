# B10 性能调优

> 优先级: **P2 开发** | 预计阅读 35 分钟 | 深度：已深化

## 本章解决什么问题

设备规模从百到 **十万连接**、消息从秒级遥测到高频告警时，瓶颈可能出现在 topic 设计、QoS、payload、连接模型、Paho 参数、Broker 配置或网络任一层次。本章给出 **L0–L5 调优金字塔**（MQTT 特化）、**决策树**、**参数对照表** 与 **10 万设备粗算**，避免在 L5 调 TCP 窗口而忽略 L0 全网 `#` 订阅。验证方法见 [B11](B11-performance-verification.md)；环境差异见 [B12](B12-environment-models.md)。

---

## 面试常问

1. 10 万 MQTT 长连接，Broker 怎么选？→ 集群 EMQX/HiveMQ，非 Mosquitto 单机。
2. QoS0/1/2 对吞吐的影响？→ 0 最快，2 最慢且占 inflight。
3. 为什么 inflight 满会「发不动」？→ QoS1 未 PUBACK 占窗口。
4. 聚合上报的代价？→ 降 publish 次数、增延迟，告警需独立 topic。
5. Keep Alive 越小越好吗？→ 否，需与 NAT/LB 协调，过小增 PING 开销。

---

## 核心知识：调优金字塔（L0–L5）

```
                    ┌─────────────────────────────┐
                    │ L5 网络：带宽、MTU、TLS卸载   │ ★★
                    └──────────────┬──────────────┘
                    ┌──────────────▼──────────────┐
                    │ L4 Broker：连接上限、队列、   │ ★★
                    │ 桥接、共享订阅、持久化        │
                    └──────────────┬──────────────┘
                    ┌──────────────▼──────────────┐
                    │ L3 客户端 Paho：maxInflight、 │ ★★★
                    │ reconnect、持久化目录         │
                    └──────────────┬──────────────┘
                    ┌──────────────▼──────────────┐
                    │ L2 连接模型：集群+LB、分片、  │ ★★★★
                    │ 边缘汇聚、多连接策略          │
                    └──────────────┬──────────────┘
                    ┌──────────────▼──────────────┐
                    │ L1 Payload：大小、聚合、压缩、  │ ★★★★★
                    │ 二进制编码、字段裁剪          │
                    └──────────────┬──────────────┘
                    ┌──────────────▼──────────────┐
                    │ L0 业务设计：Topic 层级、QoS、  │ ★★★★★
                    │ 上报频率、会话、禁止 # 全网   │
                    └─────────────────────────────┘
```

**原则：** 先自上而下排除 L0–L1；若 Mosquitto 单机已 CPU 100%，在 L4 换集群前改 L0 往往只能线性小幅改善。

### L0 业务设计（MQTT 特有）

| 维度 | 10W 设备建议 | 反例 |
|------|----------------|------|
| Topic | `prod/{tenant}/{deviceId}/telemetry` 分层，ACL 按前缀 | `deviceId` 作唯一层级且无租户隔离 |
| QoS | 遥测 QoS0；指令/告警 QoS1 + 幂等 | 全 QoS2 或全 QoS1 |
| 频率 | 温湿度 10–60s 聚合一条；告警独立流 实时 | 1Hz × 10W 裸发 |
| 订阅 | 服务按租户前缀订阅 `+/telemetry` | 单服务 `prod/#` |
| 会话 | 需离线才 `cleanSession=false` | 全持久会话撑爆队列 |
| Retain | 仅最后状态类 topic | 高频遥测 retain |

### L1 Payload 与聚合

- 目标单条 **256B–1KB**；JSON 字段名生产可用短 key。
- 设备或边缘 **N 条采样 / T 秒** 打一条 batch（见 [B5](B5-high-volume-notes.md)）。
- 图片/固件走对象存储 + MQTT 只传 URL/版本号。
- 压缩：gzip/lz4 在边缘做，注意 Broker `message_size_limit`。

### L2 连接模型（10W 设备）

| 项 | 说明 |
|----|------|
| Broker | **EMQX / HiveMQ 集群** + TCP LB（或 DNS 轮询 + 粘性可选） |
| 连接分布 | 10W 长连接 ≈ 每节点 1–2W（视规格）；水平扩节点 |
| 边缘网关 | 子设备经网关汇聚，对外 **1 连接 : N 设备**，降连接数 |
| ClientId | 全局唯一，防互踢 |
| 开发误区 | Mosquitto 单机压到 1K 连接 ≠ 生产 10W 结论 |

**带宽粗算（必会）：**

```
有效带宽 ≈ 设备数 × (1/上报间隔秒) × (MQTT固定头 + topic + payload)
例：100_000 设备 × 0.1 msg/s（10s 一条）× 500B ≈ 5 MB/s 载荷
加协议头、QoS1 重传、TLS 开销，规划常按 2–3× 余量
若改为 1 msg/s × 500B → 约 50 MB/s 级，需集群与网络专线
```

### L3 Paho / 客户端参数

见下表「参数对照」；与 [附录 D](../附录/D-performance-params.md)、[附录 C](../附录/C-paho-cheatsheet.md) 联动。

### L4 Broker

- `max_connections`、`max_queued_messages`、会话过期、规则引擎 worker。
- 共享订阅扩展消费并行度（MQTT 5 / EMQX）。
- 持久化：磁盘 IOPS 与 autosave 间隔（Mosquitto）vs EMQX 内置存储。
- 详见 [C3](../03-运维篇/C3-broker-tuning.md)、[C2](../03-运维篇/C2-capacity.md)。

### L5 网络

- TLS 终止在 LB vs 透传；证书握手 CPU。
- 跨 AZ 流量费与延迟；MQTT 长连接宜 **同 AZ 亲和** 或就近接入点。
- MTU、弱网模拟压测（见 [B11](B11-performance-verification.md)）。

---

## 参数对照表

| 参数 | 层级 | 典型范围 | MQTT 影响 |
|------|------|----------|-----------|
| 上报间隔 | L0 | 10–300s 遥测 | 线性决定 msg/s |
| QoS | L0 | 0/1/2 | 0 无 ACK；2 四段握手最慢 |
| topic 深度 | L0 | 4–6 层 | 过深略增匹配成本 |
| payload | L1 | <1KB 优先 | 超限拒发或断连 |
| 聚合条数 N | L1 | 10–100 | publish 次数 ÷N |
| 连接数 | L2 | 10W | 决定集群节点数 |
| `keepAliveInterval` | L3 | 60–300s | 过小 PING 多；过大 NAT 断 |
| `connectionTimeout` | L3 | 30s | 建连慢失败 |
| `maxInflight` | L3 | 10–100 | QoS1 窗口，大则占内存 |
| `automaticReconnect` | L3 | true | 闪断恢复；配合退避 |
| `cleanSession` | L0/L3 | 按产品 | false 增 Broker 队列 |
| Mosquitto `max_connections` | L4 | 开发 <1K | 单机上限 |
| EMQX 节点规格 | L4 | 按厂商表 | CPU/内存/FD |
| `max_queued_messages` | L4 | 数千–万 | 慢消费丢消息 |
| TLS | L5 | 8883 | CPU 与握手延迟 |

---

## 决策树

### 树 A：「慢 / 断连 / 发不动」

```
入口：客户端体感慢或 connectionLost 频繁
│
├─ messageArrived / publish 同步阻塞 > 数百 ms？
│   └─ 是 → L0 无关，先 L3 有界线程池（[B9 场景4](B9-troubleshooting.md)）
│
├─ inflight 满 / publish 阻塞？
│   ├─ QoS2 过多 → 降为 QoS1/0（L0）
│   └─ maxInflight 过小 → 适度调大并测内存（L3）
│
├─ Keep Alive / NAT / LB idle 不匹配？
│   └─ 协调 120s 级 KeepAlive + LB idle（L3/L5）
│
├─ ClientId 冲突互踢？
│   └─ 规范 ID（L2）
│
└─ 单机 Mosquitto CPU 已饱和？
    └─ 是 → L4 换 EMQX 集群 + L0 减 # 订阅与 QoS2（勿只调 kernel）
```

### 树 B：「丢消息 / 吞吐不达标」

```
入口：丢包或 msg/s 低于容量目标
│
├─ 业务容忍丢？
│   ├─ 否却用 QoS0 → L0 改 QoS1 + 幂等
│   └─ 是 → 保持 QoS0 + 聚合降量（L1）
│
├─ 离线必达却 cleanSession=true？
│   └─ L0 false + 队列容量（L4）
│
├─ Broker 队列 drop？
│   └─ 加速消费或调 max_queued_messages + 告警（L4，[P4](../04-问题百科/P4-slow-backlog.md)）
│
├─ 订阅 prod/#？
│   └─ L0 收窄通配符（[B9 场景10](B9-troubleshooting.md)）
│
└─ 压测在 Mosquitto 得出「上限」？
    └─ 必须在 EMQX 预发重测（[B12](B12-environment-models.md)）
```

### 树 C：「10W 连接规划」

```
目标：10W 长连接 + 给定上报频率
│
├─ 粗算带宽（见上文公式）是否超过单专线？
│   └─ 是 → L1 聚合或降频；或分流多集群
│
├─ 连接是否可经边缘汇聚？
│   └─ 是 → 有效连接数下降，L2 网关模型
│
├─ Broker 节点数 = ceil(10W / 单节点安全连接数)
│   └─ 参考厂商压测报告 + [C11](../03-运维篇/C11-loadtest-connections.md)
│
└─ 监控：连接数、msg in/out、规则延迟、丢弃计数（[C5](../03-运维篇/C5-monitoring.md)）
```

---

## 面试标准答案（示例）

**问：为什么 10W 设备不建议 Mosquitto 单机？**  
答：Mosquitto 适合开发与中小规模，单进程文件描述符、路由匹配、持久化 I/O 在十万连接与中等 msg/s 下易成为硬瓶颈，且无集群 HA。10W 长连接应使用 EMQX 等集群，配合 LB、容量粗算与 [C2](../03-运维篇/C2-capacity.md) 节点规划；开发阶段可用 Mosquitto 验证 **协议与业务逻辑**，但性能结论必须在目标 Broker 重测。

**问：聚合上报会不会丢告警？**  
答：若告警与遥测同一 batch 且 batch 间隔 60s，告警可能延迟 60s。应将告警发布到 **独立 topic**、QoS1、可选不聚合，遥测走 QoS0 聚合流。

---

## 生产环境注意点

- 调优变更 **一次只动一层**（例如只改聚合间隔），对比 [B11](B11-performance-verification.md) 指标。
- QoS 从 0 升到 1 会增 Broker 存储与重传，需同时上线 **幂等**（[P2](../04-问题百科/P2-duplicate.md)）。
- `maxInflight` 增大缓解阻塞但增加断线重连时的 **重投批量**。
- 10W 压测需分布式客户端机群，见 [examples/java/mqtt-loadtest/](../../examples/java/mqtt-loadtest/) 与 [C11](../03-运维篇/C11-loadtest-connections.md)。

---

## 易错点与反例

1. **在 L5 调 MTU，却保留 `prod/#` 订阅** → CPU 仍爆。
2. **用开发 Mosquitto 的 2 万 msg/s 推算生产** → 生产 EMQX + TLS + ACL 差异大。
3. **全 QoS2 求不丢不重** → 吞吐骤降；应 QoS1+幂等。
4. **无界线程池** → OOM 后全员断连。
5. **KeepAlive=10s** 且 LB idle=60s 未协调 → 假在线或频繁 PING。

---

## 动手验证

```bash
# QoS0 粗测 publish（单客户端）
time for i in $(seq 1 5000); do
  mosquitto_pub -h localhost -t 'bench/q0' -m 'x' -q 0
done
```

```java
MqttConnectOptions opts = new MqttConnectOptions();
opts.setMaxInflight(50);  // 调前后对比 publish 阻塞率
opts.setKeepAliveInterval(120);
```

---

## 相关章节

- [B5 高并发注意点](B5-high-volume-notes.md) | [B9 排障](B9-troubleshooting.md) | [B11 验证](B11-performance-verification.md)
- [附录 D 性能参数](../附录/D-performance-params.md)
- [Part D P5 吞吐](../04-问题百科/P5-performance.md)
