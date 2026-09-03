# 05 CoAP 与多协议

> 三行定稿（可背）· **与你主证据强相关**

## 定义

CoAP 是受限设备常用的请求/响应协议（UDP 或 TCP）；物联网平台常多协议接入（MQTT、CoAP、HTTP、私有 TCP），**解码后统一成内部消息模型**。

## 现网有没有

**有。** 平台支持 MQTT（Vert.x）、HTTP、CoAP(UDP)、**CoAP-TCP（GIIC）**、官方协议包等。我主证据线是 **GIIC over CoAP-TCP**：Californium 栈、PSK → Login/Refresh → Heartbeat/Data，解码后进同一套 `DeviceMessage` → EventBus。另有 GIIC over Pulsar 并行线，非全部走 TCP。

## 面试 30 秒

> 平台不止 MQTT。我做的是 CoAP-TCP 上的 GIIC：长连接、PSK 协商、Token 刷新、per-connection 队列防背压。目标 15 万在线，做过协议热缓存、Token Redis 化、全局 Sink 改 per-connection，长稳四天以上。和 MQTT 汇合点在 DeviceGatewayHelper 和 EventBus，不是两套平台。注意 CoAP-TCP 用 Californium 不是 Netty，MQTT 才是 Vert.x/Netty。

---

## 我们项目怎么做

### 1. 多协议组件地图

| 协议 | 网关类 | Codec | Transport |
|------|--------|-------|-----------|
| GIIC | `CoAPTCPServerDeviceGateway` | `GiicCoapTcpDeviceMessageCodec` | `CoAP_TCP` |
| MQTT Server | `MqttServerDeviceGateway` | JetLinks MQTT codec | `MQTT` |
| HTTP | `HttpServerDeviceGateway` | `JetLinksHttpDeviceMessageCodec` | `HTTP` |
| CoAP UDP | `CoAPServerDeviceGateway` | coap-component | `CoAP` |
| 官方协议包 | 各 Product 绑定 | `khlinks-official-protocol` | 多 transport |

协议注册：`GiicProtocolSupportProvider`（id=`giic-coap-tcp-v1.0`）。

### 2. 统一汇聚点（所有协议相同）

```text
*DeviceGateway 收字节
  → ProtocolSupport.getMessageCodec(transport).decode()
  → Flux<DeviceMessage>
  → DeviceGatewayHelper.handleDeviceMessage()
       ├─ sessionManager.compute()  // 会话
       ├─ 写 connectionServerId
       └─ DecodedClientMessageHandler.handleMessage()
  → DeviceMessageConnector.onMessage()
  → EventBus /device/{productId}/{deviceId}/...
  → 规则 / 时序 / 级联 / WebSocket
```

**GIIC 解码两条路**：

1. **物模型映射**（优先）：`third_metadata` + `metadata` → `GiicMetaMessageConvertUtil`
2. **Path 硬编码**（兜底）：`GiicMessageConverter`（heartbeat/login/data/event…）

### 3. GIIC CoAP-TCP 请求路径

| CoAP Path | 内部消息 |
|-----------|----------|
| `/.sys/psk` | PSK 协商（非 DeviceMessage，网关内处理） |
| `/.sys/login` / `activate` | `DeviceOnlineMessage` |
| `/.sys/heartbeat` | `DeviceOnlineMessage` |
| `/.sys/data` | `ReportPropertyMessage` |
| `GET /{sid}` | `ReadPropertyMessage` |
| `POST /{sid}` | `WritePropertyMessage` / Reply |
| `/event/*` | `EventMessage` |
| `/batchCmd` | 批量写属性 |

Topic 映射见 `khlinks-giic-protocol/.../TopicMessageCodec.java`（与 official 对齐，含 firmware 系列）。

### 4. GIIC vs MQTT 选型（面试说人话）

| 维度 | MQTT | GIIC CoAP-TCP |
|------|------|---------------|
| 连接模型 | pub/sub topic | CoAP 请求/响应 + 长 TCP |
| 鉴权 | 连接级 | PSK + Token |
| 我们的规模证据 | 平台常规接入 | **15 万压测主战场** |
| 栈 | Vert.x MQTT | **Eclipse Californium** CoAP-TCP |
| 背压 | connection messageProcessor | global/per-connection Sink |

### 5. CoAP 原理补课（JD 常问）

**CoAP 核心**（RFC 7252）：

- 基于 UDP 的 RESTful：GET/POST/PUT/DELETE + 资源 URI
- 轻量：4 字节头；Confirmable / Non-confirmable
- Observe 扩展：订阅资源变化（我们 GIIC 主路径用 **长 TCP + 心跳**，不是 UDP Observe）

**CoAP over TCP**（RFC 8323）：

- 解决 UDP 穿透/NAT/大包问题
- 我们 GIIC 选 TCP，Californium `CoapServer` + TCP connector

**和 MQTT 对比（成熟理解）**：

| | CoAP | MQTT |
|--|------|------|
| 模型 | 请求/响应（REST） | 发布/订阅 |
| 开销 | 更小 | 稍大 |
| 适用 | LPWAN、边缘 REST | 海量 pub/sub、生态成熟 |

---

## 面试追问速答

**Q：为什么用 CoAP-TCP 不用 MQTT？**  
A：端侧协议栈和历史选型是 GIIC 标准；平台侧通过统一 DeviceMessage 适配，下游无感。

**Q：多协议会写多套规则吗？**  
A：不会。规则订阅 EventBus `/device/**`，不关心入口协议。

**Q：GIIC 和 Pulsar 关系？**  
A：`GiicPulsarDeviceMessageCodec` 是另一条接入/级联线；CoAP-TCP 是设备直连主路径。

---

## 诚实边界

- **主证据**：CoAP-TCP GIIC 接入、15 万压测、背压改造
- **非主责**：CoAP UDP 网关、HTTP 设备接入细节、LwM2M

## 补课（可选）

- 原理：`D:\demo\coap` / [`middleware/mqtt`](../../middleware/mqtt/README.md)
- 证据：[`GIIC-15万压测参与复盘.md`](../../02-EMQX-IoT-Tuning/GIIC-15万压测参与复盘.md)
- 代码：`CoAPTCPServerDeviceGateway.java`、`GiicCoapTcpDeviceMessageCodec.java`
