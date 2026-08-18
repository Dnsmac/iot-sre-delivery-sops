# B2 发布（Publish）API 与语义

> 优先级: **P2 开发** | 预计阅读 30 分钟 | 深度：已深化

## 本章解决什么问题

掌握 Paho **发布路径**：如何构造 `MqttMessage`、设置 **QoS**、**retained**、是否 **dup**，以及同步 `publish` 与 **deliveryComplete** 异步回调的关系。能根据业务选择「可丢采样 / 必达状态 / 最后已知值」，并对照 [QoSDemo.java](../../examples/java/mqtt-basics/src/main/java/com/demo/mqtt/QoSDemo.java) 与 [HelloMqtt.java](../../examples/java/mqtt-basics/src/main/java/com/demo/mqtt/HelloMqtt.java) 做对比实验。

---

## 面试常问

1. `publish(topic, message)` 和 `publish(topic, payload, qos, retained)` 有何区别？
2. 发布 QoS2、订阅 QoS1，最终投递语义是什么？
3. retained 消息什么时候该开？误开会怎样？
4. Paho 里如何知道 QoS1 发布「已被 Broker 确认」？
5. 高频 publish 要注意哪些 Broker 与客户端限制？

---

## 核心知识

### 发布 API 形态

Paho 推荐先构造 `MqttMessage`，再发布（与 HelloMqtt 一致）：

```java
MqttMessage msg = new MqttMessage("hello mqtt".getBytes());
msg.setQos(1);
msg.setRetained(false);
client.publish("dev/test/hello", msg);
```

重载 `publish(String topic, byte[] payload, int qos, boolean retained)` 适合一行式遥测，但不利于统一设置 **UTF-8、用户属性（MQTT5）** 等；本仓主线为 v3.1.1，以 `MqttMessage` 为主。

| 字段 | 作用 |
|------|------|
| `payload` | 业务字节，MQTT 不关心 JSON/Protobuf |
| `qos` | 0/1/2，见 [A5](../01-面试篇/A5-qos-semantics.md) |
| `retained` | Broker 保留该主题**最后一条** retained 报文，新订阅者立即收到 |
| `duplicate` | 一般由库在重传时设置，业务少改 |

### QoS 与发布端语义

| QoS | 发布端感知 | 典型用途 |
|-----|------------|----------|
| 0 | 发出即返回，无 PUBACK | 高频采样、环境数据 |
| 1 | 收到 PUBACK 才算成功（库层） | 告警、订单状态、指令 |
| 2 | 四次握手完成 | 金融级极少用，成本高 |

[QoSDemo.java](../../examples/java/mqtt-basics/src/main/java/com/demo/mqtt/QoSDemo.java) 对同一主题 `dev/test/qos-demo` 依次发 qos=0 与 qos=1，便于用 `mosquitto_sub -v` 观察 **是否有重复、断网重连后是否补发**。

**发布 QoS 与订阅 QoS 取 min** 的规则要牢记：发布 QoS2、订阅 QoS0，链路按 0 投递，**不能**靠提高发布 QoS 拯救懒惰的订阅配置。

### Retained 标志

- **true**：Broker 存储该主题最后一条 retained；新订阅者连接后**先收到**这条「快照」，再收实时流。
- 适用：设备在线状态、固件版本、最后一帧配置。
- **不适用**：每条都不同的遥测序列（新订阅者会收到一条「旧数据」误当实时）。

清除 retained：向该主题发布 **零长度 payload 且 retained=true**（具体以 Broker 文档为准，Mosquitto 支持此惯例）。

### 同步 publish 与「异步」_completion_

`MqttClient.publish` 在 QoS0 上很快返回；QoS1/2 在 TCP 写完后，**真正「完成」** 还依赖与 Broker 的 ACK 往返。

实现 `MqttCallback.deliveryComplete(IMqttDeliveryToken token)` 可在 token 完成时得知某次发布已确认：

```java
client.setCallback(new MqttCallback() {
    public void deliveryComplete(IMqttDeliveryToken token) {
        System.out.println("delivered: " + Arrays.toString(token.getTopics()));
    }
    // connectionLost / messageArrived ...
});
```

注意：

