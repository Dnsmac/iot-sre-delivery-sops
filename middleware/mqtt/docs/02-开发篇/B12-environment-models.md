# B12 环境模型：开发 Mosquitto vs EMQX 集群 vs 边缘网关

> 优先级: **P2 开发** | 预计阅读 25 分钟 | 深度：已深化

## 本章解决什么问题

团队在 **本机 Mosquitto** 上开发通过后，常默认生产行为一致，导致上线后出现 TLS、ACL、容量、桥接、离线队列等「环境差」问题。本章定义三种典型 **环境模型** 的职责边界、能力矩阵与迁移注意点，并说明 **边缘网关** 如何改变连接数与 topic 拓扑。对照 [附录 I](../附录/I-env-migration-checklist.md)、[附录 J](../附录/J-env-diff-matrix.md)。

---

## 面试常问

1. Mosquitto 和 EMQX 在 10W 连接下差在哪？→ 集群、ACL、规则引擎、运维面板。
2. 开发环境能否开匿名？→ 仅本地；预发起与生产同构认证。
3. 边缘网关连接算谁的 ClientId？→ 网关一个连接，子设备用 topic 区分。
4. K8s 里 MQTT 怎么暴露？→ Service/Ingress、8883、sticky 可选。
5. 压测应在哪个环境签字？→ 预发 EMQX，非开发 Mosquitto。

---

## 核心知识

### 三种环境模型总览

```
┌─────────────────┐     ┌──────────────────────┐     ┌─────────────────┐
│ 模型 A          │     │ 模型 B               │     │ 模型 C          │
│ 开发 Mosquitto  │────▶│ 预发/生产 EMQX 集群   │◀────│ 边缘网关汇聚     │
│ 单机 localhost  │     │ LB + TLS + ACL       │     │ 子设备不直连云   │
└─────────────────┘     └──────────────────────┘     └─────────────────┘
   协议/业务调试              容量/HA/安全签字              降连接数、离线缓冲
```

### 模型 A：开发 Mosquitto（单机）

| 维度 | 典型配置 | 能力上限（经验） |
|------|----------|------------------|
| 地址 | `localhost:1883` | 单机 |
| 认证 | `allow_anonymous true` 常见 | 无企业级 RBAC |
| TLS | 通常关闭 | — |
| 连接数 | 1–500 调试 | >1K 需调优仍非生产目标 |
| 桥接 | 手动 `connection` 配置 | 适合 Pulsar 联调 |
| 监控 | `$SYS`（可选） | 无 EMQX 级规则面板 |
| 适用 | B1–B8 功能、单元测试、B9 场景复现 | **不代表** 10W SLO |

**开发约定：** `dev/{username}/...` topic 前缀；禁止把生产 ClientId 连到本机。

```bash
# docker-compose 或本地服务
mosquitto -c /path/mosquitto.conf
mosquitto_sub -h 127.0.0.1 -t 'dev/#' -v
```

### 模型 B：EMQX 集群（预发 / 生产）

| 维度 | 典型配置 | 说明 |
|------|----------|------|
| 接入 | TCP 1883 / TLS 8883 / WS | 生产仅 TLS |
| 负载均衡 | L4 LB VIP 或 K8s Service | 长连接注意 idle 超时 |
| 认证 | 用户名密码、JWT、TLS 证书 | 与 [C6](../03-运维篇/C6-security-ops.md) 一致 |
| ACL | 按租户前缀 | 与 [B4](B4-multi-service-conventions.md) 绑定 |
| 规模 | 10W+ 连接水平扩展 | 见 [B10](B10-performance-tuning.md)、[C2](../03-运维篇/C2-capacity.md) |
| 规则引擎 | MQTT → Pulsar/HTTP/Kafka | [C4](../03-运维篇/C4-bridge.md) |
| 监控 | Dashboard + Prometheus | [C5](../03-运维篇/C5-monitoring.md) |
| HA | 多节点 + 会话复制策略 | [C8](../03-运维篇/C8-ha-cluster.md) |

**K8s 生产附加项：**

| 项 | 开发 Mosquitto | K8s + EMQX |
|----|----------------|------------|
| 发现 | localhost | Service DNS |
| 证书 | 无 | cert-manager / 挂载 Secret |
| 网络 | 主机网络 | NetworkPolicy 放行 8883 |
| 伸缩 | 无 | HPA 看 CPU/连接（需厂商指引） |
| 问题百科 | — | [P10](../04-问题百科/P10-k8s.md) |

