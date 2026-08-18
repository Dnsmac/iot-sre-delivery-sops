# C10 故障 Runbook

> 优先级: **P3 运维** | 预计阅读 45 分钟 | 深度：已深化

## 本章解决什么问题

为生产 **EMQX**（及关联桥接/Pulsar）提供可执行的故障处置卡片：每条含 **触发条件、判断依据、处理步骤、回滚**，On-call 无需临时翻文档即可操作；开发 **Mosquitto** 仅作对照缩小范围。

---

## 面试常问

1. 连接数打满先扩节点还是先调 limit？
2. Broker OOM 与消息堆积如何区分？
3. 桥接断了数据会丢吗？
4. 全集群不可用时业务降级怎么做？
5. Runbook 为什么要写回滚？

---

## 核心知识

### 使用说明

- **严重级**：P0 全站不可用 / P1 部分租户 / P2 性能劣化。
- 所有步骤先 **保全证据**（指标截图、日志时间窗）再改配置。
- 变更同步值班群；超过 30 分钟未恢复升级 P0。

---

### 故障 1：连接数打满

| 项 | 内容 |
|----|------|
| **触发** | `connections` ≥ 85% `max_connections`；大量 `CONNACK` 拒绝或 `too many connections` |
| **判断** | Dashboard 连接曲线平台；是否 OTA/攻击（`connect_rate` 突增、单 IP 聚合） |
| **步骤** | 1) 确认 LB 健康 2) 临时升 `max_connections`（若 CPU/内存有余量）3) 扩 EMQX 节点 4) 限非法 `connect_rate` 5) 协调业务分批重连 |
| **回滚** | 恢复 limit 原值前确保已扩容；误杀限流则还原 zone 配置 |

---

### 故障 2：消息堆积 / 消费慢

| 项 | 内容 |
|----|------|
| **触发** | 规则队列、桥接 lag 升；设备上报正常但 Pulsar backlog 涨（[P4](../04-问题百科/P4-slow-backlog.md)） |
| **判断** | MQTT `messages_out` 正常而 Pulsar consumer lag 高 → 下游问题；两者都高 → 规则/桥接瓶颈 |
| **步骤** | 1) 扩容 Pulsar consumer 2) 降采样非关键主题 3) 暂停低优先级规则 4) 检查 Pulsar 写超时 5) 必要时网关降级丢弃 QoS0 |
| **回滚** | 恢复规则启用顺序：先 Pulsar 后 MQTT 规则；恢复采样率 |

---

### 故障 3：Broker OOM / Pod Evicted

| 项 | 内容 |
|----|------|
| **触发** | K8s OOMKilled；内存 95%+；大量大 Payload |
| **判断** | `kubectl describe pod`；堆外 vs 连接数；是否 retain 爆炸 |
| **步骤** | 1) 临时调大 memory limit（短期）2) 限 `max_packet_size` 3) 踢恶意 Client 4) 清异常 retain 5) 水平加节点分担连接 |
| **回滚** | limit 调高后记得排根因再收回；勿长期 2× 无监控 |

---

### 故障 4：桥接断开

| 项 | 内容 |
|----|------|
| **触发** | 桥接状态 `disconnected`；Pulsar 无新数据但 MQTT 有量 |
| **判断** | 网络/TLS/凭证过期；Pulsar broker 不可达；主题权限变更 |
| **步骤** | 1) 测 Pulsar 端口 2) 轮换证书 3) 重启桥接资源 4) 查 EMQX 桥接日志 5) 评估 MQTT 侧短时缓存是否已满 |
| **回滚** | 恢复旧证书 Secret 版本；禁用新桥接配置切回旧集群 |

---

### 故障 5：认证风暴 / ACL 误配

| 项 | 内容 |
|----|------|
| **触发** | `auth_failed` 飙升；设备批量离线 |
| **判断** | 是否刚发布 ACL；时钟漂移导致 JWT 过期 |
| **步骤** | 1) 对比上一版 ACL Git diff 2) 临时回滚 ACL 3) 检查 IdP 4) 抽样单设备 `mosquitto_pub` 模拟证书 |
| **回滚** | `git checkout` ACL 上一 tag + EMQX 重载认证 |

---

### 故障 6：单节点宕机

| 项 | 内容 |
|----|------|
| **触发** | 一 EMQX Pod NotReady；连接总数降 1/N |
| **判断** | 节点磁盘/脑裂；其他节点是否承接重连 |
| **步骤** | 1) LB 摘流坏节点 2) `kubectl delete pod` 重建 3) 查集群日志 4) 确认副本≥3 |
| **回滚** | 若新 Pod 反复崩溃，缩容坏节点并固定镜像版本上一版 |

---

### 故障 7：TLS / 证书过期

| 项 | 内容 |
|----|------|
| **触发** | 8883 连接全失败；SSL handshake error |
| **判断** | `openssl s_client` 看 notAfter；是否只更新了服务端未 OTA 设备 CA |
| **步骤** | 1) 紧急续签 2) 双证书监听器过渡 3) 分批 OTA 设备信任链 4) 监控剩余天数 <30 告警 |
| **回滚** | 挂载旧 Secret 到备用 listener 端口（需设备支持备用端口策略） |

---

## 生产环境注意点

- Runbook 每季度 **演练**一次（杀 Pod、断桥接）。
- Mosquitto 开发环境 **不演练** 10W 连接故障，避免误导。
- 事件复盘写入 [STUDY-TRACKER](../STUDY-TRACKER.md) 或团队 Wiki。

---

## 易错点与反例

1. **未判断就扩节点** — 实际是下游 Pulsar 慢。
2. **重启全体 EMQX 同时** — 全量设备重连风暴。
3. **桥接恢复后未对账** — 缺口窗口需 Pulsar 补偿任务。
4. **无回滚配置备份** — 手改 Dashboard 无法恢复。

---

## 动手验证

桌面演练：在测试 EMQX 上人为 `kubectl scale` 至 1 再恢复，记录连接恢复时间。

---

## 相关章节

- [C5 监控](C5-monitoring.md) | [C8 HA](C8-ha-cluster.md) | [C4 桥接](C4-bridge.md)
- [Part D 问题百科](../04-问题百科/INDEX.md) | [附录 E](../附录/E-troubleshooting-decision-tree.md)
