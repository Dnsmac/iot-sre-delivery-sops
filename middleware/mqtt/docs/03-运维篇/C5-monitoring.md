# C5 监控与告警

> 优先级: **P3 运维** | 预计阅读 35 分钟 | 深度：已深化

## 本章解决什么问题

建立 MQTT 接入层的 **可观测性**：连接数、消息速率、延迟、规则队列、桥接状态、认证失败等核心指标，并区分 Mosquitto（开发最小集）与 EMQX（生产 Prometheus/Grafana），做到故障 **5 分钟内可定位**。

---

## 面试常问

1. MQTT Broker 最需要监控哪五个指标？
2. 如何发现「慢消费者」？
3. EMQX Prometheus 如何接入？
4. 连接数正常但业务说收不到消息怎么查？
5. 告警阈值如何设才不误报？

---

## 核心知识

### 黄金指标（接入层）

| 指标 | 含义 | 告警方向 |
|------|------|----------|
| `connections` | 当前/峰值连接 | 接近 `max_connections` |
| `connect_rate` | 每秒新建连接 | 突增（OTA/攻击） |
| `messages_in/out` | 入站/出站 TPS | 骤降或暴涨 |
| `auth_failed` | 认证失败计数 | 持续升高 |
| `rule/bridge backlog` | 规则或桥接队列 | 持续 > 阈值 |

### Mosquitto 开发环境

- 日志：`log_dest stdout`，关注 `New connection`、`Socket error`。
- 系统：`docker stats`、连接数 `mosquitto_sub` 模拟 + 脚本计数。
- 无内置 Prometheus 时，**不要** 用开发监控方案冒充生产。

### EMQX 生产

- 内置 **Prometheus exporter**（端口与路径以 5.x 文档为准）。
- Dashboard：实时连接、主题流量 TopN、节点健康。
- 日志分级：`connection`、`authentication`、`rule_engine` 关键字检索（ELK/Loki）。
- **分布式追踪**：网关服务可对 `PUBLISH` 注入 trace id（用户属性 MQTT 5.0）。

### 业务层 SLI

```text
设备上报 → Broker 收到 → 规则写出 Pulsar → 消费 lag
         ↑____________ 全链路 lag 告警 ____________↑
```

- Pulsar **backlog** 与 MQTT 指标 **分开面板、联合告警**。

---

## 生产环境注意点

- 告警必须带 **环境、集群、节点** 标签，避免预发半夜叫醒生产 on-call。
- 连接数突降可能是 **LB 故障** 而非设备离线（见 [C10](C10-failure-runbook.md)）。
- 保留 **30 天** 指标用于容量复盘（[C2](C2-capacity.md)）。
- 认证失败单独告警，与 DDoS  brute force 区分（速率 + 源 IP 聚合）。
- On-call Runbook 链接到 [C10](C10-failure-runbook.md) 各条目。

---

## 易错点与反例

1. **只监控 CPU 不监控连接** — 内存先爆。
2. **TPS 高就不告警** — 可能是重试风暴（见 [P2](../04-问题百科/P2-duplicate.md)）。
3. **未监控 TLS 证书过期** — 8883 全断。
4. **Dashboard 公网暴露** — 18083 未加固。
5. **日志采样关太狠** — 排障无 CONNECT 证据。

---

## 动手验证

```powershell
# Mosquitto 日志
docker compose -f docker/docker-compose-mosquitto.yml logs -f

# 模拟流量后看订阅端是否收到
mosquitto_pub -h localhost -t dev/mon/ping -m 1 -r
mosquitto_sub -h localhost -t dev/mon/ping -C 1 -v
```

EMQX：浏览器打开 `http://<内网>:18083`，核对 Connections / Topics 页与 Prometheus scrape 是否 `UP`。

---

## 相关章节

- [C10 Runbook](C10-failure-runbook.md) | [C2 容量](C2-capacity.md) | [C8 HA](C8-ha-cluster.md)
- [附录 E 决策树](../附录/E-troubleshooting-decision-tree.md) | [B11 性能验证](../02-开发篇/B11-performance-verification.md)
