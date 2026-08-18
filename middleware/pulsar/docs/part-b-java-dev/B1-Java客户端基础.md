# B1 Java Client 基础

> 优先级: **P2 开发** | 预计阅读 30 分钟 | 深度：批次 4 ✓

## 本章解决什么问题

从零搭好 Java 依赖与 `PulsarClient` 生命周期，避免「每请求一个 Client」等常见坑，并能跑通本仓库第一个示例。

---

## 一、依赖与版本

本仓库父 POM（Java 8 + Pulsar 3.2.3）：

```xml
<dependency>
  <groupId>org.apache.pulsar</groupId>
  <artifactId>pulsar-client</artifactId>
  <version>3.2.3</version>
</dependency>
```

| 注意 | 说明 |
|------|------|
| Client/Broker 版本 | 大版本宜接近，避免 API 差异 |
| Java 8 | 本仓库编译目标 1.8；更高 JDK 可运行 |
| Spring | `pulsar-spring` 见 [B7](B7-Spring集成.md)，独立模块 |

---

## 二、核心原则（必守）

### 2.1 一个 JVM 一个 PulsarClient

```java
// 正确：单例 Bean 或 static holder
PulsarClient client = PulsarClient.builder()
    .serviceUrl("pulsar://127.0.0.1:6650")
    .build();

Producer<byte[]> p1 = client.newProducer().topic("...").create();
Consumer<byte[]> c1 = client.newConsumer().topic("...").subscriptionName("s").subscribe();
```

```java
// 错误：每次请求 newClient()
void handle() {
    PulsarClient client = PulsarClient.builder()...build(); // 连接爆炸
}
```

Client 内部维护连接池、DNS、重连；重复创建会导致 **FD 耗尽**、 [P6](../part-d-problems/P6-连接问题.md)。

### 2.2 关闭顺序

```java
try (PulsarClient client = PulsarClient.builder().serviceUrl(url).build()) {
    try (Producer<byte[]> producer = client.newProducer().topic(topic).create()) {
        producer.send("ok".getBytes(StandardCharsets.UTF_8));
    }
}
```

先关 Producer/Consumer，最后关 Client。Spring 由容器管理 destroy。

### 2.3 连接串

| URL | 场景 |
|-----|------|
| `pulsar://host:6650` | 明文 |
| `pulsar+ssl://host:6651` | TLS 生产 |

---

## 三、最小可运行示例

[`HelloPulsar.java`](../../examples/java/pulsar-basics/src/main/java/com/demo/pulsar/HelloPulsar.java)：

```java
PulsarClient client = PulsarClient.builder()
    .serviceUrl("pulsar://127.0.0.1:6650")
    .build();

Producer<byte[]> producer = client.newProducer()
    .topic("persistent://dev/test/hello")
    .create();
producer.send("hello".getBytes(StandardCharsets.UTF_8));

Consumer<byte[]> consumer = client.newConsumer()
    .topic("persistent://dev/test/hello")
    .subscriptionName("hello-sub")
  .subscriptionType(SubscriptionType.Shared)
    .subscribe();
Message<byte[]> msg = consumer.receive();
consumer.acknowledge(msg);

producer.close();
consumer.close();
client.close();
```

---

## 四、常用 Builder 参数（Client 级）

```java
PulsarClient.builder()
    .serviceUrl(url)
    .connectionTimeout(30, TimeUnit.SECONDS)
    .operationTimeout(30, TimeUnit.SECONDS)
    .authentication(AuthenticationFactory.token(jwt))  // 生产
    .build();
```

---

## 五、本地环境准备

```powershell
.\scripts\standalone-up.ps1
.\scripts\setup-dev-tenant.ps1
cd examples\java\pulsar-basics
mvn -q compile exec:java -Dexec.mainClass="com.demo.pulsar.HelloPulsar"
```

---

## 六、易错点

1. 多个 `PulsarClient` 实例。
2. 忘记 `close()` 导致泄漏（非 Spring 时）。
3. Topic 写 `my-topic` 而非全名 `persistent://dev/test/hello`。
4. Docker 内用 `localhost` 指错容器（应用与 Broker 不同容器时用服务名）。

---

## 七、下一步阅读

| 方向 | 章节 |
|------|------|
| 发送 | [B2 Producer](B2-生产者.md) |
| 消费 | [B3 Consumer](B3-消费者.md) |
| 速查 | [附录 C](../appendices/C-Java客户端速查.md) |
| 排障 | [B9](B9-排障手册.md) |

---

## 相关章节

- [B6 本地开发](B6-本地开发.md) | [B8 配置](B8-配置管理.md)