- 未设置 callback 时，QoS1 仍会在协议层完成，只是应用**无法挂钩**确认事件。
- 需要 **阻塞等待** 单次发布完成时，可用 `MqttDeliveryToken.waitForCompletion(timeout)`（慎用阻塞主线程）。
- 更高吞吐场景考虑 **`MqttAsyncClient`** + `IMqttActionListener`（本仓示例用同步 client 保持简单）。

### 主题与负载生产建议

```
{tenant}/{product}/{deviceId}/{stream}
```

- 单条 payload 控制体积（JSON 避免塞大数组）；超大文件走 HTTP/OSS，MQTT 只发引用 ID。
- 时间戳、序列号放 payload，**不要**塞进 topic 层级（见 [B4](B4-multi-service-conventions.md)）。

---

## 面试标准答案

### 题：QoS1 发布如何保证不丢？为什么还要幂等？

> QoS1 的含义是「至少一次」：客户端会把报文持久化到 Persistence（若配置），Broker 在确认写入会话并回复 PUBACK 后，发布端库才认为这次 publish 完成。网络闪断时可能重传，导致 Broker 或订阅端收到重复。所以 QoS1 解决的是「尽量不丢」，不是「恰好一次」。业务必须在消费侧用设备 ID + 序列号或业务主键做幂等，数据库用 upsert 或去重表。面试里要把「协议可靠性」和「业务一致性」分开答。

### 题：retained 和 Last Will 有什么区别？

> retained 是某主题上**正常发布**时带上的标志，表示「保留这条为最新状态」，新订阅者会收到；Last Will 是连接时注册的**遗嘱**，在客户端异常断线（非优雅 DISCONNECT）时由 Broker 代为发布到指定主题，用于离线告警。两者都可带 QoS 和 retained，但触发条件完全不同。常见错误是用 retained 发每秒遥测，导致新订阅者先收到一分钟前的温度再收到实时流，仪表盘跳变。

---

## 生产环境注意点

- 默认 **retained=false**；仅「状态类」主题显式开启，并在文档登记。
- 关键业务 **QoS1 + 幂等**；QoS2 仅在确有需要且全链路支持时启用。
- 配置 `maxInflight`（未确认 QoS1/2 并发上限），防止发布过快撑爆内存（附录 [G](../附录/G-config-reference.md)）。
- Broker `message_size_limit` 与 ACL 按前缀限制谁可 publish 到哪棵主题树。
- 发布速率与 [B5](B5-high-volume-notes.md) 聚合策略一起评估。

---

## 易错点与反例（≥3）

1. **所有消息 QoS2** — 吞吐骤降、Broker CPU 升高；反例：遥测也用 QoS2「求保险」。
2. **retained 当历史队列** — 新订阅只收到一条旧值，没有回放；反例：用 retained 发每分钟报表。
3. **以为 publish 返回即「消费者已处理」** — 只保证到 Broker（QoS1 及以上到 Broker ACK），下游处理在订阅侧。
4. **payload 用 `new String(bytes)` 未指定 Charset** — 乱码；应用 `StandardCharsets.UTF_8`。
5. **在 connectionLost 期间无限 publish** — 抛异常或静默失败；应先重连或排队。

---

## 动手验证

1. 启动 Broker（[B6](B6-local-dev.md)）。
2. 运行 QoSDemo：

```bash
cd examples/java/mqtt-basics
mvn -q compile exec:java -Dexec.mainClass=com.demo.mqtt.QoSDemo
```

3. 终端 A：`mosquitto_sub -h localhost -t 'dev/test/qos-demo' -v`
4. 终端 B 测 retained：

```bash
mosquitto_pub -h localhost -t dev/test/retain-demo -m "v1" -r
mosquitto_sub -h localhost -t dev/test/retain-demo -C 1 -v
```

5. 断网实验（可选）：发布 QoS1 后立刻 `docker stop mqtt-mosquitto`，观察 Paho 重连后是否重发（需 `automaticReconnect` + 非 clean 或持久化配合）。

---

## 相关章节

- [B1 Paho 基础](B1-paho-basics.md) · [B3 订阅](B3-subscribe.md) · [B5 大数据量](B5-high-volume-notes.md)
- [A5 QoS 语义](../01-面试篇/A5-qos-semantics.md) · [A7 Retain/Will](../01-面试篇/A7-retain-will.md)
