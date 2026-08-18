# Part D 问题百科

> **用途：** 按现象查原因、排查命令、解法与关联章节。每篇已按 [DEPTH-STANDARD](../DEPTH-STANDARD.md) 加深（批次 3）。  
> **使用方式：** 生产告警 → 本表定位 → 打开对应 P 文档 → 按「排查步骤」执行 → 回到 Part A/B 补原理。

---

## 索引表

| 现象 | 文档 | 优先级 | 深度 |
|------|------|--------|------|
| 消息丢失 | [P1](P1-消息丢失.md) | P1 | ✓ |
| 重复消费 | [P2](P2-重复消费.md) | P1 | ✓ |
| 消息乱序 | [P3](P3-消息乱序.md) | P1 | ✓ |
| Backlog 积压 | [P4](P4-积压.md) | P1/P2 | ✓ |
| 性能不够 | [P5](P5-性能不足.md) | P1/P2 | ✓ |
| 连接断开 | [P6](P6-连接问题.md) | P2 | ✓ |
| Schema 报错 | [P7](P7-Schema问题.md) | P2 | ✓ |
| OOM | [P8](P8-内存溢出.md) | P2 | ✓ |
| 本地 OK 集群不行 | [P9](P9-本地与集群差异.md) | P2 | ✓ |
| K8s 问题 | [P10](P10-K8s问题.md) | P2/P3 | ✓ |
| Bookie 磁盘满 | [P11](P11-Bookie磁盘满.md) | P3 | ✓ |

---

## 按场景快速路由

| 你在做什么 | 先看 |
|------------|------|
| 面试「丢消息/重复/乱序」 | P1 → P2 → P3 |
| 开发 Java 客户端 | P1/P2 + [B2](../part-b-java-dev/B2-生产者.md) / [B3](../part-b-java-dev/B3-消费者.md) |
| 监控 backlog 涨 | P4 → P5 → [A7](../part-a-interview/A7-保留与清理策略.md) |
| 上生产连不通 | P6 → P9 → P10 |
| 10W 设备压测前 | P4、P5、[B13](../part-b-java-dev/B13-推动策略改造.md)、[C11 项目](../projects/) |
| 磁盘告警 | P11 → P4 → A7 |

---

## 与 Part A/B 的对应关系

```
Part D（现象）          Part A（原理）           Part B（代码）
─────────────────────────────────────────────────────────────
P1 丢失        ←→    A6 ACK, A7 Retention    B2 send, B3 ack
P2 重复        ←→    A6                      B3 Consumer
P3 乱序        ←→    A5 订阅                 B2 Key, B13 改造
P4 积压        ←→    A7 Backlog Quota        B3 并发
P5 性能        ←→    A2 架构                 B10 调优
P6/P9/P10 连接 ←→    A3 多租户               B9 排障
P7 Schema      ←→    附录 F                  Schema API
P8 OOM         ←→    —                       B3/B4 参数
P11 磁盘       ←→    A7, A2 BookKeeper       Part C 运维
```

---

## 排障通用命令（Standalone）

```powershell
docker exec pulsar-standalone bin/pulsar-admin topics stats persistent://dev/test/hello
docker exec pulsar-standalone bin/pulsar-admin topics stats-internal persistent://dev/test/hello
docker exec pulsar-standalone bin/pulsar-admin namespaces policies persistent://dev/test
```

集群将 `docker exec pulsar-standalone` 换为对应 `pulsar-admin` 执行环境。

---

## 示例代码入口

| 问题 | 示例 |
|------|------|
| ACK/丢失 | `examples/java/pulsar-troubleshooting` |
| 性能 | `examples/java/pulsar-producer-tuning`、`pulsar-loadtest` |
| 基础收发 | `examples/java/pulsar-basics` |

验证脚本：`scripts/verify-examples.ps1`
