# A9 负载与 Payload 格式

> 优先级: **P1 面试** | 预计阅读 20 分钟 | 深度：已深化 | 学习路径：**D22 | 面试：★★ 选修** | 主路径：[学习路径](../学习路径.md)

## 本章解决什么问题

MQTT **不规定** payload 格式；如何在 **JSON、Protobuf、二进制** 间选型，控制大小与解析成本，并与 Topic 职责划分清楚。

---

## 面试常问

1. MQTT payload 有标准格式吗？
2. JSON 和 Protobuf 怎么选？
3. 大 payload 有什么问题？
4. 能否把业务字段都塞进 Topic？
5. 如何做版本兼容？

---

## 核心知识

### 原则

- **Topic**：路由与 ACL，层级稳定，少变。
- **Payload**：业务数据，可版本化（如 `"v":1` 字段）。

### 常见格式

| 格式 | 优点 | 缺点 |
|------|------|------|
| JSON | 可读、调试快 | 体积大、解析慢 |
| Protobuf | 小、快 | 需 schema、调试门槛 |
| 二进制自定义 | 极省流量 | 文档与兼容成本高 |

### 大小与 Broker

- Mosquitto 默认 **max_packet_size** 有限（可配）；EMQX 亦有上限。
- 大消息占带宽、阻塞 callback；**10W 设备** 场景应 **<1KB** 为常态。

### 版本演进

- payload 内 `schemaVersion` / `msgType`
- 向后兼容：新字段可选，旧设备忽略未知字段

---

## 面试标准答案

### 题：Topic 里能不能放设备类型和温度？

> 不推荐。Topic 应表达路由维度如租户、产品、设备 ID、数据流类型，具体测量值放 payload。把动态数据塞进 topic 会导致主题爆炸、ACL 难写、桥接规则复杂。例外是极简单的开关量且永不扩展的场景。

### 题：payload 太大怎么办？

> 先聚合再发，例如 10 个采样点合并一条；或降采样；或走 HTTP/OSS 传文件、MQTT 只传 URL。同时检查 QoS 和 retain 是否不必要地放大了流量。

---

## 生产环境注意点

- 统一 **字符编码 UTF-8**；二进制则约定字节序。
- 敏感字段 **TLS 之上** 仍可应用层加密。
- 与 [B5](../02-开发篇/B5-high-volume-notes.md) 大数据量章节配合。

---

## 易错点与反例

1. **Topic 编码 JSON 路径** — `device/{"t":1}` 类反模式。
2. **单条 100KB JSON 每秒** — 拖垮 Broker 与蜂窝网。
3. **无 schema 的 Protobuf** — 联调困难。
4. **不压缩重复键名** — JSON 字段名应用短 key 或换 Protobuf。

---

## 动手验证

```bash
mosquitto_pub -h localhost -t acme/iot/d001/telemetry -m '{"v":1,"temp":23.5,"ts":1716883200}'
```

---

## 相关章节

- [A3 主题](A3-topics-wildcards.md) | [B5 大数据量](../02-开发篇/B5-high-volume-notes.md)
