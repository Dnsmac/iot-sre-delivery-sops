# C9 Broker 升级与变更

> 优先级: **P3 运维** | 预计阅读 30 分钟 | 深度：已深化

## 本章解决什么问题

规范 **Mosquitto 补丁** 与 **EMQX 小版本/大版本** 升级流程：兼容矩阵、滚动策略、配置迁移、回滚条件，减少「升完一夜断连」事故。

---

## 面试常问

1. MQTT Broker 升级需要断连吗？
2. 3.1.1 设备连 5.0 Broker 要注意什么？
3. Helm upgrade 失败如何回滚？
4. 配置项改名如何发现？
5. 升级前必做哪三项检查？

---

## 核心知识

### 升级分类

| 类型 | 风险 | 策略 |
|------|------|------|
| 补丁/安全 | 低 | 滚动重启单节点 |
| 小版本 | 中 | 预发全量回归 + 生产滚动 |
| 大版本 | 高 | 蓝绿或新集群迁移 Client |

### 升级前检查清单

1. **Release Notes**：废弃配置、默认行为变化（如 ACL 默认 deny）。
2. **导出备份**：EMQX 规则 JSON、认证数据、Helm values、证书。
3. **兼容性**：设备 MQTT 版本、TLS 套件、Paho 版本。
4. **压测基线**：[C11](C11-loadtest-connections.md) 关键指标存档。

### EMQX 滚动（K8s）

```text
helm upgrade emqx ./chart -f values-prod.yaml
→ 观察 Pod Ready 与 /api/v5/status
→ 逐批设备 OTA 非必须；Client 应 automaticReconnect
```

- `PodDisruptionBudget` 保证最少可用副本。
- 失败：`helm rollback <release> <revision>`。

### Mosquitto 开发机

- 拉新镜像 → `docker compose pull && up -d` → 跑 `mvn compile`。
- 持久化卷备份 `mosquitto/data`。

---

## 生产环境注意点

- 升级窗口选 **业务低谷**；通知可能短暂重连（[P6](../04-问题百科/P6-disconnect.md)）。
- **禁止** 跳多个大版本一步到位；按官方路径逐级升。
- 升级后 24h **加强监控**（[C5](C5-monitoring.md)）：auth_failed、connect_rate、rule errors。
- 证书与 JDK/OTP 依赖随镜像变，CI 镜像需同步。
- 变更单记录：版本号、执行人、回滚命令。

---

## 易错点与反例

1. **未读 Release Notes 直接 helm upgrade** — 配置静默失效。
2. **同时升 Broker 与全量固件 MQTT5** — 问题无法二分。
3. **无 rollback revision** — 只能重装。
4. **升级时改 ACL 与版本一起** — 归因困难。
5. **预发与生产 chart version 不一致** — 预发验证无效。

---

## 动手验证

```powershell
# Mosquitto 版本
docker exec -it <container> mosquitto -h

# 本仓脚本回归
cd examples\java; mvn -q compile
```

EMQX：`GET /api/v5/status` 对比 `version` 字段；抽样 100 设备在线率。

---

## 相关章节

- [C8 HA](C8-ha-cluster.md) | [C1 部署](C1-deployment.md) | [C10 Runbook](C10-failure-runbook.md)
- [附录 I 环境迁移](../附录/I-env-migration-checklist.md)
