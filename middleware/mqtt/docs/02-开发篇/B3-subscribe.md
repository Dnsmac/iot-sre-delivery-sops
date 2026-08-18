# B3 订阅（Subscribe）与回调

> 优先级: **P2 开发** | 预计阅读 35 分钟 | 深度：已深化

## 本章解决什么问题

弄清 **订阅 API**、**MqttCallback** 三个方法的分工、通配符订阅的流量风险，以及为什么 **messageArrived 里不能做重活**（必须进线程池）。能独立运行 [SubscribeDemo.java](../../examples/java/mqtt-basics/src/main/java/com/demo/mqtt/SubscribeDemo.java)，并设计生产级「收消息 → 队列 → 业务处理」结构。

---

## 面试常问

1. `subscribe(topic, qos)` 与 `subscribe(String[] topics, int[] qos)` 区别？
2. 为什么 callback 里阻塞会导致断连？
3. MQTT 有没有 Consumer Group？多实例订阅同一主题会怎样？
4. `+` 和 `#` 订阅在生产如何控流？
5. 订阅 QoS 和发布 QoS 不一致时谁说了算？

---

## 核心知识

### 订阅 API

```java
client.subscribe("dev/test/#", 1);  // 主题过滤器, 最大愿意接受的 QoS
```

- 第二个参数是 **订阅端愿意接收的最大 QoS**，Broker 按与发布 QoS 的 **min** 投递。
- 批量：`client.subscribe(new String[]{"a/+/c", "b/#"}, new int[]{1, 0});`
- 取消：`client.unsubscribe("dev/test/#");`

[SubscribeDemo.java](../../examples/java/mqtt-basics/src/main/java/com/demo/mqtt/SubscribeDemo.java) 订阅 `dev/test/#`，10 秒内打印所有子主题消息，并开启 `automaticReconnect`。

### MqttCallback 三方法

| 方法 | 触发时机 | 生产要点 |
|------|----------|----------|
| `connectionLost` | TCP/心跳失败 | 打日志、告警；库可 automaticReconnect |
| `messageArrived` | 收到 PUBLISH | **尽快返回**；重逻辑丢线程池 |
| `deliveryComplete` | 发布端 QoS 完成 | 仅当本 client 也 publish 时需要 |

```java
client.setCallback(new MqttCallback() {
    public void connectionLost(Throwable cause) {
        System.err.println("lost: " + cause);
    }
    public void messageArrived(String topic, MqttMessage message) {
        System.out.println(topic + " => " + new String(message.getPayload()));
    }
    public void deliveryComplete(IMqttDeliveryToken token) {}
});
```

**必须在 `connect` 之前 `setCallback`**（或 connect 后订阅前设置），否则早到的消息可能无人处理。

### 线程模型：为什么需要线程池

Paho 使用 **网络读线程** 驱动 `messageArrived`。若在此方法里：

- 同步写数据库 200ms
- 调用外部 HTTP
- 复杂 JSON + 规则引擎

则读线程被占满，**PINGREQ/PINGRESP 无法及时处理**，Broker 认为客户端死掉而断开 — 表现为「消息着用着就 connectionLost」。

推荐模式：

```java
private final ExecutorService workers = Executors.newFixedThreadPool(8);

public void messageArrived(String topic, MqttMessage message) {
    byte[] payload = message.getPayload(); // 拷贝后异步，避免引用被复用
    workers.submit(() -> handle(topic, payload, message.getQos()));
}
```

配合 **有界队列 + 拒绝策略**（背压），见 [B5](B5-high-volume-notes.md)。队列满时宁可丢弃或 NACK 业务（MQTT v3 无标准 NACK，需应用层限速或暂停订阅）。

### 通配符与流量

| 过滤器 | 匹配范围 | 风险 |
|--------|----------|------|
| `dev/test/+` | 单层 | 中 |
| `dev/test/#` | 整棵子树 | 高，开发常用 |
| `#` | 全站 | **禁止生产** |

10W 设备若都发到 `acme/iot/{id}/telemetry`，后端服务应 **按产品级订阅** `acme/iot/+/telemetry`，而不是每个服务订阅 `#`。多租户用前缀隔离（[B4](B4-multi-service-conventions.md)）。

