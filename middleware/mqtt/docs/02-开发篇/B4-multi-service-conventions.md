# B4 多服务 Topic 层级与多租户规范

> 优先级: **P2 开发** | 预计阅读 30 分钟 | 深度：已深化

## 本章解决什么问题

在 **多个后端服务、多个产品线、多租户** 共用同一 Broker 时，如何避免主题冲突、重复消费误解、下行指令发错设备。本章给出可落地的 **Topic 树约定**、上下行分离、与 Pulsar/Kafka 的分工，并对照本仓示例前缀 `dev/test/`（开发）与生产式 `acme/iot/...` 的映射关系。

---

## 面试常问

1. 多租户 MQTT 如何隔离？只靠 topic 够吗？
2. 设备上报和服务之间通信能用同一棵主题树吗？
3. 为什么 MQTT 不适合做「任务队列」？
4. 下行指令主题怎么设计才安全？
5. MQTT 接入后如何进 Pulsar/Kafka？

---

## 核心知识

### 推荐层级（多租户 + 多服务）

```
{tenant}/{product}/{deviceId}/{stream}
```

| 段 | 含义 | 示例 |
|----|------|------|
| tenant | 租户 / 企业 | `acme` |
| product | 产品线或应用 | `iot`, `vehicle` |
| deviceId | 设备唯一 ID | `device001` |
| stream | 数据流类型 | `telemetry`, `event`, `command`, `ack` |

示例：

```
acme/iot/device001/telemetry    # 设备上行遥测
acme/iot/device001/event        # 告警、离散事件
acme/iot/device001/command      # 云端下行指令（设备订阅）
acme/iot/device001/command/ack  # 设备执行回执（可选）
```

本仓 Java 示例为简化使用 `dev/test/hello`、`dev/test/#`，**语义上等价于** 在 `dev` 租户下 `test` 产品的调试流；上线时替换前缀，代码中 topic 应 **配置化**（[B8](B8-config-management.md)）。

### 多服务如何各取所需

```
                    ┌─ telemetry-service  sub: acme/iot/+/telemetry
Broker ── acme/iot ─┼─ rule-engine        sub: acme/iot/+/event
                    └─ ops-dashboard      sub: acme/iot/+/status (retained)
```

原则：

1. **按 stream 拆订阅**，不要所有服务都 `acme/#`。
2. **写权限最小化**：遥测服务只 publish 下行 command，不应能 publish 他人 telemetry。
3. **设备只订阅自己相关的 command 主题**，精确到 `.../device001/command`，禁止 `+/command` 在设备端使用。

### 上行 vs 下行

| 方向 | 谁 Publish | 谁 Subscribe |
|------|------------|--------------|
| 上行遥测 | 设备 | 后端服务 |
| 下行指令 | 后端 / 规则引擎 | 设备 |
| 服务间 | **不推荐** 直接 MQTT | 用内部 MQ 或 gRPC |

服务 A 通知服务 B 若也走 MQTT，会引入 **第二套路由、ACL、监控**，除非明确「MQTT 作为企业总线」架构，否则内部用 Kafka/Pulsar。

### 与「Consumer Group」的对比

MQTT 默认 **广播**：N 个服务 sub 同一 topic → N 份拷贝。要「竞争消费」：

- 架构上 **单接入服务** 订阅 MQTT → 写入 Pulsar Topic → 多消费者组；
- 或 Broker **共享订阅**（EMQX 等，协议扩展）。

与 Pulsar 对照：

```
设备 --MQTT--> EMQX/Mosquitto --桥接/规则--> Pulsar persistent://acme/iot/telemetry
                                              └── 分析、存储、告警
```

MQTT 负责 **最后一跳接入**；Pulsar 负责 **日志、回放、计算**（见 [A2](../01-面试篇/A2-architecture.md)）。

### ACL 与多租户

Topic 规范必须配 **Broker ACL**：

- 设备证书/账号只能 `PUBLISH acme/iot/{自己的id}/telemetry`。
- 不能 `PUBLISH acme/iot/+/command`（防止伪造下行）。

