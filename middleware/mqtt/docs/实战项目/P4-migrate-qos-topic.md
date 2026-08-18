# P4：从 QoS0 + 随意主题迁移到规范体系

> 优先级: **P2/P3 跨团队** | 预计 4~8 周（视设备量） | 深度：已深化  
> 推动策略：[B13](../02-开发篇/B13-advocacy-change-strategy.md) | 方案模板：[附录 K](../附录/K-one-page-proposal-template.md)  
> 关联项目：[P1 遥测](P1-device-telemetry.md) | [P2 QoS](P2-qos-upgrade.md) | [P3 EMQX](P3-production-emqx.md)

## 项目目标

对 **存量系统** 完成可审计、可灰度、可回滚的迁移：从「全 QoS0 + 主题命名随意」过渡到 **[B4 主题规范](../02-开发篇/B4-multi-service-conventions.md) + 关键流 QoS1 + 消费幂等 + Broker ACL**；在 EMQX 生产环境用压测与对账验证，而不是一次性停机切换。交付物包括：主题/QoS 盘点表、ACL 配置、双写/灰度记录、丢包与重复率对比报告、附录 K 评审结论。

---

## 适用场景

| 信号 | 说明 |
|------|------|
| 无法做设备级 ACL | topic 无 `deviceId` 段，如 `data/temp` |
| 桥接 Pulsar 规则难写 | 通配符与层级不一致 |
| 「MQTT 老丢消息」工单 | 实为 QoS0 + Clean Session 组合（[Part D P1](../04-问题百科/P1-message-loss.md)） |
| 多服务订阅 `/#` | 权限过大、重复消费误解（[B4](../02-开发篇/B4-multi-service-conventions.md)） |

若现状已符合 B4 且仅缺监控，勿启动全量迁移，按 [B13 何时不用改](../02-开发篇/B13-advocacy-change-strategy.md) 处理。

---

## 阶段 0：盘点与证据（约 1 周）

### 步骤

1. **导出主题清单**（来源任选）：
   - Mosquitto：`mosquitto_sub -h <broker> -t '#' -v` 仅开发；生产用 EMQX Dashboard「主题统计」或日志采样。
   - 应用配置仓库：grep `publish(`、`subscribe(`、`setTopic`。
   - 网关/规则引擎导出。
2. 建表（Excel/飞书），每行一条 **发布或订阅关系**：

   | 字段 | 示例 |
   |------|------|
   | 业务名 | 温湿度上报 |
   | 当前 topic | `sensor/room1/data` |
   | 目标 topic | `acme/iot/room1/telemetry` |
   | 发布 QoS | 0 |
   | 订阅 QoS | 0 |
   | Clean Session | true |
   | ClientId 模式 | `gw-{random}` |
   | Retain | 否 |
   | 关键性 | 高/低 |
   | 负责人 | |

3. 标记 **关键流**（必须 QoS1 + 幂等）与 **可丢流**（保持 QoS0）。
4. 收集 **证据**：丢包日志、桥接条数差、重复入库工单（[Part D P2](../04-问题百科/P2-duplicate.md)）。
5. 召开评审，用 [附录 K](../附录/K-one-page-proposal-template.md) 记录「不改代价」。

### 验收（阶段 0）

- [ ] 盘点表覆盖 ≥95% 已知 MQTT 流量（按消息条数或业务确认）。
- [ ] 每条关键流有目标 QoS 与幂等方案（可引用 [P2](P2-qos-upgrade.md)）。
- [ ] 管理层签字迁移范围（避免范围蔓延）。

---

## 阶段 1：定规范、文档化、ACL 草稿（约 1~2 周）

### 步骤

1. 采纳 B4 层级：`{tenant}/{product}/{deviceId}/{stream}`，示例：
   ```
   acme/iot/device001/telemetry
   acme/iot/device001/event
   acme/iot/device001/command      # 下行，设备订阅
   ```