### 多订阅者与「广播」

MQTT **没有 Kafka Consumer Group**：同一主题被 N 个订阅者订阅时，**每条消息复制 N 份**（每个订阅会话各一份）。要「只处理一次」需：

- 业务层选举 leader，或
- 桥接到 Pulsar/Kafka 后用 **共享订阅 / 消费者组**，或
- EMQX 共享订阅（MQTT 5 / 扩展特性，见 [A10](../01-面试篇/A10-mqtt5-advanced.md)）。

### 与 HelloMqtt 的差异

HelloMqtt 订阅**精确主题**；SubscribeDemo 用 **`#`** 演示wildcard。生产从精确或 `+` 开始，确认流量后再放宽。

---

## 面试标准答案

### 题：为什么 messageArrived 里不能写重业务？

> 因为 Paho 在网络线程里同步调用 messageArrived，这条线程还要负责读 socket、处理心跳和其他报文。你在回调里阻塞，等于阻塞了整个客户端的 IO 循环，Keep Alive 超时后 Broker 会断开连接，表现为间歇性掉线、消息延迟暴增。正确做法是把 topic 和 payload 拷贝到内存队列，交给固定大小的线程池处理，并对队列做上限控制形成背压。这和 Netty 的「不要在 EventLoop 里阻塞」是同一类问题，只是 MQTT 开发者更容易忽略。

### 题：三个后端实例订阅同一主题，消息会三分还是只一份？

> 会三分。MQTT 的订阅是会话级别的，每个 clientId 一条会话，Broker 会把匹配的消息投递到每一个匹配的订阅会话。若要竞争消费，不能靠「大家都 sub 同一个 topic」，而要引入共享订阅、或只让一个服务订阅再转发到 MQ，或者桥接到 Pulsar/Kafka 后用分区消费。面试时说出「默认广播」能体现你真的做过多服务部署。

---

## 生产环境注意点

- callback **轻量** + **有界线程池**；监控队列深度与拒绝次数。
- `connectionLost` 中不要无限重试 publish；区分可恢复与配置错误（认证失败）。
- 订阅列表变更时用 `subscribe` 增量或先 `unsubscribe` 再订，避免重复过滤器。
- 长连接服务 **graceful shutdown**：先停 worker 池，再 `disconnect`。
- 通配符订阅需与运维 ACL 一致，防止新设备前缀把流量打进错误服务。

---

## 易错点与反例（≥3）

1. **messageArrived 里直接 `Thread.sleep`** — 人为触发 keepalive 超时；反例：sleep 5 秒做「限流」。
2. **未拷贝 payload 就异步** — 字节数组可能被库复用；反例：`workers.submit(() -> use(message.getPayload()))` 无拷贝。
3. **生产订阅 `#`** — 一条异常发布拖垮所有订阅者 CPU；反例：调试用 `#` 上线忘改。
4. **connect 之后才 setCallback 且存在 retained 风暴** — 首屏消息丢失；反例：顺序颠倒。
5. **以为多实例 sub 同一 topic = 负载均衡** — 实际是广播，处理重复三遍。

---

## 动手验证

1. 启动 Broker：[B6](B6-local-dev.md)。
2. 终端 A 运行 SubscribeDemo：

```bash
cd examples/java/mqtt-basics
mvn -q compile exec:java -Dexec.mainClass=com.demo.mqtt.SubscribeDemo
```

3. 终端 B 多发几条：

```bash
mosquitto_pub -h localhost -t dev/test/a -m "1" -q 1
mosquitto_pub -h localhost -t dev/test/b/nested -m "2" -q 1
```

4. 验证 `dev/test/#` 均能打印；改订阅为 `dev/test/+/nested` 观察不匹配 `dev/test/a`。
5. （可选）在 `messageArrived` 内 `Thread.sleep(30000)` 复现 connectionLost。

---

## 相关章节

- [B1 Paho 基础](B1-paho-basics.md) · [B2 发布](B2-publish.md) · [B4 Topic 规范](B4-multi-service-conventions.md) · [B5 大数据量](B5-high-volume-notes.md)
- [A3 主题与通配符](../01-面试篇/A3-topics-wildcards.md) · [B9 排障](B9-troubleshooting.md)