仅靠「约定不改别人 topic」在恶意或固件 bug 面前不够。

### 反模式：在 Topic 里编码业务

```
# 错误：时间、类型塞在层级里难以 ACL
acme/iot/device001/2026/05/28/12/telemetry

# 正确：层级稳定，变长数据放 payload
acme/iot/device001/telemetry  →  {"ts":"...","metrics":{...}}
```

---

## 面试标准答案

### 题：如何设计 10 万设备的 Topic？

> 设备级主题用 deviceId 做一段，例如 acme/iot/{deviceId}/telemetry，保证每条消息路由明确，ACL 可按设备绑定。后端不要订阅 acme/#，而是按产品线订阅 acme/iot/+/telemetry，由 Broker 做主题匹配。海量连接时还要配合 EMQX 集群、统一 keepAlive、以及桥接到 Pulsar 做持久化和分析，MQTT 层不承担长期存储。若需要「按区域聚合」，在 payload 带 region 字段或在 product 下再分 region 段，而不是把日期塞进 topic。

### 题：多服务都处理遥测，会不会重复？

> 如果多个服务都直接订阅 acme/iot/+/telemetry，会各自收到全量副本，这是 MQTT 的正常行为，不是 Bug。要么只保留一个 ingress 服务写入 Pulsar，其他服务从 Pulsar 消费；要么使用支持共享订阅的 Broker 特性。面试要说清「我们想要的是广播还是竞争」，再选 MQTT 直连还是 MQ 中转。

---

## 生产环境注意点

- 发布 **Topic 命名规范文档** + 代码评审检查硬编码字符串。
- 开发 `dev/`、测试 `stg/`、生产租户前缀 **物理隔离** 或不同 Broker 集群。
- 下行 command 带 **版本号、签名或 nonce**，防重放（[A8](../01-面试篇/A8-security.md)）。
- 桥接规则显式映射 MQTT topic → Pulsar topic，避免一对多混乱。
- 监控按 tenant/product 聚合连接数与 publish 速率。

---

## 易错点与反例（≥3）

1. **所有环境共用 `prod/` 前缀连开发 Broker** — 测试数据污染生产分析；反例：本地仍 publish `prod/...`。
2. **后端订阅 `#` 做统一接入** — 任意服务误发大 payload 拖垮全部消费者；反例：「方便」订阅全站。
3. **设备订阅 `acme/iot/+/command`** — 收到他人指令；反例：图省事用通配符收下行。
4. **把 MQTT 当内部 RPC** — 无请求关联 ID 标准，难追踪；反例：order-service 和 inventory-service 互 pub/sub。
5. **多服务重复消费却未幂等** — 以为「只会处理一次」；反例：三个服务各写一遍数据库。

---

## 动手验证

1. 启动 Broker（[B6](B6-local-dev.md)）。
2. 用规范前缀模拟（与 SubscribeDemo 一致风格）：

```bash
mosquitto_pub -h localhost -t acme/iot/device001/telemetry -m '{"t":1}' -q 1
mosquitto_pub -h localhost -t acme/iot/device002/telemetry -m '{"t":2}' -q 1
mosquitto_sub -h localhost -t 'acme/iot/+/telemetry' -v
```

3. 运行 [SubscribeDemo.java](../../examples/java/mqtt-basics/src/main/java/com/demo/mqtt/SubscribeDemo.java)，临时把订阅改为 `acme/iot/#` 观察层级。
4. 阅读 mosquitto_pub 探测：MQTT 无「建 topic API」，连通性靠 publish 探测。

---

## 相关章节

- [A3 主题与通配符](../01-面试篇/A3-topics-wildcards.md) · [B3 订阅](B3-subscribe.md) · [B5 大数据量](B5-high-volume-notes.md)
- [B13 推动改造](B13-advocacy-change-strategy.md) · [附录 J 环境矩阵](../附录/J-env-diff-matrix.md)
