# B7 Spring Integration MQTT 简明深化

> 优先级: **P2 开发** | 预计阅读 30 分钟 | 深度：已深化

## 本章解决什么问题

在 **Spring Boot / Spring Integration** 技术栈中，如何用 `spring-integration-mqtt` 把 MQTT 纳入统一的 **消息通道、生命周期与配置中心**，而不是在每个 `@Service` 里手写 `MqttClient`。本章篇幅刻意短于纯 Paho 章节，但覆盖 **ClientFactory、入站适配器、出站处理器、completionTimeout** 等面试与上线必知点，并与 [B8](B8-config-management.md) 外置配置衔接。

---

## 面试常问

1. Spring Integration MQTT 和直接用 Paho 怎么选？
2. `MqttPahoClientFactory` 管什么？能否多实例共享？
3. `MqttPahoMessageDrivenChannelAdapter` 做什么？
4. `completionTimeout` 超时会发生什么？
5. 如何在 Spring 里优雅关闭 MQTT 连接？

---

## 核心知识

### 依赖与角色

```xml
<dependency>
  <groupId>org.springframework.integration</groupId>
  <artifactId>spring-integration-mqtt</artifactId>
</dependency>
```

| 组件 | 作用 |
|------|------|
| `MqttPahoClientFactory` | 封装 `MqttConnectOptions`、clientId、ServerURI |
| `MqttPahoMessageDrivenChannelAdapter` | **入站**：订阅 → 转成 `Message<?>` 投到 Spring 通道 |
| `MqttPahoMessageHandler` | **出站**：从通道 `publish` 到 Broker |
| `@ServiceActivator` / `IntegrationFlow` | 业务消费与路由 |

设备侧、边缘网关仍常用 **纯 Paho**（体积小）；**多微服务统一配置、监控、重连策略** 时 Spring Integration 更省心。

### ClientFactory 与连接选项

```java
@Bean
public MqttPahoClientFactory mqttClientFactory(
        @Value("${mqtt.broker-url}") String url,
        @Value("${mqtt.username:}") String user,
        @Value("${mqtt.password:}") String pass) {
    DefaultMqttPahoClientFactory factory = new DefaultMqttPahoClientFactory();
    MqttConnectOptions opts = new MqttConnectOptions();
    opts.setServerURIs(new String[] { url });
    opts.setUserName(user);
    opts.setPassword(pass.toCharArray());
    opts.setCleanSession(true);
    opts.setAutomaticReconnect(true);
    opts.setKeepAliveInterval(60);
    factory.setConnectionOptions(opts);
    return factory;
}
```

- **clientId**：入站适配器构造时可传 `clientId`；多实例部署用 `mqtt.client-id: order-svc-${random.uuid}` 避免互踢（见 [B8](B8-config-management.md)）。
- **SSL**：`ssl://` URI + `MqttConnectOptions.setSocketFactory(...)`。

### 入站：MessageDrivenChannelAdapter

```java
@Bean
public MessageProducer inbound(MqttPahoClientFactory factory) {
    MqttPahoMessageDrivenChannelAdapter adapter =
        new MqttPahoMessageDrivenChannelAdapter(
            "order-svc-in-" + UUID.randomUUID(), factory, "acme/iot/+/telemetry");
    adapter.setCompletionTimeout(5000);
    adapter.setQos(1);
    adapter.setOutputChannel(mqttInputChannel());
    return adapter;
}

@Bean
public MessageChannel mqttInputChannel() {
    return new DirectChannel(); // 或 ExecutorChannel 把业务放到线程池
}
```

要点：

- **订阅主题** 在构造器传入，可 `setTopic(...)` 动态改。
- **`setQos`**：订阅最大 QoS。
- **`completionTimeout`**：与 Broker 交互的操作超时（毫秒），过小在弱网下易误报失败。
- 收到消息后到 `@ServiceActivator`，**仍须避免在单线程通道上阻塞**；用 `ExecutorChannel` + 有界队列实现与 [B3](B3-subscribe.md) 相同的背压思想。

```java
@ServiceActivator(inputChannel = "mqttInputChannel")
public void handle(Message<?> msg) {
    String topic = msg.getHeaders().get(MqttHeaders.RECEIVED_TOPIC, String.class);
    byte[] payload = (byte[]) msg.getPayload();
    // 委托业务线程池
}
```

### 出站：MqttPahoMessageHandler

```java
@Bean
@ServiceActivator(inputChannel = "mqttOutboundChannel")
public MessageHandler mqttOutbound(MqttPahoClientFactory factory) {
    MqttPahoMessageHandler handler =
        new MqttPahoMessageHandler("order-svc-out", factory);
    handler.setAsync(true);
    handler.setDefaultQos(1);
    handler.setDefaultRetained(false);
    return handler;
}
```

