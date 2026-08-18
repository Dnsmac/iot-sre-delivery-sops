# B9 开发中解决问题

> 优先级: **P2 开发** | 预计阅读 **40 分钟** | 深度：已深化 | 学习路径：**D15~D17** | [主路径](../学习路径.md)

## 本章解决什么问题

> **怎么用本章：** 每场景读完 → 做「今日必做」Demo → 写 3 行排障故事 → 面试用 [2 分钟项目模板](../学习路径.md#2-分钟介绍一个-mqtt-项目模板) 里的「难点」段。

MQTT 在开发机上「能通」，上线后却出现收不到、重复、乱序、断连、生产 ACL 失败等现象。本章给出 **可复用的五步方法论** 与 **12 个高频场景的完整处置剧本**（现象 → 定位 → 解决 → 预防），并配套 `mosquitto_*` 与 Paho Java 片段。深入机理与运维侧处置见 [Part D 问题百科](../04-问题百科/INDEX.md)；决策树见 [附录 E](../附录/E-troubleshooting-decision-tree.md)。

---

## 五步方法论

```
现象（可观测、可量化）
  → 划界（客户端 / Broker / 网络 / 桥接下游）
  → 证据（mosquitto_sub、Broker 日志、$SYS、抓包、应用埋点）
  → 缩小（单变量：改 QoS、改 topic、换 ClientId、关业务逻辑）
  → 验证（修复后回归 + 预防项进 Checklist）
```

**划界口诀：** 同一 Broker 上用 CLI 能复现 → 优先查客户端配置与业务代码；CLI 也不行 → Broker/ACL/桥接；仅生产不行 → [P9](../04-问题百科/P9-local-vs-prod.md)、[附录 I](../附录/I-env-migration-checklist.md)。

---

## 场景 1：发了收不到

### 现象

发布端日志显示 `publish` 已调用或 `deliveryComplete` 已回调，订阅端 `messageArrived` 长期无输出；或 **部分设备** 收得到、部分收不到。QoS0 场景下表现为 **间歇性缺口**（切 Wi-Fi、弱网、Broker 重启后更明显）。桥接到 Pulsar/Kafka 时表现为 **下游条数少于** MQTT 入站计数。易与「消费慢导致堆积后被丢弃」混淆，需看 Broker 是否报 `queue full` 或慢消费者策略。

### 定位

1. **主题一致性**：逐字节比对发布 `topic` 与订阅 filter（大小写、环境前缀 `dev/` vs `prod/`、单复数 `device` vs `devices`）。通配符订阅 `a/#` 无法匹配 `b/a/x` 的层级错误。
2. **订阅是否生效**：Paho `IMqttMessageListener` 或 `subscribe` 的 `onSuccess` / SUBACK；失败时往往静默或仅打 error 日志。
3. **QoS 协商**：发布 QoS1、订阅 QoS0 时，Broker 可能按规则降级；关键链路应两端显式设为 1 并抓包确认 PUBLISH QoS 位。
4. **ACL**：Mosquitto `acl_file`、EMQX 鉴权；发布不被拒但 **转发被拒** 时，CLI 用 **与生产相同的用户名** 做影子订阅。
5. **连错 Broker / 多集群**：配置中心 `broker-url` 指向旧环境；K8s Service 与本地 hosts 不一致。

```bash
# 与业务相同 Broker、相同认证（生产勿用匿名）
mosquitto_sub -h "$BROKER" -p 1883 -u "$USER" -P "$PASS" \
  -t 'prod/acme/device001/telemetry' -q 1 -v -d
mosquitto_pub -h "$BROKER" -u "$USER" -P "$PASS" \
  -t 'prod/acme/device001/telemetry' -m '{"ping":1}' -q 1 -d
```

```java
// 发布前断言 topic 规范（与 B4 一致）
String topic = TopicNames.telemetry(tenantId, deviceId);
if (!topic.equals(publishedTopic)) {
    throw new IllegalStateException("topic drift: " + publishedTopic);
}
client.publish(topic, payload.getBytes(), 1, false);
```

**交叉索引：** [P1 消息丢失](../04-问题百科/P1-message-loss.md)、[A3 主题](../01-面试篇/A3-topics-wildcards.md)、[A5 QoS](../01-面试篇/A5-qos-semantics.md)。

### 解决

- 修正 topic / 订阅 filter；集成测试 **固定 golden topic** 断言。
- 关键数据改 **QoS1**，消费端 **幂等**（见场景 2）。
- 修 ACL：按租户前缀授权 `prod/{tenant}/#`；发布与订阅权限分离审计。
- 离线必达：`cleanSession=false` + 持久会话（见场景 7）。
- 桥接：检查 EMQX 规则命中、动作错误日志；Pulsar topic 预建与权限（[C4](../03-运维篇/C4-bridge.md)）。

### 预防

- CI 中增加 **mosquitto_sub 冒烟** 或 Testcontainers Mosquitto；发布前校验 topic 生成器单测。
- 主题规范写入 [B4](B4-multi-service-conventions.md)；禁止在代码里拼接魔法字符串。
- 监控：按 topic 前缀的 publish 速率 vs 消费速率；桥接 lag 告警。
- 文档化「开发 / 预发 / 生产」Broker 与 ACL 差异表（[B12](B12-environment-models.md)、[附录 J](../附录/J-env-diff-matrix.md)）。

---

## 场景 2：重复消息（QoS1）

### 现象

同一条业务消息被处理两次以上：数据库出现重复主键、设备重复执行指令、计费多计。日志里 **相同 payload、相近时间戳** 多次 `messageArrived`。网络闪断、Broker 重传 PUBLISH（未收到 PUBACK）、客户端 **自动重连后重投** 未确认消息时最常见。QoS2 在 Broker 与客户端实现正确时可避免重复，但成本高，生产更常用 **QoS1 + 幂等**。

### 定位

1. 确认 QoS：抓包或 `-d` 看 PUBLISH 是否 QoS1/2，是否出现 **Duplicate** 标志位。
2. 看重连日志：`connectionLost` 后 `automaticReconnect` 与 inflight 窗口（`maxInflight`）。
3. 业务是否 **至少一次** 语义却按 **至多一次** 实现（无 dedup）。
4. 多实例消费同一 topic 且无共享订阅分区键，导致「看起来像重复」实为 **多消费者各处理一次**（需架构层区分）。

```bash
mosquitto_sub -h localhost -t 'prod/cmd/#' -q 1 -v -d 2>&1 | tee sub.log
# 断网模拟：iptables 或拔网线后恢复，观察 Duplicate 与重投
```

```java
// 幂等键：clientId + 业务 messageId（勿仅用 MQTT packetId 跨会话）
String dedupKey = msg.getProperties().getMessageId()
    .orElse(hash(clientId, topic, payload));
if (idempotencyStore.putIfAbsent(dedupKey, TTL_24H) != null) {
    return; // 已处理
}
processBusiness(msg);
```

**交叉索引：** [P2 重复](../04-问题百科/P2-duplicate.md)、[A5 QoS 与幂等](../01-面试篇/A5-qos-semantics.md)。

### 解决

- 消费侧 **幂等**：DB 唯一键、`INSERT IGNORE`、Redis `SET NX`、或业务 `messageId` 去重表。
- 控制面指令使用 **单调递增 seq** + 「仅处理 seq > lastApplied」。
- 调优 `setMaxInflight` 与处理速度，减少长时间 unacked 导致 Broker 重传。
- 避免多服务重复订阅同一命令 topic；命令类用 **单消费者组** 或共享订阅（MQTT 5 / EMQX）。

### 预防

- 设计评审强制：QoS1 链路必须有 **幂等契约** 与 dedup 存储选型。
- 告警：重复率 = 去重命中次数 / 总消息数（异常升高说明网络或 Broker 异常）。
- 压测含 **闪断重连** 用例（[B11](B11-performance-verification.md)）。

---

## 场景 3：乱序

### 现象

同一设备的状态更新，后到的 `temp=30` 先被应用，先到的 `temp=25` 后覆盖，界面「回跳」。或固件升级进度 3→2→1 显示错乱。多 Publisher 向 **同一 topic** 并发发布、**多线程** 处理 `messageArrived`、跨分区桥接合并流时均可能出现。MQTT **不保证** 全局有序，仅在同会话、同 QoS 流上有有限顺序语义。

### 定位

1. 是否多线程 `executor.submit` 无分区键，导致并行乱序。
2. 是否多个服务/边缘节点向同一 topic 发布（无统一 seq）。
3. 是否 QoS0 与 QoS1 混用同主题，弱网下 QoS0 先到、QoS1 后到。
4. 桥接多 worker 写同一 Pulsar partition 策略错误。

```java
// 按 deviceId 哈希到固定单线程 executor，保证同设备有序
ExecutorService[] lanes = IntStream.range(0, 16)
    .mapToObj(i -> Executors.newSingleThreadExecutor())
    .toArray(ExecutorService[]::new);
void onMessage(MqttMessage msg) {
    String deviceId = parseDeviceId(msg);
    int lane = Math.floorMod(deviceId.hashCode(), lanes.length);
    lanes[lane].execute(() -> applyInOrder(deviceId, msg));
}
```

**交叉索引：** [P3 乱序](../04-问题百科/P3-out-of-order.md)。

### 解决

- 单设备 **单线程消费** 或带 `deviceId` 的队列分区。
- Payload 带 **单调 seq / 版本号**，应用层丢弃 `seq <= lastSeq`。
- 命令与遥测 **分 topic**；命令 QoS1 单消费者。
- 桥接配置保证同 device 路由到同一下游分区。

### 预防

- 主题设计：`.../telemetry` 与 `.../command` 分离；禁止多写者无 seq 共 topic。
- Code Review 禁止在 callback 内无序线程池直接写 DB。
- 文档说明「MQTT 有序性边界」（面试见 [附录 A](../附录/A-interview-questions.md)）。

---

## 场景 4：callback 阻塞导致断连

### 现象

消息量不大，但 **周期性 `connectionLost`**，错误码与 Keep Alive 相关；Broker 日志 `Client has exceeded timeout` 或 PING 超时。堆栈显示 `messageArrived` 或 `connectComplete` 内执行 JDBC、HTTP、大 JSON 解析。inflight 堆积、内存上涨后 OOM Kill 表现为 **更频繁的断连**。与「网络差」的区别：同机 CPU 高、处理耗时 P99 与断连时间点相关。

### 定位

1. 埋点 `messageArrived` 入口到出口耗时（histogram）。
2. 线程 dump：Paho 回调线程是否 blocked on DB lock。
3. 队列长度：无界 `LinkedBlockingQueue` 是否无限涨。
4. Keep Alive 是否过短，处理时间 > KeepAlive/2 的直觉风险。

```java
// 错误：callback 内同步 HTTP/DB
// 正确：有界队列 + 线程池，拒绝策略需显式选型
BlockingQueue<Runnable> q = new ArrayBlockingQueue<>(2000);
ExecutorService workers = new ThreadPoolExecutor(
    4, 8, 60, TimeUnit.SECONDS, q,
    new ThreadPoolExecutor.AbortPolicy()); // 满则快速失败，触发监控

@Override
public void messageArrived(String topic, MqttMessage msg) {
    if (!q.offer(() -> handle(topic, msg))) {
        metrics.dropped.increment();
        // 可选：nack / 死信，勿在 Paho 线程 sleep
    }
}
```

**交叉索引：** [P4 积压/慢](../04-问题百科/P4-slow-backlog.md)、[P6 断连](../04-问题百科/P6-disconnect.md)、[B5](B5-high-volume-notes.md)。

### 解决

- callback **只做入队**；业务在 worker 池，池大小与 Broker `max_queued_messages` 对齐评估。
- 缩短单条处理：异步写库、批量 insert、裁剪 payload。
- 适当 **增大 Keep Alive**（与 NAT/LB idle 协调，见场景 6）。
- EMQX 调慢消费者策略与队列上限，避免无声丢（关联场景 1）。

### 预防

- 架构规范：MQTT 回调线程禁止 I/O；静态分析或 ArchUnit 检测。
- 压测时同时看 **消费延迟 P99** 与 **连接稳定性**（[B11](B11-performance-verification.md)）。
- 线程池队列深度告警。

---

## 场景 5：吞吐低

### 现象

连接数正常，但 **消息速率上不去**（如预期 5 万 msg/s 实测仅数千）；CPU 不高但 publish 阻塞；或 Broker 指标 `messages.dropped` 上升。设备侧表现为上报排队、inflight 满后 `publish` 阻塞。常与 QoS2 滥用、小 payload 风暴、过大 JSON、单机 Mosquitto 瓶颈、或 `#` 订阅导致 Broker 匹配开销过大并存。

### 定位

1. 分层 [B10](B10-performance-tuning.md) 金字塔：先 L0 topic/QoS/频率，再 payload，再 Broker。
2. 看 QoS 分布：是否大量 QoS2 或 QoS1 未 ack。
3. `setMaxInflight` 是否过小导致发布端阻塞。
4. Broker 类型：开发 Mosquitto 单机 vs EMQX 集群（10W 设备见 B10）。
5. 订阅侧是否 `#` 全量（场景 10）。

```bash
# 粗测 publish 速率（单客户端，非严谨压测）
time for i in $(seq 1 10000); do
  mosquitto_pub -h localhost -t 'bench/t' -m "x" -q 0
done
```

**交叉索引：** [P5 吞吐](../04-问题百科/P5-performance.md)、[C11 连接压测](../03-运维篇/C11-loadtest-connections.md)。

### 解决

- 遥测改 QoS0 + **端侧聚合**（10s 一批）；关键流单独 QoS1 topic。
- 调大 `maxInflight`（理解内存）；增加发布线程与连接分片（多 ClientId 仅当架构允许）。
- 换 EMQX 集群 + LB；调 [C3](../03-运维篇/C3-broker-tuning.md) 参数。
- 压缩 payload、二进制编码；避免 1MB 级单条。

### 预防

- 容量规划公式：`设备数 × 频率 × (头+payload)` 进 [B10](B10-performance-tuning.md)。
- 上线前在 **目标 Broker** 压测，禁止仅用 Mosquitto 结论推生产（[B12](B12-environment-models.md)）。

---

## 场景 6：断连（Keep Alive / ClientId / NAT）

### 现象

连接频繁断开重连，`connectionLost` 日志与网络切换、LB 空闲超时、**ClientId 冲突**（后者表现为刚连上又被踢）交织。移动网络 NAT 表项老化后，TCP 半开而应用未及时 PING。K8s Pod 漂移后仍用旧 TCP。错误信息可能是 `32109`（连接丢失）或 Broker 侧 `disconnected due to protocol error`。

### 定位

1. Broker 日志是否 **duplicate client id**。
2. Keep Alive 与 LB `idle_timeout`、NAT UDP/TCP 超时对比（通常 KeepAlive < LB idle 的 1/2~1/3）。
3. 是否未启用 `automaticReconnect` 或重连风暴（退避）。
4. TLS 证书过期、MTU 问题（少见）。

```java
MqttConnectOptions opts = new MqttConnectOptions();
opts.setKeepAliveInterval(120);      // 与运维对齐，非越小越好
opts.setAutomaticReconnect(true);
opts.setMaxReconnectDelay(30_000);   // 指数退避上限
// ClientId 必须全局唯一：{product}-{deviceId}-{instance}
```

**交叉索引：** [P6 断连](../04-问题百科/P6-disconnect.md)、[A6 会话](../01-面试篇/A6-session-keepalive.md)。

### 解决

- 唯一 ClientId；禁用多进程同 ID。
- 协调 Keep Alive、TCP keepalive、LB 超时（文档进 [附录 G](../附录/G-config-reference.md)）。
- 修复 callback 阻塞（场景 4）。
- 生产用 **稳定 DNS/LB VIP**，避免频繁变 IP 导致会话失效。

### 预防

- ClientId 命名规范进 [B4](B4-multi-service-conventions.md)；注册表防冲突。
- 监控：连接时长分布、重连次数/设备/小时。

---

## 场景 7：离线消息不到

### 现象

设备休眠或断网期间平台下发的配置/指令，**上线后收不到**；或仅有时能收到。开发者误以为「发了 MQTT 就一定会投递」。实际上 **Clean Session=true** 时，Broker 不为其保留 QoS1 离线队列（MQTT 3.1.1 语义）；或队列已满被丢弃；或订阅在离线后才建立，历史消息不会补发（无 retain 时）。

### 定位

1. `MqttConnectOptions.setCleanSession(true/false)` 与产品需求是否一致。
2. 离线时是否 **已订阅** 目标 topic（未订阅则无队列）。
3. Broker `max_queued_messages`、EMQX 会话过期策略。
4. 是否误用 QoS0 下发关键指令。
5. MQTT 5 的 Session Expiry 与 3.1.1 Clean Session 差异（[A10](../01-面试篇/A10-mqtt5-advanced.md)）。

```java
opts.setCleanSession(false);  // 需离线队列时
// 首次连接后必须完成 subscribe，且 ClientId 稳定
client.connect(opts);
client.subscribe("prod/acme/device001/command", 1);
```

**交叉索引：** [P7 离线](../04-问题百科/P7-offline-message.md)。

### 解决

- 需离线必达：`cleanSession=false` + 稳定 ClientId + QoS1 订阅 + Broker 队列容量。
- 平台侧 **补发 API**：设备上线后按 lastSeen 拉取配置（MQTT + HTTP 混合更可靠）。
- 关键配置可用 **retain**（注意场景 8 脏数据风险）或版本号全量同步。

### 预防

- 产品文档明确：哪些消息走 MQTT 离线，哪些走拉取。
- 压测离线队列堆积与过期策略（[B11](B11-performance-verification.md)）。

---

## 场景 8：Retain 脏数据

### 现象

新订阅者一订阅立即收到 **陈旧状态**（如上周的 `online=true`、旧固件版本号），导致误告警或跳过升级。或 retain 消息 payload 为空仍占主题，清不掉。测试环境 retain 泄漏到生产同名 topic（若 ACL 不严）。设备发布 retain 后未在关机前用 **空 payload retain** 清除。

### 定位

1. `mosquitto_sub -t '<topic>' -v` 是否首条即为 retain（标志 `retain=true`）。
2. 谁在该 topic 上设置了 retain（审计发布日志）。
3. 是否混淆 retain 与 **持久会话离线队列**。

```bash
# 清除 retain：空 payload + retain 标志
mosquitto_pub -h "$BROKER" -t 'prod/acme/device001/status' -n -r -q 1
mosquitto_sub -h "$BROKER" -t 'prod/acme/device001/status' -v -C 1
```

**交叉索引：** [P8 Retain](../04-问题百科/P8-retain.md)、[A7](../01-面试篇/A7-retain-will.md)。

### 解决

- 生命周期管理：设备下线流程发布 **clear retain**；平台侧定时巡检异常 retain。
- 状态类 topic 带 **时间戳/version**，应用层忽略过期 retain。
- 禁止对高频遥测使用 retain；仅 **最后已知状态** 类使用。

### 预防

- 主题规范：哪些 topic 允许 retain（[B4](B4-multi-service-conventions.md)）。
- 集成测试：下线后订阅应无陈旧 retain 或 version 已更新。

---

## 场景 9：本地行生产不行

### 现象

开发环境 Mosquitto 匿名可连、收发正常；部署到 EMQX/K8s 后 **CONNACK 拒绝**、能连但 publish 无转发、TLS 握手失败、或仅部分机房失败。典型根因：环境变量仍指向 `localhost`、证书链不完整、ACL 按前缀拒绝、WS 与 TCP 端口混淆、K8s NetworkPolicy 阻断。

### 定位

1. 对照 [附录 I](../附录/I-env-migration-checklist.md) 逐项打勾。
2. 用生产账号 CLI 影子验证：`mosquitto_sub -h prod-lb ... -u ... --cafile ...`
3. EMQX Dashboard：鉴权失败、规则未命中。
4. 对比 [附录 J](../附录/J-env-diff-matrix.md) 开发 vs 生产矩阵。

```bash
openssl s_client -connect mqtt.prod.example.com:8883 -servername mqtt.prod.example.com
mosquitto_sub -h mqtt.prod.example.com -p 8883 \
  --cafile /etc/ssl/corp-ca.pem -u "$USER" -P "$PASS" \
  -t 'prod/#' -v -q 1
```

**交叉索引：** [P9 本地 vs 生产](../04-问题百科/P9-local-vs-prod.md)、[P10 K8s](../04-问题百科/P10-k8s.md)。

### 解决

- 配置分环境：`broker-url`、`username`、TLS 路径；启动时 **健康检查** 连 Broker。
- 修 ACL/TLS/防火墙；Service 与 Ingress 暴露正确端口（8883/8083）。
- 禁止生产 `allow_anonymous`（[C6](../03-运维篇/C6-security-ops.md)）。

### 预防

- 预发环境 **同构 EMQX**；CI 部署后自动 MQTT 冒烟。
- [B12](B12-environment-models.md) 写入团队 wiki。

---

## 场景 10：`#` 订阅爆炸

### 现象

Broker CPU 飙升、消息速率下降、个别共享订阅消费者 OOM；EMQX 路由表膨胀。某服务订阅 `prod/#` 或 `$SYS/#`，千万级 topic 流量 **全部命中** 该订阅。开发图省事用 `#` 做「总线」，上线后成为单点瓶颈。与场景 5 吞吐低强相关。

### 定位

1. Broker 控制台查 **订阅列表** 与 wildcard 数量。
2. 审计代码 `client.subscribe("#")` 或 `prod/#`。
3. 对比业务实际需要的前缀（租户级、设备类型级）。

```java
// 反例
client.subscribe("prod/#", 1);
// 正例：按租户 + 类型
client.subscribe("prod/" + tenantId + "/+/telemetry", 1);
```

**交叉索引：** [A3 通配符](../01-面试篇/A3-topics-wildcards.md)、[B4](B4-multi-service-conventions.md)。

### 解决

- 收窄为 `prod/{tenant}/+/telemetry` 或多条精确前缀。
- 海量 fan-out 用 **共享订阅**（MQTT 5 / EMQX）水平扩展消费者。
- 规则引擎侧过滤，避免应用层 `#` 抽全量。

### 预防

- Code Review 禁止 `#` 除非架构评审通过；静态扫描 subscribe 参数。
- 告警：单连接订阅 topic 数、wildcard 深度。

---

## 场景 11：遗嘱（Will）误触发

### 现象

设备仍在线却被平台判 **离线**；或测试环境频繁收到 `LWT` 遗嘱消息，触发误告警、级联踢设备。原因包括：进程崩溃未发 DISCONNECT、网络闪断超过 Will Delay（MQTT5）、**遗嘱 topic 与业务 topic 冲突**、ClientId 被抢连导致旧连接被踢触发遗嘱、测试脚本异常退出。

### 定位

1. 遗嘱配置：`setWill(topic, payload, qos, retain)` 是否在 **每次 connect** 重复设置且 topic 正确。
2. 正常下线是否调用 `disconnect()`（会抑制遗嘱）。
3. 是否另一实例用同 ClientId 连接。
4. retain 遗嘱是否被新订阅者长期误读（叠加场景 8）。

```java
// 正常维护窗口：先显式发布在线状态，再 disconnect
client.publish("prod/acme/device001/status", "maintenance".getBytes(), 1, false);
client.disconnect();
```

**交叉索引：** [A7 遗嘱](../01-面试篇/A7-retain-will.md)。

### 解决

- 正常关机流程：**DISCONNECT** + 可选 retain 更新为 maintenance。
- 遗嘱 payload 带 **原因码/时间戳**，消费端去抖（N 秒内仅处理一次）。
- ClientId 唯一；避免测试工具与真设备冲突。
- MQTT 5 使用 **Will Delay** 给网络恢复留窗口。

### 预防

- 遗嘱 topic 独立 `.../lwt`，不与遥测混用；文档化触发条件。
- 监控 LWT 速率异常尖峰。

---

## 场景 12：桥接丢消息

### 现象

MQTT 侧计数正常，**Pulsar/Kafka/HTTP 下游少条**；或间歇性丢，高峰更明显。EMQX 规则动作失败、桥接 QoS 与源不一致、下游慢导致 **规则内部队列满丢弃**、topic 映射错误（MQTT `a/b` 映射到 Pulsar `persistent://` 错误 namespace）。Mosquitto 手动 bridge 在断连期间 **未配置 proper inflight** 也会丢。

### 定位

1. EMQX：规则命中次数 vs 动作成功次数；失败日志 stack trace。
2. 桥接 QoS：MQTT QoS0 桥接默认可能 **at most once**。
3. Pulsar producer 阻塞、topic 不存在、权限拒绝。
4. 网络分区恢复后是否 **自动重放**（取决于桥接实现）。

```bash
# Mosquitto bridge 日志（示例路径因安装而异）
grep -i bridge /var/log/mosquitto/mosquitto.log | tail -50
```

**交叉索引：** [C4 桥接](../03-运维篇/C4-bridge.md)、[P1](../04-问题百科/P1-message-loss.md)。

### 解决

- 关键桥接链路 MQTT **QoS1** + 下游幂等；规则失败 **死信 + 重试**。
- 预建 Pulsar topic；调大规则引擎缓冲并监控 drop。
- 补偿：按时间窗口从 MQTT 持久化或上游重放（运维 runbook [C10](../03-运维篇/C10-failure-runbook.md)）。

### 预防

- 桥接 SLA 纳入 [C5 监控](../03-运维篇/C5-monitoring.md)：lag、失败率、重试次数。
- 变更桥接规则前在预发 **对账计数**（MQTT in == Pulsar in ± 幂等去重）。

---

## 面试常问（精选）

1. 发了收不到，你最先查哪三项？→ topic/SUBACK/ACL，见场景 1。
2. QoS1 为什么必须幂等？→ 至少一次 + 重传，见场景 2。
3. callback 里写 DB 为什么断连？→ 阻塞 PING，见场景 4。

## 动手验证

- 用本文 12 场景各建 **1 条** 团队内 known-issue 卡片（链接 Part D 对应篇）。
- 仓库根目录：`cd examples\java; mvn -q compile`（需 Broker 已启动）。

| 场景 | Java 类 | 运行示例 |
|------|---------|----------|
| 1 收不到 | [WrongTopicDemo](../../examples/java/mqtt-troubleshooting/src/main/java/com/demo/mqtt/troubleshoot/WrongTopicDemo.java) | `mvn -pl mqtt-troubleshooting -q exec:java -Dexec.mainClass=com.demo.mqtt.troubleshoot.WrongTopicDemo` |
| 2 重复 | [DuplicateHandlingDemo](../../examples/java/mqtt-troubleshooting/src/main/java/com/demo/mqtt/troubleshoot/DuplicateHandlingDemo.java) | 同上改 mainClass |
| 4 callback 阻塞 | [BlockingCallbackDemo](../../examples/java/mqtt-troubleshooting/src/main/java/com/demo/mqtt/troubleshoot/BlockingCallbackDemo.java) | `-Dexec.args=sync` 与 `async` |
| 7 离线 | [OfflineSessionDemo](../../examples/java/mqtt-troubleshooting/src/main/java/com/demo/mqtt/troubleshoot/OfflineSessionDemo.java) | 按类内说明分两次运行 |
| 8 Retain | [RetainDemo](../../examples/java/mqtt-troubleshooting/src/main/java/com/demo/mqtt/troubleshoot/RetainDemo.java) | `-Dexec.args=set` / `read` / `clear` |

（在 `examples/java` 目录下执行；场景 5~12 以 CLI + Part D 为主。）

## 相关章节

| 资源 | 链接 |
|------|------|
| Part D 问题百科 | [INDEX](../04-问题百科/INDEX.md) |
| 性能调优 | [B10](B10-performance-tuning.md) |
| 排查决策树 | [附录 E](../附录/E-troubleshooting-decision-tree.md) |
| 环境迁移 | [附录 I](../附录/I-env-migration-checklist.md) |
| Paho 速查 | [附录 C](../附录/C-paho-cheatsheet.md) |
