# P7 Schema 报错

> 优先级: **P2 开发** | 深度：批次 3 ✓  
> 链接: [附录 L Schema](../appendices/L-Schema注册表速查.md) | [A9](../part-a-interview/A9-Schema注册.md) | [P2 项目](../projects/P2-Schema演进.md)

---

## 典型现象

- `SchemaSerializationException` / `IncompatibleSchemaException`
- Consumer 反序列化失败，消息堆积。
- 升级 Avro/JSON 定义后**老 Consumer 全挂**。
- `getSchema` 显示版本与代码不一致。

---

## 原因（按概率排序）

| # | 原因 | 说明 |
|---|------|------|
| 1 | **Producer/Consumer Schema 不一致** | 一端 `BYTES` 一端 `JSON` |
| 2 | **兼容性策略违反** | BACKWARD/FULL 下删字段、改类型 |
| 3 | **未注册 Schema 直接发** | AUTO_PRODUCE 与显式 Schema 混用 |
| 4 | **多语言类名不同** | Avro `namespace` 不一致 |
| 5 | **Topic 复用** | 同 Topic 先后两种业务 Schema |
| 6 | **Schema 版本缓存** | 升级后 Consumer 未重启 |

---

## 排查步骤

### 1. 查看 Topic Schema

```powershell
docker exec pulsar-standalone bin/pulsar-admin schemas get-schema-authentication-data persistent://dev/test/events
docker exec pulsar-standalone bin/pulsar-admin schemas get-schema-version persistent://dev/test/events
```

### 2. 对比代码

```java
Schema<MyRecord> schema = Schema.JSON(MyRecord.class);
// Producer 与 Consumer 必须用同一 Schema 类型
```

### 3. 看 Broker 日志

搜索 `Incompatible`、`Schema`。

### 4. 确认策略

```powershell
docker exec pulsar-standalone bin/pulsar-admin namespaces get-schema-compatibility-strategy persistent://dev/test
```

| 策略 | 含义 |
|------|------|
| BACKWARD | 新 Schema 可读旧数据（Consumer 先升级） |
| FORWARD | 旧 Consumer 可读新数据 |
| FULL | 双向 |

---

## 解决方案

| 措施 | 说明 |
|------|------|
| 统一 Schema 类 | 共享 `api` 模块 jar |
| 兼容演进 | 只加可选字段；不删不改类型 |
| 新 Topic 迁移 | 不兼容变更用 `events-v2` |
| 原始字节 | 临时用 `Schema.BYTES` + 应用内 Protobuf（失去 Registry 校验） |
| 测试 | CI 里 Schema 兼容性检查 |

```java
Producer<MyRecord> p = client.newProducer(Schema.JSON(MyRecord.class))
    .topic("persistent://dev/test/events")
    .create();
```

---

## 预防

- Namespace 默认 `BACKWARD`。
- 字段用包装类型/Optional，避免 primitive 缺失歧义。
- 文档记录每个 Topic 的 Schema 版本。

---

## 面试一句话

> Schema 报错本质是生产和消费对消息结构理解不一致；用 Schema Registry 和兼容性策略，变更时只加字段或开新 Topic，Consumer 先升级再改 Producer（BACKWARD）。
