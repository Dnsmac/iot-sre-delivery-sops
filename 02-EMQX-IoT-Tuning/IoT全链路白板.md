# IoT 全链路白板（面试用 · 脱敏）

> 详版代码级梳理：[`IoT业务流程梳理.md`](IoT业务流程梳理.md)  
> 组件清单：[`生产服务清单.md`](../01-K8s-Troubleshooting/生产服务清单.md)  
> **栈特征**：iot-server 内嵌 MQTT 网关 + **EventBus** 分发（JetLinks 系）；设备主链路 **不经 Pulsar**。

---

## §1 一句话（HR 30 秒）

认证后 **TCP 在 Pod 内存**，**Redis 存 connectionServerId 路由**；上报进 **EventBus** 写 **ES/MySQL**，下行经 **Redis+RPC** 找正确 Pod 再 **MQTT 下发**。

---

## §2 总览图（技术面 90 秒 · 照着讲）

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

---

## §3 五层职责（面试分层）

| 层 | 组件 | 干什么 | 不干什么 |
|----|------|--------|----------|
| 接入 | MetalLB + iot-web(nginx) | 对外 VIP、**TCP 透传** 1883 到 iot-server | 不解码 MQTT、不做业务 |
| 网关 | MqttServerDeviceGateway、MqttServer | 连接、认证、收包、**按产品协议解码** | 不直接写 ES 业务表 |
| 业务中枢 | EventBus + 规则/数据流/级联 | 设备消息 **发布订阅**、上下线事件、业务编排 | 不替代持久化组件 |
| 持久化 | MySQL / ES / Redis | 元数据、最新值、在线状态、**时序历史**、会话与集群 | 不做协议解析 |
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

## §8 规模与我负责（2026-05 定稿 · 四问）

| 项 | 内容 |
|----|------|
| **设备连谁** | 对外 **MQTT TCP 1883** → MetalLB VIP → iot-web(nginx) 透传 → **iot-server 内嵌 MqttServer**（**JVM 线程**监听 1883，非独立 EMQX） |
| **上报路径** | **先进 iot-server 内置 MQTT** 解码 → **EventBus** → ES/MySQL/规则/级联等；**设备 PUBLISH 不经 Pulsar 第一跳** |
| **Pulsar 角色** | 平台有 Pulsar；与设备主链路 **解耦**。**级联**等场景走 Pulsar；40 万压测协助 **Pulsar 调优**（W6 复盘补参数） |
| 设备规模 / 压测 | 参与 **40 万级**压测（**协助**）；动过 **级联链路** + **Pulsar 调优**，非方案 owner |
| K8s | 单例集群；iot-web **3 副本** + MetalLB VIP |
| **我负责** | 日常改 **iot-server**（接入/EventBus/级联相关 Java）；具体类名与改动 **W4 模块故事** 定稿 |

---

## §9 与 PLAN/画像差异（面试诚实口径）

| 文档曾写 | 现网梳理 |
|----------|----------|
| 上报走 **Pulsar** | 设备主链路：**内置 MQTT → EventBus**；Pulsar 用于 **级联** 等场景，压测协助 **Pulsar 调优** |
| EMQX 独立 Broker | 现网 **iot-server 内嵌 MqttServer**，nginx 只做透传 |

---

## §10 口述自检

- [ ] 不看稿 **90 秒**讲完 §2 + §4 表头五阶段
- [ ] 能答：**会话三层**（内存 TCP / Redis 路由 / H2 元数据）
- [ ] 能答：多副本下行怎么找到正确 Pod（Redis + RPC）
- [ ] 已脱敏（客户名、真实 productId 可泛化）
