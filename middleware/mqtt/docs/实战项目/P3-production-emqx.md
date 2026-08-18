# P3：生产环境 EMQX 部署与接入

> 优先级: **P3 运维** | 预计实操 1~2 周（含评审） | 深度：已深化  
> 前置：[C1 部署](../03-运维篇/C1-deployment.md) | [P1](P1-device-telemetry.md) 或已有主题规范  
> 安全：[A8 TLS](../01-面试篇/A8-security.md) | [C6 安全运维](../03-运维篇/C6-security-ops.md)

## 项目目标

将 **本地 Mosquitto 开发栈** 平滑升级为 **生产级 EMQX 集群接入层**：完成 TLS、认证、ACL、负载均衡、监控与发布回滚方案；使 P1/P2 中的 `acme/iot/...` 主题与 ClientId 规范在 **预发/生产** 可直接复用，并通过 [附录 I](../附录/I-env-migration-checklist.md) 全量勾选。压测与容量不在本项一次性做完，但须完成 **冒烟连接** 并引用 [C11](../03-运维篇/C11-loadtest-connections.md) 制定后续压测计划。

---

## 架构目标（必读）

```text
设备 ──TLS 8883──► 云 LB / Nginx (TCP 透传) ──► EMQX 节点 × N
                        │
                        ├── Dashboard/API（仅运维网段 18083）
                        └── 规则引擎 → Pulsar（可选，[C4](../03-运维篇/C4-bridge.md)）
```

| 环境 | Broker | 本仓入口 |
|------|--------|----------|
| 本地开发 | Mosquitto Docker | [docker-compose-mosquitto.yml](../../docker/docker-compose-mosquitto.yml)、Docker Compose |
| 生产 | EMQX 5.x 集群 | Helm / 安装包 + LB（[C1](../03-运维篇/C1-deployment.md)） |

**禁止** 用 Mosquitto 单机结论推导 10W 连接能力（[C11](../03-运维篇/C11-loadtest-connections.md)、[A12 性能](../01-面试篇/A12-performance-scale.md)）。

---

## 阶段 0：差距分析与方案（约 2 天）

### 步骤

1. 对照 [附录 J 环境差异矩阵](../附录/J-env-diff-matrix.md) 与 [附录 I Checklist](../附录/I-env-migration-checklist.md)，逐项标记当前状态。
2. 填写 [附录 K 一页纸](../附录/K-one-page-proposal-template.md)：设备规模、QoS 策略、是否关匿名、TLS 方案。
3. 确认 **命名空间与隔离**：K8s `mqtt-prod` / `mqtt-staging`；主题前缀 `acme/` 与 [B4](../02-开发篇/B4-multi-service-conventions.md) 一致。
4. 列出 **端口清单**：8883（TLS MQTT）、8084（WSS 若需要）、18083（管理，内网）。

### 验收（阶段 0）

- [ ] 附录 I 12 项均有责任人及计划完成日。
- [ ] 评审记录：明确「不用 Mosquitto 扛生产全量」。
- [ ] 回滚策略：保留上一版 Helm values / 镜像 tag。

---

## 阶段 1：预发 EMQX 单节点（约 2~3 天）

### 步骤

1. 按 [C1 动手验证](../03-运维篇/C1-deployment.md) 拉起 EMQX 单节点（Docker 或 Helm staging）。
2. **关闭匿名**；创建设备账号与后端服务账号（分离权限）。
3. **ACL 按主题前缀**（与 Mosquitto `acl_file` 思路一致，语法见 [附录 G](../附录/G-config-reference.md)）：
   - 设备 `device001`：仅 `PUBLISH acme/iot/device001/telemetry`、`SUBSCRIBE acme/iot/device001/command`。
   - 后端 `telemetry-svc`：仅 `SUBSCRIBE acme/iot/+/telemetry`。
4. 用本仓 Java 示例指向预发（环境变量）：
   ```powershell
   $env:MQTT_BROKER="ssl://emqx-staging.example.com:8883"
   mvn -pl mqtt-basics -am exec:java -Dexec.mainClass="com.demo.mqtt.HelloMqtt"
   ```
   需在 JVM 或 Paho 配置信任库（[A8](../01-面试篇/A8-security.md)）。
5. CLI 验证（若安装 `mosquitto_pub` 且支持 TLS）：
   ```bash
   mosquitto_pub -h emqx-staging.example.com -p 8883 --cafile ca.crt -u device001 -P '***' \
     -t acme/iot/device001/telemetry -q 1 -m '{"v":1,"deviceId":"device001"}'
   ```
6. 对照 [Part D P9 本地 vs 生产](../04-问题百科/P9-local-vs-prod.md)，记录预发与本地差异。

### 验收（阶段 1）

- [ ] 匿名关闭：无凭证 CONNECT 被拒绝。
- [ ] ACL 拒绝用例：设备 A 无法向设备 B 的 telemetry 发布。
- [ ] HelloMqtt / SubscribeDemo 在预发 SSL 下跑通（可改 topic 为 `acme/iot/...`）。
- [ ] Dashboard 仅内网可达，公网未暴露 18083。

---

## 阶段 2：集群、LB 与高可用（约 3~5 天）

### 步骤

