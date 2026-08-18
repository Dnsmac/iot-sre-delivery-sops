# P1：设备遥测端到端实战

> 优先级: **P2 开发入门** | 预计实操 2~3 天 | 深度：已深化  
> 前置：[B6 本地环境](../02-开发篇/B6-local-dev.md) | [B1 Paho 基础](../02-开发篇/B1-paho-basics.md) | [A5 QoS](../01-面试篇/A5-qos-semantics.md)

## 项目目标

在本仓 Mosquitto 开发 Broker 上，完成一条 **可复现的设备遥测链路**：设备（或模拟器）按 [B4](../02-开发篇/B4-multi-service-conventions.md) 规范向 `acme/iot/{deviceId}/telemetry` 发布 JSON 遥测；后端服务订阅 `acme/iot/+/telemetry` 落库或打印；能通过 CLI 与 Java 示例 **独立验证** 发布、订阅、QoS1 与断线重连。为后续 P2（QoS 升级）、P3（EMQX 生产）、P4（主题迁移）打基础。

---

## 背景与范围

| 在范围内 | 不在范围内 |
|----------|------------|
| 单设备、单 Broker（本仓 Docker Mosquitto） | EMQX 集群、10W 连接（见 [C11](../03-运维篇/C11-loadtest-connections.md)） |
| QoS1 遥测 + JSON payload（[A9](../01-面试篇/A9-payload-format.md)） | 固件 OTA、下行 command 全链路 |
| Paho 或 `mosquitto_pub/sub` | Spring Integration 完整工程（可参考 [B7](../02-开发篇/B7-spring-mqtt.md)） |

