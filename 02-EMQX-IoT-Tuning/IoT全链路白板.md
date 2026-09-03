# IoT 全链路白板（面试用 · 脱敏）

> 详版代码级梳理：[`IoT业务流程梳理.md`](IoT业务流程梳理.md)  
> 组件清单：[`生产服务清单.md`](../01-K8s-Troubleshooting/生产服务清单.md)  
> **栈特征**：iot-server 内嵌 MQTT 网关 + **EventBus** 分发（JetLinks 系）；设备主链路 **不经 Pulsar**。  
> **第二条接入线**：**GIIC over CoAP-TCP**（15W 压测主证据）→ [`GIIC-15万压测参与复盘.md`](GIIC-15万压测参与复盘.md)

---

## §1 一句话（HR 30 秒）

认证后 **TCP 在 Pod 内存**，**Redis 存 connectionServerId 路由**；上报进 **EventBus** 写 **ES/MySQL**，下行经 **Redis+RPC** 找正确 Pod 再下发。接入协议可以是 **MQTT:1883**，也可以是 **GIIC CoAP-TCP**——进平台后都汇到 **DeviceMessage → EventBus**。

---

## §2 总览图（技术面 90 秒 · 照着讲）

### 2.1 MQTT 主路径（默认口述）

```text
┌──────────┐     TCP:1883      ┌─────────┐   stream透传   ┌────────────────────────────────────┐
│  设备端   │ ───────────────► │ MetalLB │ ─────────────► │ iot-web(nginx) → iot-server Pod     │
└──────────┘                   │   VIP   │                  │                                     │
                               └─────────┘                  │ MqttServerDeviceGateway             │
                                                            │   → Protocol 解码                   │
                                                            │   → DeviceMessageConnector          │
                                                            │        → EventBus                   │
                                                            │          ├─ TimeSeriesWriter → ES   │
                                                            │          ├─ LatestDataService → MySQL│
                                                            │          ├─ StateSync → MySQL       │
                                                            │          ├─ 规则/数据流/级联         │
                                                            │          └─ WebSocket → 前端        │
                                                            └────────────────────────────────────┘
                                                                       │        │        │
                                                                       ▼        ▼        ▼
                                                                    MySQL    Redis      ES
```

**接入路径（口述补一句）**：`设备 mqtt:1883 → MetalLB → nginx(iot-web) TCP 透传 → iot-server:1883`

### 2.2 GIIC / CoAP-TCP 路径（压测主线 · 追问时展开）

```text
压测/设备 ──CoAP-TCP──► nginx/LVS（**sysctl + Stream 代理调优**）──► iot-server
                                      │ CoAP TCP Gateway（per-connection 队列）
                                      │   PSK → Login → HB/Data/Refresh
                                      │   协议包 L1 热缓存 + Token Redis
                                      ▼
                                   DeviceMessage → DeviceMessageConnector → EventBus → …
                                      │
                                   MySQL（生产档 cnf） / Redis
```

| 与 MQTT 相同 | 与 MQTT 不同 |
|--------------|--------------|
| 解码后都进 **EventBus**；会话路由仍靠 **Redis** | 协议是 **CoAP-TCP + PSK/Token**；网关有 **按连接队列**；热路径有 **L1 / Token async** |
| 持久化仍 ES/MySQL；入口同样可走 Nginx TCP | 压测证据规模：**15W × ≥96h**；入口/库专项见 [`GIIC-全栈运维优化要点.md`](GIIC-全栈运维优化要点.md) |

**口述补一句**：两条接入线，**汇合点在 DeviceMessageConnector / EventBus**；15W 还要记得 **入口临时端口 + MySQL 连接池**，别只讲业务 jar。

---

## §3 五层职责（面试分层）

| 层 | 组件 | 干什么 | 不干什么 |
|----|------|--------|----------|
| 接入 | MetalLB + iot-web(nginx) / **GIIC 入口 Nginx** | 对外 VIP、**TCP 透传/代理**；15W 场景含 **sysctl + hash(ip+port) + 防摘流** | 不解码业务协议 |
| 网关 | MqttServer / **CoAP-TCP Gateway** | 连接、认证、收包、**按产品协议解码** | 不直接写 ES 业务表 |
| 业务中枢 | EventBus + 规则/数据流/级联 | 设备消息 **发布订阅**、上下线事件、业务编排 | 不替代持久化组件 |
| 持久化 | MySQL / ES / Redis | 元数据、最新值、在线、时序、会话；**MySQL 按内存选生产档**；GIIC Token HASH | 不做协议解析 |
| 展现 | WebSocket `/api/messaging` | 实时推前端（含超级设备拓扑 `update_line`） | 不直连设备 |

---

## §4 上行（设备 → 平台）— 五阶段口述版

| 阶段 | 做什么 | 关键类/机制 |
|------|--------|-------------|
| **1 连接认证** | clientId 作设备 ID → 注册中心取设备 → 协议包 `authenticate` → 注册会话 | `MqttServer#handleConnection`、`DeviceSessionManager`；**MySQL** 元数据，**Redis** 会话/集群 |
| **2 解码** | PUBLISH → 协议 `MessageCodec#decode` → `DeviceMessage`；超级设备有能力预处理 | `VertxMqttConnection`、`MqttServerDeviceGateway#decodeAndHandleMessage` |
| **3 总线** | 解码后统一进 **EventBus**；上下线也发总线 | `DeviceMessageConnector`；topic 如 `/device/{productId}/{deviceId}/reportProperty`、`online`/`offline` |
| **4 持久化** | 三分工：ES 时序、MySQL 最新值+在线状态（**批量缓冲写**）、Redis 缓存/限流/统计 | `TimeSeriesMessageWriterConnector`、`DatabaseDeviceLatestDataService`、`DeviceMessageBusinessHandler` |
| **5 实时** | EventBus → WebSocket → 浏览器 | 超级设备拓扑 `update_line` → 空间管理页 |

