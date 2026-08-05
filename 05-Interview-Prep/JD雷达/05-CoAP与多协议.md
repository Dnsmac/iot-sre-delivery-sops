# 05 CoAP 与多协议

> 三行定稿（可背）· **与你主证据强相关**

## 定义

CoAP 是受限设备常用的请求/响应协议（可 UDP/TCP）；物联网平台常多协议：MQTT、CoAP、HTTP、私有 TCP 等，解码后统一成内部消息模型。

## 现网有没有

**有。** 主讲线常是 **内嵌 MQTT**；我负责压测的是 **GIIC over CoAP-TCP**：PSK 协商 → Login/Refresh → Heartbeat/Data。解码后进同一套 `DeviceMessage` → EventBus。

## 面试 30 秒

> 平台不止 MQTT。我做的是 CoAP-TCP 上的 GIIC：长连接、PSK、令牌刷新。目标 15 万在线，做过按连接队列、协议热缓存和 Token Redis 化，长稳跑过四天以上。和 MQTT 汇合点在 EventBus，不是两套平台。

---

## 补课（可选）

- 外链：`D:\demo\coap` / `D:\demo\mqtt`（若有）
- 证据：[`GIIC-15万压测参与复盘.md`](../../02-EMQX-IoT-Tuning/GIIC-15万压测参与复盘.md)
