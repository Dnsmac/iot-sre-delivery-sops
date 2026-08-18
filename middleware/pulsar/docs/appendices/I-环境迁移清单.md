# 附录 I：Standalone → Cluster 迁移 Checklist

> 深度：全文加深 ✓ | 配合 [P3 项目](../projects/P3-上集群迁移.md)、[B12](../part-b-java-dev/B12-环境模型.md)

---

## 使用说明

- 打印本表或复制到 Wiki，**逐项勾选并填负责人/日期**
- 第 1~9 项为**应用侧**；第 10~14 为**平台侧**
- 预发与生产各跑一遍

---

## Checklist（14 项详解）

| # | 检查项 | 怎么做 | 不做的后果 | ✓ |
|---|--------|--------|------------|---|
| 1 | **serviceUrl** 指向 Cluster/Proxy | `pulsar://` 或 `pulsar+ssl://` 用 LB/DNS；非 localhost | 连不上、连错环境 | |
| 2 | **Tenant/Namespace 预建** | `tenants create` + `namespaces create` | TopicNotFound | |
| 3 | **关闭 Auto-Create** | `allowAutoTopicCreation=false` | 静默建错 Topic | |
| 4 | **Topic 脚本化** | IaC/脚本与代码配置一致 | 环境漂移 | |
| 5 | **Schema 注册** | `schemas upload` 或首次生产带 Schema | IncompatibleSchema | |
| 6 | **subscriptionName 统一** | 全环境 = 服务名登记册 | 抢消息/进度乱 | |
| 7 | **Batching/压缩** | 与生产一致（压测环境尤其） | 吞吐差 5~10× | |
| 8 | **ackTimeout** | ≥ 处理 P99×3 | 重复消费暴增 | |
| 9 | **DLQ/Retry** | deadLetterPolicy 配置 | 失败消息无限重试 | |
| 10 | **blockIfQueueFull** | Producer true | 静默丢或 OOM | |
| 11 | **TLS** | `pulsar+ssl://` + 信任链 | 连接拒绝 | |
| 12 | **Auth Token/JWT** | 各服务独立角色 | 401/越权 | |
| 13 | **Retention/TTL/Backlog Quota** | Namespace 策略 | 磁盘满/数据意外删 | |
| 14 | **监控告警** | Prometheus + backlog/磁盘 | 故障不可见 | |

---

## 冒烟脚本（迁移当天）

```bash
# 1. 健康
pulsar-admin brokers healthcheck
pulsar-admin bookies list-bookies -rw

# 2. 收发
pulsar-client produce persistent://<tenant>/<ns>/health-check -m "ok"
pulsar-client consume persistent://<tenant>/<ns>/health-check -s health-sub -n 1

# 3. 应用启动自检（可选）
```

---

## 回滚准备

| 项 | 回滚 |
|----|------|
| serviceUrl | 指回 Standalone（仅紧急） |
| 配置 | 保留上一版 ConfigMap/yml |
| Topic | 双写期保留旧 Topic |

---

## 相关

- [P9 本地 vs 集群](../part-d-problems/P9-本地与集群差异.md) | [附录 J](J-环境差异矩阵.md) | [P4 改造](../projects/P4-订阅与Topic改造.md)