发布时设置 header：

```java
MessageBuilder.withPayload(bytes)
    .setHeader(MqttHeaders.TOPIC, "acme/iot/device001/command")
    .setHeader(MqttHeaders.QOS, 1)
    .build();
```

`setAsync(true)` 时行为接近 Paho 异步完成，需结合错误通道或 `MessagingException` 处理。

### 与纯 Paho 示例的对照

本仓 [HelloMqtt.java](../../examples/java/mqtt-basics/src/main/java/com/demo/mqtt/HelloMqtt.java) 等价 Spring 流程：

```
connect → subscribe → callback
```

Spring 用 **适配器 + 通道** 解耦；测试时可 `Mockito` mock `MessageChannel`，或用 **Testcontainers Mosquitto** 做冒烟。

### 生命周期

实现 `SmartLifecycle` 或由 Spring Boot 自动管理适配器 **start/stop**：

- 应用关闭时 **先停 inbound 适配器**，再停线程池，最后释放连接，避免 ghost 订阅。
- 与 Kubernetes `preStop` 钩子配合 `terminationGracePeriodSeconds`。

### 配置外置

生产禁止硬编码 `tcp://localhost:1883`：

```yaml
# application-prod.yml — 详见 B8
mqtt:
  broker-url: ssl://mqtt.prod.example:8883
  client-id: order-service-${HOSTNAME:${random.uuid}}
```

---

## 面试标准答案

### 题：什么时候用 Spring Integration MQTT，什么时候用 Paho？

> 如果是 Spring 微服务、已经大量使用 Integration 或 Cloud Stream，用 spring-integration-mqtt 可以把订阅、发布统一到 MessageChannel，享受 Spring 的生命周期、配置绑定和测试工具。如果是嵌入式设备、Android、或极简 Java 进程，Paho 直连更轻。两者底层都是 Paho，不是两套协议。选型关键在团队是否愿意维护 Integration 流程 DSL，以及是否需要与 Spring 事务、重试、错误通道整合。

### 题：MessageDrivenChannelAdapter 的 completionTimeout 是什么？

> 它限制适配器在等待 MQTT 操作完成时的最长等待时间，例如订阅确认或消息接收循环中的某些阻塞调用。设得太短，在 Broker 负载高或网络抖动时会抛超时异常，导致适配器 stop 或反复重连。设得太长，关停时 graceful shutdown 变慢。生产应结合 Broker 监控调优，并在日志里区分超时与认证失败。它和 Paho 的 keepAlive 不是同一个概念，面试不要混为一谈。

---

## 生产环境注意点

- **clientId、账号、密码** 走 [B8](B8-config-management.md) 与密钥管理，不进 Git。
- 入站用 **ExecutorChannel** 或业务线程池，禁止在单线程 `DirectChannel` 做重 SQL。
- 出站 QoS1 配合 **幂等**（[B2](B2-publish.md)）。
- 多环境 `application-{profile}.yml` 隔离 Broker 地址与 ACL 账号。
- 指标：Spring Integration 通道深度、MQTT 连接状态、重连次数（Micrometer 自定义或 Broker 侧看）。

---

## 易错点与反例（≥3）

1. **入站出站共用一个 clientId** — 互踢；反例：in/out 相同 `"spring-mqtt"`。
2. **DirectChannel 里调用远程 HTTP** — 阻塞适配器；反例：与 Paho callback 阻塞同理。
3. **未配置 errorChannel** — 异步出站失败静默；反例：`setAsync(true)` 无全局错误处理。
4. **dev profile 连生产 Broker** — 数据串扰；反例：复制 yml 不改 url。
5. **以为 Spring 会自动 Consumer Group** — 仍是 MQTT 广播；反例：多副本重复写库。

---

## 动手验证

1. 本地 Broker：[B6](B6-local-dev.md)。
2. 新建最小 Spring Boot 模块（自练）：引入 `spring-integration-mqtt`，配置 `mqtt.broker-url=tcp://localhost:1883`，入站订阅 `dev/test/#`，与 [SubscribeDemo.java](../../examples/java/mqtt-basics/src/main/java/com/demo/mqtt/SubscribeDemo.java) 并行，用 `mosquitto_pub` 发消息观察日志。
3. 关闭应用时确认日志出现 adapter **stopped** 且无幽灵连接（`mosquitto_sub -t '$SYS/broker/clients/connected' -v` 若已开启系统主题）。
4. 对照纯 Paho：运行 HelloMqtt 理解无 Spring 时的最小路径。

---

## 相关章节

- [B1 Paho 基础](B1-paho-basics.md) · [B3 订阅](B3-subscribe.md) · [B8 配置管理](B8-config-management.md)
- [B12 环境模型](B12-environment-models.md) · [附录 G 配置参考](../附录/G-config-reference.md)