2. 编写 **《MQTT 主题与 QoS 规范 v1》**（1~3 页），包含：
   - 禁止项：日期进 topic、`/#` 给设备订阅、服务间乱用 MQTT 等（[B4 反模式](../02-开发篇/B4-multi-service-conventions.md)）。
   - QoS 缺省：遥测可 0，告警/指令 1；禁止默认 QoS2 全库。
   - ClientId：`{env}-{role}-{id}`。
3. **Mosquitto ACL 草稿**（开发验证）：编辑 [docker/mosquitto.conf](../../docker/mosquitto.conf) 同目录 `acl`（参考 [附录 G](../附录/G-config-reference.md)）：
   ```
   user device001
   topic write acme/iot/device001/telemetry
   topic read acme/iot/device001/command

   user telemetry-svc
   topic read acme/iot/+/telemetry
   ```
   本地关闭匿名后测试拒绝路径（[B6](../02-开发篇/B6-local-dev.md)）。
4. 新代码 **topic 配置化**（[B8](../02-开发篇/B8-config-management.md)）；本仓 `dev/test/` 映射表写入规范附录。
5. CI：增加 topic 命名 lint（正则 `^acme/iot/[^/]+/(telemetry|event|command)$` 等）。

### 验收（阶段 1）

- [ ] 规范 v1 发布，新旧 topic 对照表完整。
- [ ] 开发环境 ACL 用例：非法 cross-device publish 失败。
- [ ] 新功能只允许新 topic，旧 topic 冻结（仅维护）。

---

## 阶段 2：选一条关键流试点 QoS1 + 幂等（约 2 周）

### 步骤

1. 选 **一条** 高价值、中流量流（如 `event` 告警），避免第一条就选全网 telemetry。
2. 按 [P2](P2-qos-upgrade.md) 实施：发布/订阅 QoS1、payload `seq`、DB 幂等。
3. **双写灰度**（可选）：
   - 设备或网关同时发 `legacy/topic` 与 `acme/iot/device001/event`；
   - 消费端以新 topic 为准，旧 topic 只对账计数。
4. 用 [QoSDemo.java](../../examples/java/mqtt-basics/src/main/java/com/demo/mqtt/QoSDemo.java) 与 [HelloMqtt.java](../../examples/java/mqtt-basics/src/main/java/com/demo/mqtt/HelloMqtt.java) 在 Mosquitto 复现 QoS 行为后，在预发 EMQX 重复实验。
5. **对比指标**（至少 72h）：

   | 指标 | 迁移前 | 迁移后 |
   |------|--------|--------|
   | 丢包率 | | |
   | 重复率 | | |
   | P99 处理延迟 | | |
   | Broker CPU | | |

6. 失败回滚：切回旧 topic + QoS0 开关（feature flag），保留数据兼容。

### 验收（阶段 2）

- [ ] 试点流丢包率下降或达 SLA，重复率被幂等吸收（无业务重复工单）。
- [ ] 回滚演练一次成功（≤30 分钟）。
- [ ] [Part D P1](../04-问题百科/P1-message-loss.md) / [P2](../04-问题百科/P2-duplicate.md) 排查清单各走通一例。

---

## 阶段 3：主题批量迁移与消费切换（约 2~4 周）

### 步骤

1. **批次策略**：按产品线 / 区域 / 固件版本分批，每批 ≤10% 设备。
2. 每批流程：
   - 固件/网关改 publish topic；
   - 后端增加新 subscription（`acme/iot/+/telemetry`）；
   - 对账：新旧消费者计数差异 < 阈值；
   - 下线旧 subscription。
