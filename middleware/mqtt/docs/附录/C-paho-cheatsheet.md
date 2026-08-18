# 附录 C：Eclipse Paho Java 速查

> 与 [B1](../02-开发篇/B1-paho-basics.md)、[B2](../02-开发篇/B2-publish.md)、[B3](../02-开发篇/B3-subscribe.md) 配套。

---

## 最小连接与发布

```java
String broker = "tcp://localhost:1883";
String clientId = "demo-" + UUID.randomUUID();
MqttClient client = new MqttClient(broker, clientId, new MemoryPersistence());

MqttConnectOptions opts = new MqttConnectOptions();
opts.setCleanSession(true);
opts.setKeepAliveInterval(60);
opts.setConnectionTimeout(30);
opts.setAutomaticReconnect(true);
opts.setMaxInflight(10);

client.connect(opts);
MqttMessage msg = new MqttMessage("hello".getBytes(StandardCharsets.UTF_8));
msg.setQos(1);
client.publish("dev/demo/telemetry", msg);
client.disconnect();
client.close();
```

---

## 订阅与 Callback

```java
client.setCallback(new MqttCallback() {
    @Override
    public void connectionLost(Throwable cause) {
        log.warn("lost", cause);
    }
    @Override
    public void messageArrived(String topic, MqttMessage message) {
        // 勿阻塞：见 B9 场景4
    }
    @Override
    public void deliveryComplete(IMqttDeliveryToken token) { }
});

client.subscribe("dev/demo/#", 1);
```

**异步订阅（带 SUBACK 回调）：**

```java
client.subscribe("dev/demo/cmd", 1, null, new IMqttActionListener() {
    @Override
    public void onSuccess(IMqttToken asyncActionToken) { }
    @Override
    public void onFailure(IMqttToken asyncActionToken, Throwable exception) { }
});
```

---

## 常用 ConnectOptions

| 方法 | 说明 |
|------|------|
| `setCleanSession(boolean)` | 持久会话 vs 临时 |
| `setKeepAliveInterval(int)` | 秒 |
| `setUserName` / `setPassword` | 认证 |
| `setAutomaticReconnect(true)` | 断线重连 |
| `setMaxReconnectDelay` | 退避上限 ms |
| `setMaxInflight(int)` | QoS1/2 窗口 |
| `setWill(topic, payload, qos, retained)` | 遗嘱 |
| `setSocketFactory` | TLS |

---

## TLS 片段

```java
SSLContext ssl = SSLContext.getInstance("TLSv1.2");
// 加载 trustStore / keyStore 后
opts.setSocketFactory(ssl.getSocketFactory());
// broker 改为 ssl://host:8883
```

---

## Spring Integration（指向）

见 [B7](../02-开发篇/B7-spring-mqtt.md)：`MqttPahoClientFactory`、`MqttPahoMessageDrivenChannelAdapter`。

---

## 反模式速记

| 反模式 | 后果 |
|--------|------|
| callback 里 JDBC/HTTP | 断连 |
| 无界队列线程池 | OOM |
| 多进程同 ClientId | 互踢 |
| 未幂等却 QoS1 | 重复写 |

---

## 相关

- [附录 G 配置](G-config-reference.md) | [附录 D 性能参数](D-performance-params.md) | [B9 排障](../02-开发篇/B9-troubleshooting.md)
