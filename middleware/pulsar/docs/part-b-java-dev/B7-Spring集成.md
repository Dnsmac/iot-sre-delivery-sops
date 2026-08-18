# B7 Spring 集成

> 优先级: **P2 开发** | 预计阅读 30 分钟 | 深度：批次 4 ✓

## 本章解决什么问题

在 Spring Boot 中用 **Spring for Apache Pulsar** 声明式生产/消费，并与 [B8](B8-配置管理.md) 多环境配置衔接。

---

## 一、模块位置

本仓库 **`examples/java/pulsar-spring`** 为**独立 Maven 工程**（不进 `pulsar-examples` 父聚合），避免 Spring Boot 3 与全仓库 Java 8 策略冲突。本地开发可单独用 JDK 17 运行。

---

## 二、依赖（Spring Boot 3.2+）

```xml
<dependency>
  <groupId>org.springframework.pulsar</groupId>
  <artifactId>spring-pulsar-spring-boot-starter</artifactId>
</dependency>
```

由 Starter 自动配置 `PulsarTemplate`、`@PulsarListener` 等。

---

## 三、配置

[`application-dev.yml`](../../examples/java/pulsar-spring/src/main/resources/application-dev.yml)：

```yaml
spring:
  pulsar:
    client:
      service-url: pulsar://localhost:6650
    admin:
      service-url: http://localhost:8080
```

生产：`pulsar+ssl://` + `authentication` token 从环境变量注入（见 B8）。

自定义 Topic 前缀：

```yaml
app:
  pulsar:
    tenant: dev
    namespace: test
```

---

## 四、消费：@PulsarListener

```java
@Component
public class OrderListener {

    @PulsarListener(
        subscriptionName = "order-service",  // = 服务名，见 B4
        topics = "persistent://dev/test/spring-demo",
        subscriptionType = SubscriptionType.Shared
    )
    void listen(String message) {
        // 处理成功即 ACK；抛异常触发重试（视配置）
    }
}
```

| 注意 | 说明 |
|------|------|
| subscriptionName | 多服务不能重名 |
| 异常 | 默认可能重投；可配 ErrorHandler / DLQ |
| 类型 | 配合 Schema 用 `OrderEvent` 而非 String |

---

## 五、发送：PulsarTemplate

```java
@Autowired PulsarTemplate<String> pulsarTemplate;

public void publish(String payload) {
    pulsarTemplate.send("persistent://dev/test/spring-demo", payload);
}
```

异步：

```java
pulsarTemplate.sendAsync(topic, payload);
```

---

## 六、与原生 Client 选型

| 用 Spring | 用原生 Client |
|-----------|---------------|
| CRUD 式微服务、Listener 够用 | 精细控制 batch、Key_Shared 策略 |
| 团队已统一 Spring | 极致压测、复杂事务 |

高吞吐设备场景可在**网关**用原生 Client，业务服务用 Spring。

---

## 七、易错点

1. `@PulsarListener` 的 topic 写短名导致连错集群。
2. 复制 Demo 的 `subscriptionName` 到多个服务。
3. 未配 DLQ，异常消息无限重试。
4. 升级 Spring Boot 未对照 spring-pulsar 兼容矩阵。

---

## 相关章节

- [B8 配置](B8-配置管理.md) | [B4 多服务](B4-多服务协作.md) | [B3 Consumer](B3-消费者.md)
