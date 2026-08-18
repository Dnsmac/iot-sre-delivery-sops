# 附录 C：Java Client 速查

> 深度：全文加深 ✓ | 详见 [B1](../part-b-java-dev/B1-Java客户端基础.md)、[B2](../part-b-java-dev/B2-生产者.md)、[B3](../part-b-java-dev/B3-消费者.md)

---

## 一、依赖与 Client

```xml
<dependency>
  <groupId>org.apache.pulsar</groupId>
  <artifactId>pulsar-client</artifactId>
  <version>3.2.3</version>
</dependency>
```

```java
// 一个 JVM 一个实例
PulsarClient client = PulsarClient.builder()
    .serviceUrl("pulsar://127.0.0.1:6650")
    .serviceUrl("pulsar+ssl://host:6651")  // 生产 TLS
    .authentication(AuthenticationFactory.token(jwt))
    .connectionTimeout(30, TimeUnit.SECONDS)
    .build();
```

---

## 二、Producer 速查

```java
Producer<byte[]> p = client.newProducer()
    .topic("persistent://dev/test/events")
    .producerName("order-pub")           // 可选
    .enableBatching(true)
    .batchingMaxPublishDelay(10, TimeUnit.MILLISECONDS)
    .compressionType(CompressionType.LZ4)
    .blockIfQueueFull(true)
    .maxPendingMessages(1000)
    .create();

// 同步
MessageId id = p.send(bytes);

// 异步（正确写法）
p.newMessage().key("order-1").value(bytes).sendAsync()
    .whenComplete((mid, ex) -> { if (ex != null) { /* 重试/告警 */ } });

p.flush();  // 关闭前刷出 batch
p.close();
```

| API | 说明 |
|-----|------|
| `.key(String)` | 分区路由、Key_Shared、Compaction |
| `.property(k,v)` | 元数据，不参与分区 |
| `.eventTime(long)` | 事件时间 |
| `MessageRoutingMode` | RoundRobin / SinglePartition（分区 Topic） |

---

## 三、Consumer 速查

```java
Consumer<byte[]> c = client.newConsumer()
    .topic("persistent://dev/test/events")
    .subscriptionName("order-service")   // = 服务名
    .subscriptionType(SubscriptionType.Key_Shared)
    .keySharedPolicy(KeySharedPolicy.stickyHashRange())
    .receiverQueueSize(1000)
    .subscriptionInitialPosition(SubscriptionInitialPosition.Earliest)
    .deadLetterPolicy(DeadLetterPolicy.builder()
        .maxRedeliverCount(3)
        .deadLetterTopic("persistent://dev/test/events-dlq")
        .build())
    .subscribe();

Message<byte[]> m = c.receive();
c.acknowledge(m);
c.negativeAcknowledge(m);
c.acknowledgeCumulative(m);  // 慎用

// Listener
c.messageListener((consumer, msg) -> { ... }).subscribe();
```

| 订阅类型 | 场景 |
|----------|------|
| Shared | 日志、无序 |
| Key_Shared | 订单/设备有序 |
| Exclusive | 单实例 |
| Failover | 主备 |

---

## 四、Reader（无 Subscription）

```java
Reader<byte[]> r = client.newReader()
    .topic("persistent://dev/test/audit")
    .startMessageId(MessageId.earliest)
    .create();
while (r.hasMessageAvailable()) {
    Message<byte[]> msg = r.readNext();
}
// 无 ACK，不影响 Subscription 进度
```

---

## 五、Schema 泛型

```java
Producer<OrderEvent> p = client.newProducer(Schema.JSON(OrderEvent.class))
    .topic("persistent://dev/test/orders")
    .create();
```

---

## 六、常见错误对照

| 错误写法 | 正确 |
|----------|------|
| 每请求 `newClient()` | 单例 Client |
| `sendAsync(messageBuilder)` | `newMessage()...sendAsync()` |
| 多服务同一 `subscriptionName` | 每服务独立名 |
| 先 ACK 再异步写库 | 先幂等写库再 ACK |
| 短 Topic 名 `events` | `persistent://tenant/ns/events` |

---

## 七、关闭顺序

`consumer.close()` → `producer.close()` → `client.close()`

---

## 相关

- [附录 D](D-性能参数速查.md) | [附录 E](E-排查决策树.md) | [B9](../part-b-java-dev/B9-排障手册.md)
