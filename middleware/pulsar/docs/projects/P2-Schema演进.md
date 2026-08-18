# 项目 P2：Schema 演进

> 深度：全文加深 ✓ | 预计 1~2 天 | 优先级 P2

## 目标

完成一次 **BACKWARD** 兼容的 Schema 演进：v1 → v2 增加字段，验证 **Consumer 先升、Producer 后升** 无报错。

## 前置

- [A9 Schema](../part-a-interview/A9-Schema注册.md)
- [附录 L](../appendices/L-Schema注册表速查.md)
- [B4 多服务](../part-b-java-dev/B4-多服务协作.md)

---

## 步骤 1：定义 v1

```java
public class OrderEvent {
    public String orderId;
    public long amountCents;
}
```

Topic：`persistent://dev/test/order-schema-demo`

```java
Producer<OrderEvent> p = client.newProducer(Schema.JSON(OrderEvent.class))
    .topic("persistent://dev/test/order-schema-demo")
    .create();
```

发送 10 条 v1 消息。

---

## 步骤 2：注册策略

```bash
pulsar-admin namespaces set-schema-compatibility-strategy persistent://dev/test \
  --strategy BACKWARD
pulsar-admin schemas get-schema-version persistent://dev/test/order-schema-demo
```

---

## 步骤 3：部署 Consumer v2（能读新字段）

```java
public class OrderEvent {
    public String orderId;
    public long amountCents;
    public String currency;  // 新增，可选/nullable
}
```

Consumer 使用 `Schema.JSON(OrderEvent.class)` 消费 v1 消息 — 应成功。

---

## 步骤 4：部署 Producer v2

发送带 `currency` 的消息。

Consumer 旧版（仅 v1 字段）应仍能消费 — BACKWARD。

---

## 步骤 5：负向测试（可选）

- Producer 先升、Consumer 未升且删字段 → 应 `IncompatibleSchemaException`
- 记录日志截屏作团队培训材料

---

## 步骤 6：CI 建议（文档化即可）

- 使用 Pulsar Schema 兼容性 API 或 `mvn` 插件对比 `.avsc`
- PR 改 schema 必须过兼容性检查

---

## 验收标准

- [ ] `schemas get-schema-version` 显示版本递增
- [ ] Consumer 先升、Producer 后升无报错
- [ ] 能口述 BACKWARD 与 FORWARD 区别
- [ ] 团队约定：不兼容变更走新 Topic

---

## 相关

- [P7 Schema 排障](../part-d-problems/P7-Schema问题.md) | [P1 订单](P1-订单系统.md)（选修，可跳过）