---

## §5 下行（平台 → 设备）与会话三层

### 5.1 下行步骤

```text
API / 规则引擎
  → ClusterSendToDeviceMessageHandler
  → 本 Pod localSessions 有会话？→ 直接 PUBLISH
  → 无会话：Redis 读 connectionServerId → 集群 RPC 到目标 Pod → PUBLISH
```

### 5.2 会话三层（口述加分项）

| 层 | 是什么 | 记住一句 |
|----|--------|----------|
| **① JVM** | `localSessions` → `VertxMqttConnection` → **TCP 长连接** | **只有这层能发 MQTT** |
| **② Redis** | `device.online` 写 `connectionServerId`、`sessionId`（`ConfigStorageManager`） | **集群路由索引** |
| **③ H2 文件** | `./data/sessions/{clusterId}`，`PersistenceDeviceSessionManager` | 重启恢复 **元数据**，**TCP 仍要设备重连** |

```text
内存(TCP) ──变更时写──► Redis(路由) ──可选──► H2(元数据落盘)
```

### 5.3 多副本一句话

设备连在 **Pod-A**；管理平台打到 **Pod-B** 时，经 **Redis 查 connectionServerId** + **RPC 转发到 Pod-A** 再下发。

详图：[`IoT业务流程梳理.md`](IoT业务流程梳理.md) §7.2（Mermaid）

---

## §6 EventBus 典型 topic（脱敏模式）

> 原理与三种订阅方式、集群 broker、vs Pulsar：[`EventBus-原理与现网用法.md`](EventBus-原理与现网用法.md)

| Topic 模式 | 含义 |
|------------|------|
| `/device/{productId}/{deviceId}/reportProperty` | 属性上报 |
| `/device/.../online`、`/offline` | 上下线 |
| `/device/.../update_line` | 超级设备节点拓扑变化 |

---

## §7 存储分工（面试表格式）

| 存储 | 存什么 | 机制要点 |
|------|--------|----------|
| **MySQL** | 设备实例、产品、网关配置、最新属性表、在线状态 | 在线状态 **缓冲批写**，防高并发打爆 DB |
| **Elasticsearch** | 属性历史、事件、日志等 **时序消息** | `TimeSeriesMessageWriterConnector` 订阅 `/device/**` |
| **Redis** | **connectionServerId 路由**、缓存、限流、鉴权 | 下行寻 Pod；**不替代 TCP 会话** |
| **H2 本地文件** | 会话元数据 `PersistenceDeviceSessionManager` | Pod 重启不恢复 Socket，设备需重连 |

---

## §8 规模与我负责（2026-07 更新 · 四问）

| 项 | 内容 |
|----|------|
| **设备连谁** | ① **MQTT TCP 1883** → MetalLB → nginx 透传 → **内嵌 MqttServer**；② **GIIC CoAP-TCP** → 同集群网关（压测经 LVS/nginx） |
| **上报路径** | 协议解码 → **DeviceMessageConnector → EventBus** → ES/MySQL/规则/级联；**设备上报不经 Pulsar 第一跳** |
| **Pulsar 角色** | 与设备主链路 **解耦**；**级联**等场景走 Pulsar；40 万级口径作平台背景，非个人主证据 |
| **设备规模 / 压测** | **主证据**：GIIC **15W 在线 × 长稳 ≥96h（4×24h）**，你负责协议/网关段；详见复盘。平台「40 万级」= 背景协助，勿混讲 |
| K8s | 单例集群；iot-web **多副本** + MetalLB VIP（口述按现网） |
| **我负责** | **iot-server**：GIIC 网关/协议热路径；**协助** `docs/ops` 入口 Nginx/sysctl、MySQL 生产档；**禁改** `device-manager` |

### 8.1 白板口述加分：禁改边界怎么说

> EventBus 入口在 `DeviceMessageConnector`。我们曾想对 GIIC 做 header 短路和 fire-and-forget，但 **device-manager 模块政策不能改**，所以那两刀永久不做；压测靠 **网关与协议侧** 卸压，这是工程取舍不是技术不会。

### 8.2 白板口述加分：为啥还要动运维层

> 长连接经 Nginx 全代理时，容器出站 **临时端口** 会耗尽（errno 99）；粘滞只用源 IP 会把少机压测打爆单后端。库侧要 **buffer + max_connections 与应用池联动**，不能靠关刷盘骗吞吐。现网说明在 `docs/ops`，面试摘要见运维要点文。

---

## §9 与 PLAN/画像差异（面试诚实口径）

| 文档曾写 | 现网梳理 |
|----------|----------|
| 上报走 **Pulsar** | 设备主链路：**内置 MQTT / GIIC → EventBus**；Pulsar 用于 **级联** 等 |
| EMQX 独立 Broker | 现网 **iot-server 内嵌 MqttServer**，nginx 只做透传 |
| 压测主数字 40W | **面试主数字用 GIIC 15W×96h**；40W 仅背景 |

---

## §10 口述自检

- [ ] 不看稿 **90 秒**讲完 §2.1 + §4 表头五阶段
- [ ] 能补一句 **§2.2 GIIC 汇合到 EventBus**
- [ ] 能答：**会话三层**（内存 TCP / Redis 路由 / H2 元数据）
- [ ] 能答：多副本下行怎么找到正确 Pod（Redis + RPC）
- [ ] 能答：压测规模用 **15W**，且提到 **入口/MySQL** 不只 jar
- [ ] 已脱敏（客户名、真实 productId 可泛化）
