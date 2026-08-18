# P4 项目：从 Shared + 非分区 + Auto-Create 迁移

> **目标：** 用数据和灰度证明新策略更稳，并产出可评审的 [附录 K](../appendices/K-方案一页纸模板.md) 一页纸。  
> **前置：** [B13](../part-b-java-dev/B13-推动策略改造.md)、[B3](../part-b-java-dev/B3-消费者.md)、[B12](../part-b-java-dev/B12-环境模型.md)

---

## 适用场景

团队当前类似：

- `SubscriptionType.Shared`
- 非分区 Topic（`create` 时未指定分区或默认单分区）
- `allowAutoTopicCreation` 开启（开发/生产均未区分）

若调研后发现**无顺序要求、流量极低**，本项目可只做 **阶段 1（治理）**，不做 2/3。

---

## 阶段 0：调研清单（2~3 天）

### 0.1 Topic 与订阅盘点

```powershell
# 列出 namespace 下所有 topic（按你们 tenant/ns 改）
docker exec pulsar-standalone bin/pulsar-admin topics list public/default
# 或生产集群执行
```

填表：

| Topic 全路径 | 分区数 | 生产/消费服务 | subscriptionName | 订阅模式 | Producer 是否带 Key | 峰值 msg/s | 是否要求有序 |
|--------------|--------|---------------|------------------|----------|---------------------|------------|--------------|
| | | | | Shared | | | |

### 0.2 代码扫描（Java 多服务）

在仓库搜索：

```
SubscriptionType.Shared
SubscriptionType.KeyShared   # 或 Key_Shared
newProducer(                  # 是否 .key(
allowAutoTopicCreation
persistent://
```

记录：**哪些服务、哪些 Topic** 需要改。

### 0.3 抓一条证据

对**最核心**的一个 Topic 执行：

```powershell
docker exec pulsar-standalone bin/pulsar-admin topics stats persistent://<tenant>/<ns>/<topic>
```

记录：`msgRateIn`、`msgRateOut`、各 subscription 的 `backlog`。

可选：运行 [SharedOrderingDemo](../examples/java/pulsar-troubleshooting/src/main/java/com/demo/pulsar/trouble/SharedOrderingDemo.java) 对比 Key_Shared（本地 Standalone）。

**产出：** 填 [附录 K](../appendices/K-方案一页纸模板.md) 第 1~3 节。

---

## 阶段 1：治理（低风险，先做）

| 步骤 | 动作 | 验收 |
|------|------|------|
| 1.1 | 文档化 Topic 命名规范 | [B4](../part-b-java-dev/B4-多服务协作.md) |
| 1.2 | 脚本预建测试/生产 Topic | `scripts/setup-dev-tenant.ps1` 作模板扩展 |
| 1.3 | **生产**关闭 Auto-Create（Broker 配置） | 故意拼错 Topic 应失败而非静默创建 |
| 1.4 | 配置 Retention / Backlog Quota（至少测试环境） | `namespaces set-retention` / `set-backlog-quota` |

**对上级说法：** 「第一期不动业务逻辑，只避免建错 Topic 和磁盘失控。」

---

## 阶段 2：单 Topic 灰度 Key_Shared（1~2 周）

选一个 **有序要求高、流量中等** 的 Topic（不要一上来改最大的）。

### 2.1 Producer 改动

```java
producer.newMessage()
    .key(orderId)   // 或 deviceId，与业务一致
    .value(payload)
    .send();
```

### 2.2 Consumer 改动

```java
.subscriptionType(SubscriptionType.Key_Shared)
.keySharedPolicy(KeySharedPolicy.stickyHashRange())
// subscriptionName 保持不变，便于对比
```

### 2.3 灰度方式（择一）

| 方式 | 做法 | 适用 |
|------|------|------|
| A | 新 subscription 名并行消费，对比 backlog | 可双倍消费，仅测试环境 |
| B | 单 Consumer 实例先上 Key_Shared | 生产常用 |
| C | 新 Topic 名，流量双写后切 | 最稳，改动大 |

### 2.4 对比指标（前后各跑 24h 或压测 30min）

| 指标 | 改造前 Shared | 改造后 Key_Shared |
|------|---------------|-------------------|
| backlog 峰值 | | |
| 乱序 case 数 | | |
| P99 处理延迟 | | |
| Consumer CPU | | |

**产出：** 更新附录 K 第 3、4 节。

---

## 阶段 3：分区规划（按流量）

### 3.1 估算

```
目标吞吐(MB/s) ÷ 每分区 5~10 MB/s = 建议分区数（取整，预留 30%）
```

见 [B10](../part-b-java-dev/B10-性能调优.md)。

### 3.2 实施注意

- **不能减少分区**
- 推荐：**新建分区 Topic** → 应用双写 → 切 Consumer → 停旧 Topic
- 或：`update-partitioned-topic` **只增不减**

```powershell
# 新建 8 分区示例
pulsar-admin topics create-partitioned-topic persistent://dev/test/order-events -p 8
```

### 3.3 压测

- 本地：`pulsar-loadtest` 模块冒烟（[C11](../part-c-ops/C11-十万设备压测.md)）
- **真实数据必须在 Cluster 上测**（[B12](../part-b-java-dev/B12-环境模型.md)）

---

## 阶段 4：推广与收尾

- [ ] 将其余「有序」Topic 按阶段 2 模板推广
- [ ] 明确「继续 Shared」的 Topic 清单（埋点等）写入团队 Wiki
- [ ] Grafana 告警：backlog、msgRateOut < msgRateIn
- [ ] 复盘：附录 K 第 8 节评审结论

---

## 回滚方案

| 变更 | 回滚 |
|------|------|
| Key_Shared | 改回 Shared + 原 subscription（需重启 Consumer） |
| 新 Topic 双写 | 停新 Topic 写入，只写旧 Topic |
| 加分区 | 无法减分区；回滚=切回旧非分区 Topic |
| 关 Auto-Create | 临时开回（不推荐长期） |

---

## 毕业标准

- [ ] 完成阶段 0 盘点表
- [ ] 附录 K 一页纸已评审（至少 1 位开发 + 1 位负责人）
- [ ] 至少 1 个核心 Topic 完成 Key_Shared 灰度并有对比数据
- [ ] 生产（或预发）已关 Auto-Create 且 Topic 脚本化
- [ ] 能用自己的话向同事解释：**为什么埋点 Topic 仍用 Shared**

---

## 相关

- [B13 说服策略](../part-b-java-dev/B13-推动策略改造.md)
- [附录 K](../appendices/K-方案一页纸模板.md)
- [附录 I 迁移清单](../appendices/I-环境迁移清单.md)
- [P9 本地 OK 集群不行](../part-d-problems/P9-本地与集群差异.md)
