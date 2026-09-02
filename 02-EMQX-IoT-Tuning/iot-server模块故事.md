# iot-server 模块故事（IoT 主炮 · 5 分钟版）

> **用途**：回答「你在 iot-server 上具体改过什么」——把「改过链路、讲不清」变成「我改了 X 类，从 ~5k 挂到 15W 长稳」。
> **代码核对（只读）**：`D:\gerrit\iot-server`，禁止改现网仓；类名来源 [`IoT业务流程梳理.md`](IoT业务流程梳理.md)。
> **主故事线**：[`GIIC-15万压测参与复盘.md`](GIIC-15万压测参与复盘.md) §3 时间线（r1–r8）。
> **口述稿**：[`../05-Interview-Prep/口述稿/W5-模块.md`](../05-Interview-Prep/口述稿/W5-模块.md)

---

## §0 六要素（面试主表）

| 节 | 一句话 |
|----|--------|
| 边界 | iot-server = **接入网关 + 协议解码 + EventBus 分发**；**不**做独立 Broker（内嵌 MqttServer），**不**直写 ES/MySQL 业务表 |
| 现象 | GIIC 压测 **~5k 即挂**（Login 超时 / Sink 断流），中期卡 **~14.3W** |
| 排查 | 分层：**入口 → 网关 → 协议热路径 → Redis → MySQL**，不是「机器不够」 |
| 改动 | per-connection / L1 热缓存 / Token 迁 Redis / Login 减负 / async 批写 / SCAN 替 KEYS |
| 结果 | **15W 在线长稳 ≥96h（4×24h）**，超验收节点 72h |
| 原理 | Netty/Reactor 背压、连接治理、Redis 热点、会话三层 |

---

## §1 边界（先立好，别被追问打穿）

**iot-server 负责**：
1. 接入：内嵌 `MqttServer`（MQTT:1883）+ CoAP-TCP 网关（GIIC 线）——不是独立 EMQX。
2. 认证：`MqttServer#handleConnection` → 用 `clientId` 当设备 ID → `ProtocolSupport#authenticate` 按产品协议包认证。
3. 解码：`MqttServerDeviceGateway#decodeAndHandleMessage` → 协议 `MessageCodec#decode` → 统一 `DeviceMessage`。
4. 分发：`DeviceMessageConnector` → **EventBus**，下游（ES 时序 / MySQL 最新值 / 规则 / 级联 / WebSocket）都订阅总线。

**iot-server 不负责**：
- **不**做独立 Broker（MQTT 网关内嵌在 JVM，nginx 只做 TCP 透传）。
- **不**直写业务表：ES 由 `TimeSeriesMessageWriterConnector`、MySQL 由 `DeviceMessageBusinessHandler` / `DatabaseDeviceLatestDataService` 分工。
- **不**替代 Redis：`ConfigStorageManager` 只存 `connectionServerId` 路由索引，TCP 本体永远在 Pod 内存 `localSessions`。

> **一句话防穿**：我改的是「接入 + 热路径」，不是把 ES/MySQL/Redis 全改成我的方案；三层分工没动。

---

## §2 现象（真实可追问）

| 阶段 | 症状 |
|------|------|
| 优化前 | **~5k 连接** 就出现 Login 超时、Sink 断流 |
| 中期 | 优化后爬到 **~14.3W** 卡死，上不去 15W |

**关键判断（说给面试官）**：卡在 14.3W 不是「机器不够」，是**四类问题叠加**——
① 全局单管道 Sink 背压整网；② 热路径 Registry/Redis/DB 风暴；③ 跨节点 L1 token 不一致误杀；④ Login 写 configuration 放大。

---

## §3 排查（分层 · 有步骤非空话）

按 `入口 → 网关 → 协议 → Redis → MySQL` 五层定位：

| 层 | 典型症状 | 我怎么看 |
|----|----------|----------|
| 入口 | errno 99、no live upstreams、少 IP 打爆单机 | Nginx 日志 + 内核临时端口水位 |
| 网关管道 | Sink 断流、全局背压 | 连接队列积压、reject 计数 |
| 协议热路径 | Login 风暴、access 不匹配 | Login 耗时、L1 hit/miss、Token 权威源 |
| Redis | OPS 不高但延迟尖刺 | `slowlog`：`KEYS dfx:*`、大 HSET |
| MySQL | 库连接顶满、热路径写放大 | 连接池等待 + 慢 SQL（写 configuration 放大） |

> **结论一句**：瓶颈在「架构性背压 + 热点放大」，不是单点堆内存或 CPU，所以加机器只缓不治。

---

## §4 改动（我亲手改的 · 按 r1–r8）

