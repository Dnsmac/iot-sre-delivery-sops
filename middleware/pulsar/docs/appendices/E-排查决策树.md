# 附录 E：排查决策树

> 深度：全文加深 ✓ | 每叶节点链到 Part D / Part B 详文

---

## 使用方式

1. 从**现象**入口向下走  
2. 每步执行**一条命令**验证假设  
3. 未解决则打开链接中的 **P 文档** 完整排查  

**通用命令：**

```powershell
docker exec pulsar-standalone bin/pulsar-admin topics stats persistent://dev/test/<topic>
docker exec pulsar-standalone bin/pulsar-admin topics stats-internal persistent://dev/test/<topic>
```

---

## 1. 消息丢了？

```
消息丢了?
│
├─ Producer 异步 send 未处理失败?
│     └─ 是 → 加 whenComplete/exceptionally → [P1]
│
├─ topics stats 有 msgInCounter 增长?
│     ├─ 无 → Producer/Topic 名/权限 → [P1] [P6] [P9]
│     └─ 有 → 哪个 subscription 的 msgOut 不增?
│           ├─ 订阅名错误 → [B4]
│           └─ Consumer 未连接 → [P4]
│
├─ non-persistent Topic?
│     └─ 是 → 改 persistent
│
├─ TTL / Retention 过期?
│     └─ namespaces get-retention / get-message-ttl → [A7] [P1]
│
└─ Backlog eviction 丢消息?
      └─ get-backlog-quotas → [A7] [P11]
```

**详文：** [P1 消息丢失](../part-d-problems/P1-消息丢失.md)

---

## 2. 重复消费？

```
重复消费?
│
├─ 是否「至少一次」预期行为? → 业务幂等 → [P2]
│
├─ ackTimeout < 处理 P99?
│     └─ 调大 / 优化处理 → [P2] [B3]
│
├─ ACK 在写库之前?
│     └─ 先写库再 ACK → [P2]
│
├─ 频繁 negativeAcknowledge?
│     └─ DLQ + maxRedeliverCount → [A8]
│
└─ Shared + 多线程乱 ACK?
      └─ Key_Shared 或单线程 ACK → [P3]
```

**详文：** [P2 重复消费](../part-d-problems/P2-重复消费.md)

---

## 3. 消息乱序？

```
乱序?
│
├─ SubscriptionType == Shared?
│     └─ 是 → 预期行为；改 Key_Shared + Key → [P3] [B13]
│
├─ Producer 未设 key?
│     └─ 补 key → [B2]
│
├─ 非分区 + 多 Producer 异步?
│     └─ 分区 Topic 或单线程发 → [P3]
│
└─ NACK 重投递插队?
      └─ 幂等 + 版本号 → [P2]
```

**详文：** [P3 乱序](../part-d-problems/P3-消息乱序.md)

---

## 4. Backlog 积压？

```
Backlog 涨?
│
├─ Consumer connected == false?
│     └─ [P6] 连接 / 重启
│
├─ msgRateOut << msgRateIn?
│     ├─ 处理慢 → 优化/SQL/批处理 → [P4] [P5]
│     └─ Consumer 不够 → 扩实例+分区 → [P4]
│
├─ 单 Consumer backlog 极高?
│     └─ Key 热点 → [P5] [A12]
│
└─ producer_request_hold?
      └─ 消费跟不上，先止血再扩容 → [P4] [P11]
```

**详文：** [P4 积压](../part-d-problems/P4-积压.md)

---

## 5. 吞吐不够？

```
吞吐不够?
│
├─ sync send? → async + batch → [P5] [B10]
├─ batching 关闭? → 开启 → [附录 D]
├─ 分区数 < Consumer 数? → 加分区 → [A12]
├─ ADD_ENTRY P99 高? → Bookie 磁盘 → [C3] [P11]
└─ Standalone 测的? → Cluster 复测 → [B11]
```

**详文：** [P5 性能](../part-d-problems/P5-性能不足.md)

---

## 6. 连接 / 环境

```
连不上? → [P6]
本地 OK 集群不行? → [P9] [附录 I]
K8s? → [P10]
Schema 报错? → [P7] [L-schema-registry]
OOM? → [P8]
Bookie 磁盘满? → [P11]
```

---

## 7. 按角色速查

| 角色 | 先看 |
|------|------|
| 开发 | P1~P3、B9 |
| 运维 | P4、P11、C10 |
| 架构 | A12、B13、附录 B |

**完整索引：** [Part D INDEX](../part-d-problems/INDEX.md)

---

## 相关

- [B9 排障场景](../part-b-java-dev/B9-排障手册.md) | [C10 Runbook](../part-c-ops/C10-故障预案.md)
