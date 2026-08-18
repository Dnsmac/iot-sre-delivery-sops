# P2：关键流 QoS 升级与消费幂等

> 优先级: **P2 开发进阶** | 预计实操 3~5 天 | 深度：已深化  
> 前置：完成 [P1 设备遥测](P1-device-telemetry.md) 或已有稳定遥测主题  
> 理论：[A5 QoS 语义](../01-面试篇/A5-qos-semantics.md) | [A6 会话](../01-面试篇/A6-session-keepalive.md)

## 项目目标

将 **一条已识别的业务关键流**（告警、订单状态、计费脉冲等，非全量可丢采样）从 **QoS0 升级为 QoS1**，在发布端、订阅端、存储层同时落地 **幂等消费**；用可量化对比证明「丢包率下降、重复率可控」，并输出改造说明供 [B13](../02-开发篇/B13-advocacy-change-strategy.md) / [附录 K](../附录/K-one-page-proposal-template.md) 使用。

---

## 何时做 / 何时不做

| 建议升级 | 可维持 QoS0 |
|----------|-------------|
| 告警、交易、固件结果、配置确认 | 环境温湿度每秒采样、可丢预览流 |
| 有「发布成功但下游未收到」工单 | 已有应用层 ACK + 补传且指标良好 |
| 桥接 Pulsar 条数长期 < MQTT 入站 | 纯本地演示、无 SLA |

全库 QoS2 **不作为默认目标**（吞吐与 Broker 压力见 [A5](../01-面试篇/A5-qos-semantics.md)）；仅极少数控制 topic 可单独评估 QoS2。

---

## 阶段 0：基线度量（约 1 天）

### 步骤

1. **圈定关键流**：例如 `acme/iot/+/event`（告警）或 P1 中的 `telemetry` 若业务声明不可丢。
2. **盘点现状**（表格）：

   | 项 | 当前值 |
   |----|--------|
   | Topic 全名 | |
   | 发布 QoS / 订阅 QoS | |
   | Clean Session | |
   | ClientId 规则 | |
   | 是否 retain | |

3. 用 [QoSDemo.java](../../examples/java/mqtt-basics/src/main/java/com/demo/mqtt/QoSDemo.java) 对专用测试主题 `dev/test/qos-baseline` 在 QoS0 下做 **断网实验**：
   - 终端 A：`mosquitto_sub -h localhost -t dev/test/qos-baseline -q 0 -v`
   - 终端 B：循环 `mosquitto_pub ... -q 0`（脚本每 200ms 一条）
   - 中间 `docker stop mqtt-mosquitto` 3~5 秒再 `start`，统计 sub 端缺口条数。
4. 记录 **7 天或 24h** 生产/预发丢包工单数（若无生产，用实验缺口率代替）。

### 验收（阶段 0）

- [ ] 基线表完整，团队确认「升级的是这一条流，不是全库一刀切」。
- [ ] QoS0 断网实验报告：发布 N 条，收到 M 条，丢包率 ≈ (N-M)/N。
- [ ] 已阅读 [Part D P1 丢失](../04-问题百科/P1-message-loss.md) 与 [P2 重复](../04-问题百科/P2-duplicate.md) 的区别。

---

## 阶段 1：发布端改 QoS1（约 1 天）

### 步骤

1. 修改 Paho 发布代码（参考 [HelloMqtt.java](../../examples/java/mqtt-basics/src/main/java/com/demo/mqtt/HelloMqtt.java)）：
   ```java
   MqttMessage msg = new MqttMessage(payload);
   msg.setQos(1);  // 明确设置，勿依赖默认 0
   msg.setRetained(false);
   client.publish(topic, msg);
   ```
2. 对照 [B2 发布](../02-开发篇/B2-publish.md)：理解 QoS1 下 `deliveryComplete` 触发时机；高可靠场景避免在 PUBACK 前 dispose 客户端。
3. **订阅 QoS 对齐**：消费端 `subscribe(topic, 1)`，避免 min 规则把链路降为 0（[A5](../01-面试篇/A5-qos-semantics.md)）。
4. Spring 用户：出站 `MqttPahoMessageHandler` 的 defaultQos 同步改为 1（[B7](../02-开发篇/B7-spring-mqtt.md)）。
5. 在 Mosquitto 上用 CLI 回归：
   ```powershell
   mosquitto_pub -h localhost -t "acme/iot/device001/event" -q 1 -m '{"v":1,"seq":1,"type":"alarm"}'
   mosquitto_sub -h localhost -t "acme/iot/device001/event" -q 1 -C 1 -v
   ```

### 验收（阶段 1）

- [ ] Wireshark 或 `mosquitto_sub -d` 可见 PUBLISH qos=1 与 PUBACK（开发环境）。
- [ ] 代码搜索：关键流路径无 `setQos(0)` 残留（CI 可加 grep 规则）。
- [ ] [附录 C Paho 速查](../附录/C-paho-cheatsheet.md) 中 QoS 相关 API 与实现一致。

---

## 阶段 2：消费幂等（约 2 天）

### 步骤

1. **接受 QoS1 会重复**（[Part D P2](../04-问题百科/P2-duplicate.md)）：在 payload 增加单调字段：
   ```json
   { "v": 1, "deviceId": "device001", "seq": 42, "event": "overtemp" }
   ```