| 轮次 | 改了什么 | 对应的类/配置 |
|------|----------|--------------|
| v1 | 抽公共 `handleExchange`；**per-connection** 拆连接队列；L1 热缓存；热路径 Skip 多余 persist | `giic.connection-model=per-connection`、`giic.cache.*` |
| r2 | Login grace / LVS 漂移兜底；压测配置 = 上线配置 | `giic.security.psk-grace-ms` |
| r3 | L1 miss 与 hit 对称 reload，防 stale loader 写回 | `giic.cache.*` |
| r4 | invalidate 异步；冷 Login 减 headers；`setConfigs` 批量写 | Login persist 减负 |
| r5 | **Token 权威迁 Redis HASH**（离开 configuration 大字段） | `giic.token.persist-mode` |
| r6 | Refresh 后 prevAccess 宽限 | — |
| r7 | L1 先回 200 + Redis 异步批写（可回滚 sync） | `giic.token.persist-mode=async` |
| r8 | PENDING overloaded 日志限频；抬高 batch/concurrency/capacity | 异步刷盘队列加固 |
| 旁路 | `RedisScanUtils.smartKeys`：**SCAN 优先、失败再 KEYS** | 公共工具类 |

**协助段（不算我 owner）**：入口 Nginx TCP + 内核 sysctl；MySQL 生产档 cnf + 连接池联动（见 [`GIIC-全栈运维优化要点.md`](GIIC-全栈运维优化要点.md)）。

**禁改边界（必须主动说）**：
- `device-manager` 模块**政策禁止改**——`refactorHeader` skip、`event-bus-fire-and-forget` 两刀已回滚、永不合入。
- 所以「EventBus 那刀」靠**网关/协议/Redis 侧卸压**顶住，这是工程取舍，不是不会。

---

## §5 结果（数字 · 背书）

| 指标 | 优化前 / 中期 | 优化后 |
|------|---------------|--------|
| 在线规模 | ~5k 挂；中期卡 ~14.3W | **15W（5×30k 线程）可长稳** |
| 长稳时长 | 30min 冒烟不足 | **连续 96h（4×24h）**，超 72h 验收 |
| 手段分层 | — | 入口 Nginx/sysctl → 网关 per-connection → L1/Token Redis → SCAN/MySQL 档 |

**证据**：`evidence/giic-15w-jmeter-dashboard-2026-07-23.png`（JMeter Dashboard · GIIC Heartbeat · 5×30k 线程水位平坦）。

---

## §6 原理补课（被追问时的 30 秒弹药）

1. **为什么 per-connection？** 全局单管道 = 一个慢消费者背压所有连接；拆成每 TCP 独立队列，Sink 满则 reject，隔离故障。
2. **Token 为什么迁 Redis？** 原来存 configuration 大字段，Login 每次读写放大；迁 Redis HASH 后 L1 先回、权威源异步批写，挂靠 reload/宽限兜底。
3. **KEYS vs SCAN？** `KEYS` 阻塞式扫全库，压测统计前缀拖慢 Redis；`SCAN` 游标式分页，公共工具 `smartKeys` 先 SCAN 失败再 KEYS。
4. **会话三层（常问）**：TCP 本体在 `localSessions`（内存）→ Redis 存 `connectionServerId` 路由 → H2 存元数据（重启不恢复 Socket）。

---

## §7 面试 90 秒（可背）

> iot-server 是接入网关，内置 MQTT 和 CoAP-TCP 网关，解码后统一进 EventBus。我最近负责 GIIC（CoAP-TCP）15 万长连接压测：优化前几千连接就 Login 超时、Sink 断流，中期卡在 14 万出头。排查是分层的——入口端口耗尽、全局单管道背压、Login 写配置放大、Redis 热点，四类问题叠加。我做了按连接拆队列、协议侧 L1 热缓存、Token 迁 Redis 异步批写，公共工具 KEYS 改 SCAN；入口 Nginx/sysctl 和 MySQL 生产档是协助对齐。有一块 device-manager 政策不能改，EventBus 那刀没上，靠网关侧卸压顶住。到 7 月下旬，15 万在线已经连续长稳 96 小时，超过 72 小时验收节点。整个平台 40 万方案我不是 owner，我负责的是这条接入线。

---

## §8 自检

- [ ] 不看稿 5 分钟讲完 §0 六要素 + §7
- [ ] 能说清 3 个类名：`handleConnection` / `decodeAndHandleMessage` / `DeviceMessageConnector`
- [ ] 能主动说「device-manager 禁改」且不慌
- [ ] 结果数字：15W × 96h，不吹 40W / HA50w
- [ ] 已脱敏（客户名、真实 productId 泛化）