### 模型 C：边缘网关

| 维度 | 直连云 Broker | 经边缘网关 |
|------|---------------|------------|
| 连接数 | 每设备 1 | 每网关 1（子设备 N:1） |
| 离线 | 设备离线即无上报 | 网关可缓冲后批量上送 |
| Topic | `prod/.../deviceId/...` | 网关 ID + 子设备 ID 在 payload 或 topic 第三段 |
| 安全 | 每设备证书成本高 | 网关持证书，子设备局域网 |
| 适用 | 4G 直连、少量设备 | 工厂、楼宇、车载多子节点 |

```
子设备 D1..Dn ──(局域网 MQTT/Modbus)──▶ 边缘网关 G1 ──(TLS 1 连接)──▶ EMQX 集群
                                      聚合、QoS0 批量、本地规则
```

**注意：** 网关进程崩溃会触发 **一条** 遗嘱，平台需区分「网关离线」与「子设备离线」语义（topic 设计见 B4）。

---

## 环境能力对照总表

| 能力 | Mosquitto 开发 | EMQX 预发/生产 | 边缘 + EMQX |
|------|----------------|----------------|-------------|
| 协议调试 | ✅ 最佳 | ✅ | ✅（多一跳延迟） |
| 10W 连接 | ❌ | ✅ | ✅（有效连接↓） |
| 企业 ACL | 基础文件 | ✅ 细粒度 | 网关侧 + 云侧 |
| TLS/mTLS | 需自配 | ✅ | 网关终止或透传 |
| 规则引擎 | ❌ | ✅ | 网关轻量 + 云规则 |
| 共享订阅 | 有限/无 | ✅ | 云侧消费扩展 |
| 压测签字 | ❌ | ✅ | 需含网关缓冲场景 |
| 成本 | 低 | 集群+LB | 硬件+运维 |

---

## 面试标准答案

**问：为什么文档强调 Mosquitto 不能代表 10W 压测？**  
答：10W 长连接涉及文件描述符、会话状态、路由表、TLS 握手 CPU 与集群 HA，Mosquitto 单机架构并非为此设计。开发用它验证 **协议、topic、Paho 代码** 正确；容量与 SLO 必须在 **EMQX 预发** 用分布式压测复现，并写入 [B11](B11-performance-verification.md) 报告。

---

## 生产环境注意点

- 预发与生产 **同构**：同 EMQX 版本、同 TLS 策略、同 ACL 模式；仅规模可缩小。
- 配置中心区分 `spring.profiles` / 环境变量，禁止 fat jar 内写死 `localhost`。
- 边缘网关固件升级与云 topic 版本 **兼容矩阵** 单独维护。
- 从 A 迁到 B 走 [附录 I](../附录/I-env-migration-checklist.md) 12 项。

---

## 易错点与反例

1. **开发匿名，生产忘关** → [P9](../04-问题百科/P9-local-vs-prod.md)。
2. **在 Mosquitto 调优 max_connections 后推全公司容量** → 误导采购。
3. **边缘网关与子设备共用 ClientId** → 互踢断连。
4. **K8s 仅暴露 WS 端口却配了 TCP 客户端** → 连不上。
5. **桥接只在 Mosquitto 测通即上线** → EMQX 规则 SQL 错误生产才暴露。

---

## 动手验证

1. 列出团队三环境 Broker 地址、端口、是否 TLS（填 [附录 J](../附录/J-env-diff-matrix.md)）。
2. 用生产账号在预发执行 `mosquitto_sub` 冒烟（[B9 场景9](B9-troubleshooting.md)）。
3. 若有网关：统计「子设备数 / 云连接数」比，更新容量公式（[B10](B10-performance-tuning.md)）。

---

## 相关章节

- [B6 本地开发](B6-local-dev.md) | [B10 调优](B10-performance-tuning.md) | [B11 验证](B11-performance-verification.md)
- [附录 I 迁移清单](../附录/I-env-migration-checklist.md) | [附录 J 差异矩阵](../附录/J-env-diff-matrix.md)
- [Part D P9](../04-问题百科/P9-local-vs-prod.md) | [C1 部署](../03-运维篇/C1-deployment.md)
