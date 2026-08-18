# 附录 L：Schema Registry 速查

> 深度：全文加深 ✓ | 原理 [A9](../part-a-interview/A9-Schema注册.md) | 排障 [P7](../part-d-problems/P7-Schema问题.md)

---

## 一、类型选择

| Schema 类型 | Java 用法 | 适用 |
|-------------|-----------|------|
| BYTES | `Schema.BYTES` | Protobuf 自解析、临时 |
| STRING | `Schema.STRING` | 简单文本 |
| JSON | `Schema.JSON(MyClass.class)` | 内部服务 |
| AVRO | `Schema.AVRO(MyClass.class)` | 强演进、大数据 |
| PROTOBUF | `Schema.PROTOBUF` | 跨语言 |

```java
Producer<OrderEvent> p = client.newProducer(Schema.JSON(OrderEvent.class))
    .topic("persistent://dev/test/orders")
    .create();
```

---

## 二、兼容性策略

| 策略 | 升级顺序 | 允许变更 |
|------|----------|----------|
| BACKWARD | **Consumer 先**，Producer 后 | 加可选字段 |
| FORWARD | Producer 先 | 旧 Consumer 读新数据 |
| FULL | 极谨慎 | 双向兼容 |
| ALWAYS | 不推荐生产 | 任意 |

```bash
pulsar-admin namespaces set-schema-compatibility-strategy persistent://dev/test \
  --strategy BACKWARD
```

---

## 三、Admin 命令

```bash
# 查看
pulsar-admin schemas get-schema-version persistent://dev/test/orders
pulsar-admin schemas get-schema-authentication-data persistent://dev/test/orders

# 上传（运维/CI）
pulsar-admin schemas upload --filename ./order-event.avsc \
  persistent://dev/test/orders
```

---

## 四、演进流程（BACKWARD）

```
1. 修改 schema：仅新增 optional 字段
2. 部署所有 Consumer（能读新 schema）
3. 部署 Producer（开始写新字段）
4. CI 跑兼容性检查
```

**不兼容变更：** 新 Topic `orders-v2` + 双写迁移。

---

## 五、常见错误

| 错误 | 处理 |
|------|------|
| IncompatibleSchemaException | 检查策略与升级顺序 |
| 一端 BYTES 一端 JSON | 统一 Schema 类型 |
| 同 Topic 两种业务结构 | 拆 Topic |
| 删字段改类型 | 禁止（BACKWARD 下） |

---

## 六、多服务协作

- 共享 `events-api` Maven 模块
- 版本号写入 message property（可选）
- 见 [B4](../part-b-java-dev/B4-多服务协作.md)、[P2 项目](../projects/P2-Schema演进.md)

---

## 相关

- [A9](../part-a-interview/A9-Schema注册.md) | [P7](../part-d-problems/P7-Schema问题.md)
