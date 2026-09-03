# 07 Netty 与接入层

> 三行定稿（可背）· 对齐 CoAP-TCP / Reactor + 入口 Nginx 经验

## 定义

Netty 是高性能 NIO 网络框架（Reactor 线程模型：boss 接受连接、worker IO）；接入层负责连接生命周期、编解码、背压。生产上接入前还有 **Nginx TCP 代理 + 内核参数**，和业务层队列同属容量面。

## 现网有没有

**有接入层，但不止 Netty。** MQTT/HTTP 走 **Vert.x（底层 Netty）**；GIIC 主路径是 **Californium CoAP-TCP**（非 Netty）。压测核心改造：**全局单 Sink → per-connection 队列**；队列满 **reject 单连接** 而非拖死全局。入口 Nginx：`hash(ip+port)`、临时端口、`max_fails` 防误摘。

## 面试 30 秒

> 接入层要管连接数、队列和背压。GIIC CoAP-TCP 我们从全局单管道改成每条 TCP 独立队列，满则 503 reject 只影响该连接。MQTT 侧 Vert.x 也有 connection 级 reject。入口 Nginx 还要防 ephemeral port 耗尽和后端误下线。上层 Token Redis 化、L1 缓存减 DB。这是入口代理加网络层加业务热路径一起治，不单独调 JVM。

---

## 我们项目怎么做

### 1. 各协议栈真实技术栈（别全说 Netty）

| 接入 | 底层 | 网关类 |
|------|------|--------|
| GIIC CoAP-TCP | **Eclipse Californium** | `DefaultCoapTCPServer` |
| MQTT Server | **Vert.x → Netty** | `MqttServerDeviceGateway` |
| HTTP Server | **Vert.x/Netty** | `HttpServerDeviceGateway` |
| CoAP UDP | Californium | `CoAPServerDeviceGateway` |

面试被问「Netty 线程模型」：boss/worker、**不要在 IO 线程 block**——对我们 MQTT/HTTP 成立；GIIC 要补一句「Californium 自有 IO 线程，业务用 Reactor 异步」。

### 2. GIIC 背压机制（主证据）

**两种连接模型**（`giic.connection-model`）：

| 模式 | 入队 | 风险 |
|------|------|------|
| `global` | 所有请求进全局 `Sinks.Many<CoapExchange>` | 一条慢请求拖死全局 |
| `per-connection`（压测选用） | `GiicConnectionRouter` → 每连接 `GiicConnectionState` 队列 | 只 reject 该连接 |

**Per-connection 路径**：

```text
Californium IO 线程 handleRequest()
  → GiicConnectionRouter.tryRoute()
  → GiicConnectionState.tryEnqueue()
       ├─ 成功 → Gateway concatMap/flatMap 处理
       └─ 满   → rejectExchange(SERVICE_UNAVAILABLE)  // 503
  → PSK/解密 → Codec.decode → DeviceGatewayHelper
```

关键类：

- `DefaultCoapTCPServer` — 全局 `requestSink()`、`requestSinkRejectCount`
- `GiicConnectionRouter` / `GiicConnectionState` — per-connection 队列
- `CoapTcpSinkEmitSupport` — `FAIL_NON_SERIALIZED` 最多 64 次重试
- `CoapTcpGatewayTuner` — 按堆内存算 `requestSinkSize`

**默认容量**（`GiicGatewayProperties`）：

- `queueSize` 默认 16
- `maxConnections` 50000
- `requestSinkSize`：堆 1% 预算，5120~65536
- `sink-reject-on-overflow=true` → 溢出 reject 而非抛异常杀订阅

### 3. MQTT 侧背压（Netty 线）

- `VertxMqttConnection`：`messageProcessor` Sink、CONNACK reject
- 同样最终进 `DeviceGatewayHelper`，但背压实现与 CoAP-TCP 不同

### 4. 入口 Nginx + 内核（运维面）

压测全栈要点（与代码并列）：

| 层 | 典型调优 |
|----|----------|
| Nginx stream | `hash $remote_addr$remote_port consistent` 会话粘滞 |
| 内核 | `ip_local_port_range`、`somaxconn`、`tcp_tw_reuse` |
| Nginx | 临时 listen 端口扩容量、`max_fails` 防抖动摘节点 |
| JVM | 堆/GC 与 `requestSinkSize`、连接数联动 |

详见 [`GIIC-全栈运维优化要点.md`](../../02-EMQX-IoT-Tuning/GIIC-全栈运维优化要点.md)

### 5. 业务热路径减负（接入层之上）

| 优化 | 作用 |
|------|------|
| Token Redis 化 | Login 后无 MySQL 热读 |
| L1/Caffeine 缓存 | 产品/设备元数据 |
| skip-persist 等 | 减 MySQL 放大（压测线） |
| per-connection 队列 | 防全局背压 |

---

## Netty 原理补课（JD 常问 · 通用）

**Reactor 模型**：

```text
BossEventLoop：accept 新连接
WorkerEventLoop：read/write IO
Business：丢到业务线程池，禁止 block IO 线程
```

**背压（Netty 原生）**：

- `WRITE_BUFFER_WATER_MARK`：写缓冲高低水位，触达 stop write
- `autoRead`：下游慢时暂停读
- 我们 GIIC **没用这套**，用的是 Reactor `Sinks` + 显式 reject

**成熟方案对比**：

| 机制 | 场景 |
|------|------|
| 有界队列 + reject | 我们 GIIC per-connection |
| 令牌桶限流 | API 网关 |
| Netty water mark | TCP 写背压 |
| Reactive Streams request(n) | Reactor 端到端背压 |

---

## 面试追问速答

**Q：CoAP-TCP 用 Netty 吗？**  
A：不用，Californium；MQTT/HTTP 才是 Vert.x/Netty。接入层概念统一，实现分协议。

**Q：15 万连接怎么撑住？**  
A：per-connection 队列 + Nginx 粘滞 + 内核端口 + Token Redis + 减 DB 热路径；见压测复盘。

**Q：Sink reject 和 drop 区别？**  
A：reject 给设备 503，设备可重试；silent drop 会丢请求无反馈——我们选 reject 可观测。

**Q：全局模式为什么有问题？**  
A：Californium IO 线程入队到单 Sink，一个慢 handler 堵住全部连接，压测已验证。

---

## 配置键

```yaml
giic:
  connection-model: per-connection   # 或 global
  connection:
    queue-size: 16
    max-connections: 50000
  sink-reject-on-overflow: true
```

## 诚实边界

- **主证据**：CoAP-TCP 背压、Nginx/内核、15 万压测
- **能答 Netty 理论**：boss/worker、不能 block IO 线程
- **非主责**：自研 Netty 协议栈、内核调优 owner

## 补课（可选）

- [`GIIC-15万压测参与复盘.md`](../../02-EMQX-IoT-Tuning/GIIC-15万压测参与复盘.md)
- 代码：`DefaultCoapTCPServer.java`、`GiicConnectionRouter.java`