3. 避免多服务同时 `acme/#`：按 stream 拆分（[B4 多服务](../02-开发篇/B4-multi-service-conventions.md#多服务如何各取所需)）；需竞争消费则 **单 ingress → Pulsar**（[C4](../03-运维篇/C4-bridge.md)）。
4. 处理 **retained 脏数据**：旧 topic 上误开 retain 的，迁移前 `mosquitto_pub -t <old> -n -r` 清除（[Part D P8](../04-问题百科/P8-retain.md)）。
5. 文档更新 [附录 I](../附录/I-env-migration-checklist.md)、[附录 J](../附录/J-env-diff-matrix.md)。

### 验收（阶段 3）

- [ ] 设备批次迁移完成率 100%，旧 topic 流量归零（监控 7 天）。
- [ ] 无 P1 类「主题少一层」突发工单。
- [ ] 服务订阅符合最小权限（非 `/#`）。

---

## 阶段 4：EMQX 生产、压测与评审（约 1~2 周）

### 步骤

1. 完成 [P3 EMQX 生产](P3-production-emqx.md) 或确认生产已就绪。
2. **压测在 EMQX** 执行（[C11](../03-运维篇/C11-loadtest-connections.md)）：阶梯 1K→10K 连接，关键流 QoS1、payload 与生产一致。
3. 使用 [ConnectionLoadTest.java](../../examples/java/mqtt-loadtest/src/main/java/com/demo/mqtt/loadtest/ConnectionLoadTest.java) 仅作冒烟；大规模用 emqtt-bench。
4. 对账：MQTT `messages_in` vs 业务入库 vs Pulsar offset（若有桥接）。
5. **附录 K 终审**：问题、证据、建议、资源、结论归档；[B13](../02-开发篇/B13-advocacy-change-strategy.md) 话术用于复盘会。

### 总体验收标准（项目关闭）

| # | 标准 | 验证方式 |
|---|------|----------|
| 1 | 无未登记「随意 topic」在生产流量中 | 监控 + 盘点表 |
| 2 | 关键流 QoS1 + 幂等，可丢流 QoS0 有书面名单 | 规范 v1 附件 |
| 3 | EMQX ACL 与 B4 一致 | 安全测试报告 |
| 4 | 迁移批次记录与回滚演练存档 | 变更系统 |
| 5 | 丢包/重复对比报告已评审 | 附录 K 第 8 节 |
| 6 | C11 压测达到项目门槛或已备案风险 | 压测报告 |

---

## 沟通与反对意见（摘要）

| 反对 | 回应要点 |
|------|----------|
| 「QoS0 一直够用」 | 展示断网实验与工单证据（[A5](../01-面试篇/A5-qos-semantics.md)） |
| 「改 topic 要改固件，太慢」 | 网关聚合转换 + 双写过渡期 |
| 「QoS2 才不重复」 | QoS1+幂等更省资源；QoS2 仅极少数 topic |
| 「先上 EMQX 再规范」 | 无 ACL 的 EMQX 风险更高；可并行但 ACL 随批次上线 |

---

## 动手验证清单（开发机）

```powershell
cd docker; docker compose -f docker-compose-mosquitto.yml up -d

# 旧主题（模拟遗留）
mosquitto_pub -h localhost -t "sensor/room1/data" -q 0 -m '{"temp":1}'

# 新主题（规范）
mosquitto_pub -h localhost -t "acme/iot/room1/telemetry" -q 1 -m '{"v":1,"deviceId":"room1","seq":1,"metrics":{"temp":1}}'

mosquitto_sub -h localhost -t "acme/iot/+/telemetry" -q 1 -v
```

Java 回归：`mvn -pl mqtt-basics -am package -DskipTests` 后运行 HelloMqtt、QoSDemo（[B6](../02-开发篇/B6-local-dev.md)）。

---

## 相关章节

- [B4 规范](../02-开发篇/B4-multi-service-conventions.md) [B13 推动改造](../02-开发篇/B13-advocacy-change-strategy.md) [附录 K](../附录/K-one-page-proposal-template.md)
- 问题百科：[P1 丢失](../04-问题百科/P1-message-loss.md) [P2 重复](../04-问题百科/P2-duplicate.md) [P9 本地 vs 生产](../04-问题百科/P9-local-vs-prod.md)
- 示例：[QoSDemo.java](../../examples/java/mqtt-basics/src/main/java/com/demo/mqtt/QoSDemo.java) [SubscribeDemo.java](../../examples/java/mqtt-basics/src/main/java/com/demo/mqtt/SubscribeDemo.java)