本仓示例前缀 `dev/test/` 与规范前缀 `acme/iot/` 的对应关系见 [B4](../02-开发篇/B4-multi-service-conventions.md#推荐层级多租户--多服务)。

---

## 阶段 0：环境就绪（约 30 分钟）

### 步骤

1. 启动 Broker：`cd docker; docker compose -f docker-compose-mosquitto.yml up -d`（见 [B6](../02-开发篇/B6-local-dev.md)）。
2. 连通探测：`mosquitto_pub -h localhost -t dev/test/hello -m ping -q 1` 或 `mosquitto_pub -h localhost -t dev/test/hello -m ping -q 1`。
3. 编译 Java 示例（仓库根目录或 `examples/java`）：
   ```bash
   mvn -pl mqtt-basics -am package -DskipTests
   ```
4. 设置环境变量（可选）：`$env:MQTT_BROKER="tcp://localhost:1883"`。

### 参考示例

| 示例 | 路径 | 用途 |
|------|------|------|
| HelloMqtt | [HelloMqtt.java](../../examples/java/mqtt-basics/src/main/java/com/demo/mqtt/HelloMqtt.java) | 发布 + 订阅 QoS1 |
| SubscribeDemo | [SubscribeDemo.java](../../examples/java/mqtt-basics/src/main/java/com/demo/mqtt/SubscribeDemo.java) | 通配符订阅 `dev/test/#` |
| QoSDemo | [QoSDemo.java](../../examples/java/mqtt-basics/src/main/java/com/demo/mqtt/QoSDemo.java) | QoS0/1 对比 |

### 验收（阶段 0）

- [ ] `docker compose -f docker/docker-compose-mosquitto.yml ps` 显示 `mqtt-mosquitto` 运行中。
- [ ] `HelloMqtt` 控制台输出 `Published` 与 `Received`。
- [ ] [附录 F](../附录/F-mosquitto-cli-cheatsheet.md) 中 `mosquitto_sub -v` 能收到消息。

---

## 阶段 1：主题与 Payload 契约（约半天）

### 步骤

1. **选定设备 ID**：例如 `device001`，主题固定为 `acme/iot/device001/telemetry`（勿把日期、温度写进 topic 层级，见 [B4 反模式](../02-开发篇/B4-multi-service-conventions.md#反模式在-topic-里编码业务)）。
2. **定义 JSON 契约**（最小字段）：
   ```json
   {
     "v": 1,
     "deviceId": "device001",
     "ts": "2026-05-28T10:00:00Z",
     "metrics": { "temp": 25.3, "humidity": 60 }
   }
   ```
3. **文档化**：在团队 Wiki 或本仓 `docs/` 旁注一条「遥测契约表」：字段含义、单位、是否必填。
4. **配置化 topic**：Java 中勿硬编码散落字符串；对齐 [B8 配置管理](../02-开发篇/B8-config-management.md) 思路，至少用常量或环境变量 `MQTT_TOPIC_TELEMETRY`。

### 动手验证

```powershell
# 终端 A：订阅产品线级通配符
mosquitto_sub -h localhost -t "acme/iot/+/telemetry" -q 1 -v

# 终端 B：模拟设备上报
mosquitto_pub -h localhost -t "acme/iot/device001/telemetry" -q 1 -m '{"v":1,"deviceId":"device001","ts":"2026-05-28T10:00:00Z","metrics":{"temp":25.3}}'
```

### 验收（阶段 1）

- [ ] 订阅端收到的 topic 与发布完全一致（无多/少一层，见 [Part D P1 丢失](../04-问题百科/P1-message-loss.md)）。
- [ ] Payload 可被 `jq` 或 IDE JSON 解析，`deviceId` 与 topic 中 ID 一致。
- [ ] 团队书面确认：遥测 **不用** retained（避免新订阅者误读旧快照，见 [B2 Retained](../02-开发篇/B2-publish.md)）。

---

## 阶段 2：设备侧发布（Paho，约 1 天）

### 步骤

1. 复制 [HelloMqtt.java](../../examples/java/mqtt-basics/src/main/java/com/demo/mqtt/HelloMqtt.java) 为练习类（或在本机新建 `TelemetryPublisher`），修改：
   - `topic` → `acme/iot/device001/telemetry`
   - `MqttMessage.setQos(1)`
   - payload 为阶段 1 的 JSON 字节数组。
2. **ClientId 规范**：`telemetry-pub-device001-{实例后缀}`，避免多实例抢会话（[A6 会话](../01-面试篇/A6-session-keepalive.md)）。
3. **连接选项**：`setCleanSession(true)` + `setAutomaticReconnect(true)` + `setKeepAliveInterval(60)`（开发默认；离线必达场景在 P2/P4 再改）。
4. 按 [B2 发布](../02-开发篇/B2-publish.md) 理解：`deliveryComplete` 与 QoS1 PUBACK 的关系；发布失败时打日志而非静默。
5. 可选：用 [QoSDemo](../../examples/java/mqtt-basics/src/main/java/com/demo/mqtt/QoSDemo.java) 对 `acme/iot/device001/telemetry-qos-test` 发 QoS0/1，断网实验对比丢包（见 [A5](../01-面试篇/A5-qos-semantics.md)）。

### 验收（阶段 2）

- [ ] 连续发布 100 条，订阅端计数 ≥99（允许极端情况下 1 条差异，并记录是否 QoS0 误用）。
- [ ] 重启 Broker 容器后，**不依赖 retained** 仍能继续收到新上报（验证持久化会话非本阶段重点）。
- [ ] ClientId、topic、QoS 在代码评审清单中可一眼看出（对照 [附录 I](../附录/I-env-migration-checklist.md) 第 5、7 项）。

---

## 阶段 3：消费侧订阅与处理（约 1 天）

### 步骤

1. 基于 [SubscribeDemo.java](../../examples/java/mqtt-basics/src/main/java/com/demo/mqtt/SubscribeDemo.java)：
   - 订阅 `acme/iot/+/telemetry`，订阅 QoS **≥ 发布 QoS**（都用 1）。
   - 在 `messageArrived` 中解析 JSON，打印 `deviceId` + `metrics.temp`。
2. 阅读 [B3 订阅](../02-开发篇/B3-subscribe.md)：通配符 `+` 只匹配一层；`#` 慎用范围。
3. **慢消费警示**：若处理耗时 > 数秒，查阅 [Part D P4 积压](../04-问题百科/P4-slow-backlog.md)，本阶段保持处理 <100ms。
4. 理解 MQTT **广播语义**：再开一个相同订阅的进程，应收到 **两份** 拷贝；若要不重复，需单 ingress + Pulsar（[B4 与 Consumer Group](../02-开发篇/B4-multi-service-conventions.md#与-consumer-group-的对比)）。

### 验收（阶段 3）

- [ ] 双开订阅进程，每条消息打印两次（证明理解广播，非 Bug）。
- [ ] 故意将订阅 QoS 设为 0、发布 QoS 为 1，观察 [A5 min 规则](../01-面试篇/A5-qos-semantics.md) 下的行为并写 3 行实验笔记。
- [ ] 错误 JSON payload 不导致进程崩溃（try/catch + 死信日志）。

---

## 阶段 4：可观测与排障演练（约半天）

### 步骤

1. 模拟 **主题写错**：发到 `acme/iot/device001/telemetery`，确认订阅端无输出；按 [Part D P1](../04-问题百科/P1-message-loss.md) 排查清单走一遍。
2. 模拟 **ClientId 冲突**：两进程用同一 ClientId 连接，观察互踢与 `connectionLost`（[Part D P6](../04-问题百科/P6-disconnect.md)）。
3. 记录指标（开发期可手工）：每分钟发布条数、订阅端最后收到时间戳。
4. 阅读 [B9 排障](../02-开发篇/B9-troubleshooting.md) 与 [附录 E 决策树](../附录/E-troubleshooting-decision-tree.md)，在笔记中画一条「收不到消息」路径。

### 验收（阶段 4）

- [ ] 能在 15 分钟内用 CLI 定位「主题错误」类问题。
- [ ] 输出一页「P1 遥测链路图」（设备 → Broker → 消费者），可贴进 [附录 K](../附录/K-one-page-proposal-template.md) 背景节。

---

## 总体验收标准（项目完成）

| # | 标准 | 验证方式 |
|---|------|----------|
| 1 | 主题符合 `acme/iot/{deviceId}/telemetry` | 代码 + CLI 截图 |
| 2 | 遥测 QoS1，订阅 QoS1 | `mosquitto_sub -v` 显示 qos=1 |
| 3 | JSON 契约稳定且含 `v`、`deviceId`、`ts` | 样例消息存档 |
| 4 | 发布端、消费端可独立用 Java 或 CLI 跑通 | 同事按 README 复现 ≤30min |
| 5 | 理解广播、min(QoS)、retained 误用风险 | 口头或书面 3 题自测 |

---

## 常见问题

| 现象 | 查阅 |
|------|------|
| 发布成功但收不到 | [Part D P1 消息丢失](../04-问题百科/P1-message-loss.md) |
| 重复入库 | [Part D P2 重复](../04-问题百科/P2-duplicate.md)（P2 项目重点） |
| 本地 Broker 起不来 | [B6](../02-开发篇/B6-local-dev.md)、[docker/mosquitto.conf](../../docker/mosquitto.conf) |

---

## 相关章节

- 开发：[B1](../02-开发篇/B1-paho-basics.md) [B2](../02-开发篇/B2-publish.md) [B3](../02-开发篇/B3-subscribe.md) [B4](../02-开发篇/B4-multi-service-conventions.md) [B5 高吞吐备注](../02-开发篇/B5-high-volume-notes.md)
- 面试：[A3 主题](../01-面试篇/A3-topics-wildcards.md) [A9 Payload](../01-面试篇/A9-payload-format.md)
- 下一步：[P2 QoS 升级](P2-qos-upgrade.md) | [P4 迁移](P4-migrate-qos-topic.md)
