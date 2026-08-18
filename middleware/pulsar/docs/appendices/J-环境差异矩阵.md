# 附录 J：环境差异速查矩阵

> 深度：全文加深 ✓ | 决策时对照，避免「开发能跑生产挂」

---

## 一、三环境总表

| 维度 | 开发 Standalone | 压测 Cluster | 生产 Cluster/K8s |
|------|-----------------|--------------|------------------|
| **目标** | 逻辑正确、学 API | 性能上限、容量签字 | 稳定、安全、可观测 |
| **Tenant/NS** | `dev/test` | `stress/*` 或同 prod 结构 | `company/production` |
| **Topic** | Auto-Create 可开 | **预建、与 prod 同拓扑** | **禁 Auto-Create** |
| **分区数** | 随意 | **= prod** | 按容量规划 |
| **订阅模式** | 可 Shared 偷懒 | **= prod** | Key_Shared 等按设计 |
| **Batching** | 可关 | **与 prod 一致** | 开 + LZ4 |
| **压缩** | 可选 | 与 prod 一致 | 大消息必开 |
| **TLS** | 无 | 建议开 | **必须** |
| **Auth** | 无 | 建议 JWT | **必须 RBAC** |
| **监控** | 可选 | 完整 | 完整 + 告警 On-call |
| **Retention** | 短（1d） | 接近 prod | 合规天数 |
| **压测签字** | ❌ 仅趋势 | ✅ | ✅ 复验 |

---

## 二、行为差异（易忽略）

| 现象 | Standalone | Cluster |
|------|-----------|---------|
| 最大连接数 | 低 | 高（+ Proxy） |
| Bundle 迁移 | 无 | 有 |
| Bookie 故障演练 | 不真实 | 可演练 |
| advertisedAddress 问题 | 少见 | **常见**（K8s） |
| 性能数字 | 不可签字 | 可签字 |

---

## 三、配置项必须一致（压测 ↔ 生产）

1. `enableBatching` / `batchingMaxPublishDelay`
2. `compressionType`
3. 分区数、SubscriptionType
4. `receiverQueueSize`（可按比例缩）
5. `ackTimeout` 策略
6. Schema 类型与兼容性策略

**可不同：** retention 长度、Consumer 实例数（按流量缩比）。

---

## 四、Java 应用配置 profile

| Profile | `PULSAR_URL` | `tenant/ns` |
|---------|--------------|-------------|
| dev | localhost:6650 | dev/test |
| stress | stress-proxy:6651 | company/stress |
| prod | prod-proxy:6651 | company/production |

见 [B8](../part-b-java-dev/B8-配置管理.md)。

---

## 五、何时必须上 Cluster

- [ ] 性能/容量 **签字**
- [ ] 连接数 > 数千
- [ ] TLS/Auth 联调
- [ ] Bookie 故障演练
- [ ] C11 10W 设备压测

---

## 相关

- [B12](../part-b-java-dev/B12-环境模型.md) | [B11](../part-b-java-dev/B11-性能验证.md) | [附录 I](I-环境迁移清单.md)
