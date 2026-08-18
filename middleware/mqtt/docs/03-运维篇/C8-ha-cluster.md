# C8 集群与高可用

> 优先级: **P3 运维** | 预计阅读 40 分钟 | 深度：已深化

## 本章解决什么问题

说明 **EMQX 集群** 如何实现接入层高可用：节点发现、会话复制边界、负载均衡、脑裂与滚动升级；并明确 **Mosquitto 单机无集群** 的定位，避免用开发 Broker 推导生产 HA 方案。

---

## 面试常问

1. MQTT Broker 集群是无状态的吗？
2. ClientID 相同的两端同时连不同节点会怎样？
3. 会话粘滞是否必须？
4. EMQX 节点宕机后未送达消息怎么办？
5. 跨地域双活 MQTT 可行吗？

---

## 核心知识

### HA 架构

```text
        [LB TCP 8883]
       /    |    \
   EMQX-1 EMQX-2 EMQX-3
       \    |    /
      [集群总线 / Mnesia 等]
```

- **无状态部分**：监听器、路由表同步（实现因产品而异）。
- **有状态部分**：会话、飞行窗口、部分插件状态；节点故障时依赖 **会话接管** 策略。

### EMQX 集群要点

- **节点名与 cookie** 部署规范；K8s 用 Headless Service 做 DNS 发现。
- **quorum**：至少 3 节点避免脑裂两边各写（具体以官方 K8s Operator 为准）。
- **LB**：四层透传；不必粘滞 ClientID，但 **TLS 会话复用** 注意证书一致。
- **共享订阅**（MQTT 5.0）：`$share/group/topic` 用于应用层消费者负载均衡，与 Broker 集群不同层。

### Mosquitto

- 单进程；HA 需 **主备 + VIP** 或外部冷备，**非** 原生多活；本仓仅开发。
- 生产 HA **标准答案**：EMQX 集群 + 多 AZ LB。

### 容灾层级

| RTO 目标 | 方案 |
|----------|------|
| 分钟级 | 同 Region 3 节点 + LB 健康检查 |
| 小时级 | 跨 AZ，DNS 切换备用集群 |
| 天级 | 冷备 + 配置与证书同步 |

---

## 生产环境注意点

- 滚动重启 **逐节点**，确认 `emqx_cluster_nodes_running` 正常再摘下一台。
- 防火墙：集群总线端口 **仅内网** 互通。
- 备份：规则、认证数据、证书 Secret（GitOps）。
- 压测在 **集群形态** 下进行（[C11](C11-loadtest-connections.md)），非单节点 extrapolate。
- 与 Pulsar 多副本 **独立** 规划；MQTT 集群挂不影响已写入 Pulsar 的数据。

---

## 易错点与反例

1. **两节点「集群」** — 脑裂风险高，生产建议奇数节点。
2. **LB 健康检查用 HTTP 查 1883** — 误判节点存活。
3. **会话仅本地节点** — 故障转移后设备需重连并可能丢飞行中消息。
4. **跨 Region 强一致双写** — 延迟与冲突成本极高，慎用。
5. **K8s Pod 随机 DNS 作 MQTT 地址** — 设备应连 LB 固定入口（见 [P10](../04-问题百科/P10-k8s.md)）。

---

## 动手验证

- 本地无法用 Mosquitto 验证集群；使用 EMQX 3 节点 compose 或 Helm `replicaCount: 3`。
- 杀一个 Pod：`kubectl delete pod emqx-1` → 观察 Client 自动重连与 [C5](C5-monitoring.md) 连接总数恢复曲线。

---

## 相关章节

- [C1 部署](C1-deployment.md) | [C9 升级](C9-upgrade.md) | [C10 Runbook](C10-failure-runbook.md)
- [P6 断连](../04-问题百科/P6-disconnect.md) | [P10 K8s](../04-问题百科/P10-k8s.md)