2. **存储幂等**（择一或组合）：
   - DB 唯一键 `(device_id, seq)` 或 `(device_id, event_id)`；
   - Redis `SETNX idempotency:{deviceId}:{seq}` TTL 24h；
   - 业务状态机：仅当 `seq > last_seq` 时更新。
3. 在 [SubscribeDemo](../../examples/java/mqtt-basics/src/main/java/com/demo/mqtt/SubscribeDemo.java) 回调中 **先查重再处理**，模拟重复投递：
   ```powershell
   # 同一 payload 连发两次
   mosquitto_pub -h localhost -t "acme/iot/device001/event" -q 1 -m '{"v":1,"deviceId":"device001","seq":42,"event":"overtemp"}'
   mosquitto_pub -h localhost -t "acme/iot/device001/event" -q 1 -m '{"v":1,"deviceId":"device001","seq":42,"event":"overtemp"}'
   ```
4. 禁止「仅靠 QoS2 解决重复」作为默认方案；若评估 QoS2，需全链路支持并压测（[B5](../02-开发篇/B5-high-volume-notes.md)）。
5. 桥接 Pulsar 时：MQTT ingress QoS1 + Pulsar 至少一次 + 消费幂等（[C4 桥接](../03-运维篇/C4-bridge.md)）。

### 验收（阶段 2）

- [ ] 故意重复 publish 同一 `seq`，DB/日志显示 **仅一次有效业务副作用**。
- [ ] 乱序 `seq` 有策略（拒绝或缓冲），见 [Part D P3 乱序](../04-问题百科/P3-out-of-order.md)。
- [ ] 单元测试覆盖：重复消息、缺 seq、seq 回退。

---

## 阶段 3：会话策略与离线窗口（约 1 天）

### 步骤

1. 判断是否需要 **离线必达**：
   - 若需要：`MqttConnectOptions.setCleanSession(false)` + 固定 ClientId + Broker 会话队列（[A6](../01-面试篇/A6-session-keepalive.md)、[Part D P7 离线](../04-问题百科/P7-offline-message.md)）。
   - 若不需要：保持 `cleanSession=true`，但知晓断线期间 QoS1 **不保证** 补发到持久会话。
2. 设备端与云端 **策略一致**：禁止一端 true 一端 false 导致「以为有离线消息其实被清会话」。
3. 调优 Keep Alive 与 NAT（[附录 I](../附录/I-env-migration-checklist.md) 第 9 项）。
4. 在测试环境模拟：订阅端离线 2 分钟，发布端持续 QoS1 发布，再上线核对条数与幂等表。

### 验收（阶段 3）

- [ ] 书面「会话策略」：Clean Session true/false 及理由，与产品 SLA 一致。
- [ ] 离线实验：预期条数与实测条数差异 ≤ 团队定义阈值，或解释 Broker `max_queued_messages` 截断。

---

## 阶段 4：对比与上线灰度（约 1 天）

### 步骤

1. **重复实验**：QoS1 + 不稳定网络，统计 [Part D P2](../04-问题百科/P2-duplicate.md) 重复率与幂等命中率。
2. **丢包对比**：同场景 QoS0 vs QoS1，丢包率应下降；记录 CPU、PUBACK 延迟（[附录 D 性能参数](../附录/D-performance-params.md)）。
3. **灰度**：按 deviceId 批次或 topic 后缀 `-v2` 双写对比（与 [P4 迁移](P4-migrate-qos-topic.md) 阶段 2 衔接）。
4. 填写 [附录 K](../附录/K-one-page-proposal-template.md) 第 3~5 节：证据、建议、计划。
5. 预发用 EMQX 单节点复测（勿只用 Mosquitto 结论上生产，见 [C1](../03-运维篇/C1-deployment.md)）。

### 总体验收标准

| # | 标准 | 验证方式 |
|---|------|----------|
| 1 | 关键流发布/订阅均为 QoS1 | 日志 + CLI |
| 2 | 消费幂等：重复 seq 无副作用 | 自动化测试 |
| 3 | QoS0 基线 vs QoS1 丢包率量化对比 | 实验报告 |
| 4 | 重复率在预期内且有监控阈值 | 仪表盘或手工统计 |
| 5 | 会话策略文档化 | 附录 I 勾选第 6、7 项 |

---

## 易错点

1. **只改发布不改订阅** → 实际 QoS 仍为 0。  
2. **无幂等直接上 QoS1** → 重复写库，工单反增。  
3. **Clean Session=true 却指望离线必达** → [A5](../01-面试篇/A5-qos-semantics.md) 面试陷阱在生产重现。  
4. **全库升 QoS2** → 连接数与 TPS 暴跌（[C2 容量](../03-运维篇/C2-capacity.md)）。  
5. **桥接双写** → MQTT 不重复但 Pulsar 重复（[C7 规则](../03-运维篇/C7-rule-engine.md)）。

---

## 相关章节

- [B2 发布](../02-开发篇/B2-publish.md) [B13 改造话术](../02-开发篇/B13-advocacy-change-strategy.md) [P4 全量迁移](P4-migrate-qos-topic.md) [P3 EMQX 生产](P3-production-emqx.md)
- 示例：[QoSDemo.java](../../examples/java/mqtt-basics/src/main/java/com/demo/mqtt/QoSDemo.java) [HelloMqtt.java](../../examples/java/mqtt-basics/src/main/java/com/demo/mqtt/HelloMqtt.java)