1. 部署 EMQX **≥3 节点**（[C8 HA 集群](../03-运维篇/C8-ha-cluster.md)）。
2. 前置 **四层 LB** TCP 透传 8883；不要求会话粘滞（MQTT ClientID 会话由 Broker 集群处理，以 EMQX 文档为准）。
3. Helm 设置 `resources.limits`、持久卷（会话/规则状态，见 [C1](../03-运维篇/C1-deployment.md) 易错点）。
4. **ClientId 加环境前缀**：`prod-telemetry-svc-01`，避免预发与生产互踢（[附录 I](../附录/I-env-migration-checklist.md) 第 5 项）。
5. 配置 [C5 监控](../03-运维篇/C5-monitoring.md)：连接数、消息 in/out、规则失败率、节点 CPU/内存。
6. 冒烟压测：用 [ConnectionLoadTest.java](../../examples/java/mqtt-loadtest/src/main/java/com/demo/mqtt/loadtest/ConnectionLoadTest.java) 打 **≤500** 连接验证脚本与 LB；大规模交给 [C11](../03-运维篇/C11-loadtest-connections.md) 与 emqtt-bench。

### 验收（阶段 2）

- [ ] 单节点故障，设备自动重连到存活节点（观察 CONNECT 日志）。
- [ ] LB 后端健康检查配置文档化。
- [ ] Grafana/告警：连接数突降、规则引擎错误率 >0 有通知（[C10 Runbook](../03-运维篇/C10-failure-runbook.md)）。

---

## 阶段 3：安全、桥接与发布（约 2~3 天）

### 步骤

1. **TLS**：生产证书链、设备 CA 轮换流程（[C6](../03-运维篇/C6-security-ops.md)）。
2. **桥接 Pulsar**（若架构需要）：按 [C4](../03-运维篇/C4-bridge.md) 预建 Topic；规则 **单出口**，避免 [Part D P2](../04-问题百科/P2-duplicate.md) 双写。
3. **规则引擎**：[C7](../03-运维篇/C7-rule-engine.md) 将 `acme/iot/+/telemetry` 转发到 Pulsar；MQTT 层不承担长期存储（[A2 架构](../01-面试篇/A2-architecture.md)）。
4. **发布顺序**（[C9 升级](../03-运维篇/C9-upgrade.md)）：先扩 Broker 容量 → 灰度设备批次（10%→50%→100%）→ 监控 24h。
5. **Broker 调优**：[C3](../03-运维篇/C3-broker-tuning.md) `max_connections`、`max_packet_size` 与 payload 大小对齐（[A9](../01-面试篇/A9-payload-format.md)）。

### 验收（阶段 3）

- [ ] 附录 I 第 2、3、4、10、11 项在生产勾选完成。
- [ ] 桥接：MQTT 入站条数与 Pulsar 写入条数 24h 对账误差 < 团队阈值。
- [ ] [C10](../03-运维篇/C10-failure-runbook.md) 中「Broker 不可用」演练完成一次。

---

## 阶段 4：与开发协作及文档收口（约 1 天）

### 步骤

1. 向开发交付 **连接串规范**：`ssl://`、端口、用户名来源、ClientId 模板（[B8](../02-开发篇/B8-config-management.md)）。
2. 更新 CI：集成测试仍对 Mosquitto（[B6](../02-开发篇/B6-local-dev.md)）；增加 **staging EMQX** 夜间冒烟（可选）。
3. 设备固件与云端 **同时切 TLS**，避免明文 1883 公网暴露。
4. 将 P2 幂等与 QoS 策略写入生产配置审查项。

### 总体验收标准

| # | 标准 | 验证方式 |
|---|------|----------|
| 1 | 生产 EMQX 集群 + LB + TLS 8883 | 渗透/扫描无匿名 1883 公网 |
| 2 | ACL 与 [B4](../02-开发篇/B4-multi-service-conventions.md) 主题树一致 | 用例测试矩阵 |
| 3 | 监控与 Runbook 就绪 | 告警演练记录 |
| 4 | 灰度发布记录与回滚演练 | 变更单 |
| 5 | 附录 I 全勾选 | 运维签字 |
| 6 | C11 压测计划已排期（可未完成 10W） | 项目计划链接 |

---

## 易错点

1. **开发 `allow_anonymous true` 抄到生产**（[C1](../03-运维篇/C1-deployment.md)）。  
2. **七层 LB 错误配置 WebSocket**（8084）。  
3. **Helm 无 resource limit** → OOM。  
4. **用 Mosquitto 压测结论买机器** → 容量错误（[C2](../03-运维篇/C2-capacity.md)）。  
5. **ClientId 无环境前缀** → 预发踢生产会话。

---

## 相关章节

- 运维：[C1](../03-运维篇/C1-deployment.md) [C2](../03-运维篇/C2-capacity.md) [C4](../03-运维篇/C4-bridge.md) [C5](../03-运维篇/C5-monitoring.md) [C8](../03-运维篇/C8-ha-cluster.md) [C11](../03-运维篇/C11-loadtest-connections.md)
- 开发迁移：[附录 I](../附录/I-env-migration-checklist.md) [P4 QoS/Topic 迁移](P4-migrate-qos-topic.md)
- 示例（冒烟）：[ConnectionLoadTest.java](../../examples/java/mqtt-loadtest/src/main/java/com/demo/mqtt/loadtest/ConnectionLoadTest.java)
- K8s 专题：[Part D P10](../04-问题百科/P10-k8s.md)
