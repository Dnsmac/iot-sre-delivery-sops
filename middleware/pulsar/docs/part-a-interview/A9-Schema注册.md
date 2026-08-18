# A9 Schema

> 优先级: **P1 面试** | 预计阅读 25 分钟 | 深度：批次 4 ✓

## 本章解决什么问题

理解 Schema Registry 如何约束消息结构、兼容性策略如何选、以及为什么「随便发 JSON 字符串」在生产会炸。

---

## 面试常问

1. Pulsar Schema 有哪些类型？
2. BACKWARD 和 FORWARD 区别？升级顺序？
3. Schema 不兼容时会发生什么？
4. 多语言服务如何共享 Schema？
5. Schema 和消息 Key 有关系吗？

---

## 一、Schema 是什么

- 每条 Topic 在 Broker 上注册**消息结构定义**（Avro/JSON/Protobuf 等）。
- Producer 发送时携带 schema 版本；Consumer 按版本反序列化。
- **不匹配 → 客户端启动或发送时报错**，而非静默乱码（对比无 Schema 裸 bytes）。

---

## 二、常见 Schema 类型

| 类型 | 场景 |
|------|------|
| **BYTES** | 自定义序列化，无 Registry 校验 |
| **STRING** | 纯文本 |
| **JSON** | 简单结构，类名绑定 `Schema.JSON(MyClass.class)` |
| **AVRO** | 大数据生态，强 schema 演进 |
| **PROTOBUF** | 跨语言、体积小 |
| **AUTO_PRODUCE** | 从 payload 推断（慎用） |

```java
Producer<OrderEvent> producer = client.newProducer(Schema.JSON(OrderEvent.class))
    .topic("persistent://company/order/order-created")
    .create();
```

---

## 三、兼容性策略

| 策略 | 含义 | 升级顺序 |
|------|------|----------|
| **ALWAYS** | 任意变更都允许 | 无约束（几乎不用） |
| **BACKWARD** | 新 Schema 可读旧数据 | **先升 Consumer，再升 Producer** |
| **FORWARD** | 旧 Consumer 可读新数据 | 先升 Producer |
| **FULL** | 双向 | 最严格 |

**生产默认推荐 BACKWARD：**

- 只**新增可选字段**
- **不删字段、不改类型、不改字段名**

```bash
pulsar-admin namespaces set-schema-compatibility-strategy persistent://company/order \
  --strategy BACKWARD
```

---

## 四、多服务协作

1. 公共模块 `events-api.jar` 放 `.avsc` / `.proto`。
2. CI 跑兼容性检查（against 上一版本）。
3. 不兼容变更 → **新 Topic**（`order-created-v2`），双写迁移。

见 [B4](../part-b-java-dev/B4-多服务协作.md)、[P7](../part-d-problems/P7-Schema问题.md)。

---

## 五、与 Key / 分区的关系

- **无关**：Schema 管 payload 结构；Key 管分区与 Key_Shared。
- Compaction 依赖 **Message Key**，与 Schema 类型独立。

---

## 六、生产环境注意点

- **禁止**各服务自行 `BYTES` + 私下 JSON 格式漂移。
- Namespace 默认 BACKWARD；文档登记每个 Topic 的 schema 版本。
- 查看当前 schema：

```bash
pulsar-admin schemas get-schema-version persistent://dev/test/events
```

---

## 七、易错点

1. 删 Avro 字段导致旧 Consumer 启动失败。
2. Producer 升级在前、Consumer 在后（BACKWARD 下违规）。
3. 同一 Topic 混用两种业务消息。
4. 以为 Schema 能保证「不丢消息」——只保证结构一致。

---

## 面试标准答案

> Pulsar 在 Broker 维护 Schema Registry，Producer 和 Consumer 使用相同 schema 才能正常收发。兼容性常用 BACKWARD，即只加可选字段，先升级 Consumer 再升级 Producer。不兼容会直接在客户端报错，避免脏数据。多服务通过共享 Maven 模块和 CI 检查保证 schema 一致。

---

## 相关章节

- [附录 L Schema](../appendices/L-Schema注册表速查.md) | [B4](../part-b-java-dev/B4-多服务协作.md) | [P7](../part-d-problems/P7-Schema问题.md)
