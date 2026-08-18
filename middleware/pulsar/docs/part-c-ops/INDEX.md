# Part C 运维扩展（P3）

> 深度：批次 4 ✓ | 与 Part D 问题百科、B12 环境模型配合使用

## 索引

| 章节 | 文档 | 深度 | 主题 |
|------|------|------|------|
| C1 | [集群部署](C1-集群部署.md) | ✓ | Standalone/Cluster/K8s、角色 |
| C2 | [硬件规划](C2-硬件规划.md) | ✓ | 磁盘、容量粗算 |
| C3 | [BookKeeper 调优](C3-BookKeeper调优.md) | ✓ | E-Q-W、Journal、GC |
| C4 | [Broker 调优](C4-Broker调优.md) | ✓ | Cache、Bundle |
| C5 | [监控告警](C5-监控告警.md) | ✓ | Prometheus、阈值 |
| C6 | [安全](C6-安全.md) | ✓ | TLS、JWT、RBAC |
| C7 | [Geo-Replication](C7-跨机房复制.md) | ✓ | 跨机房复制 |
| C8 | [分层存储](C8-分层存储.md) | ✓ | Tiered / Offload |
| C9 | [升级迁移](C9-升级迁移.md) | ✓ | 版本、KoP |
| C10 | [故障 Runbook](C10-故障预案.md) | ✓ | On-call 场景表 |
| C11 | [10W 设备压测](C11-十万设备压测.md) | ✓ | 综合项目 |
| C12 | [源码导读](C12-源码导读.md) | ✓ | 进阶阅读路径 |

## 学习路径建议

```
C1 部署 → C2 硬件 → C3/C4 调优 → C5 监控 → C6 安全
                              ↘ C10 Runbook（随时查）
毕业项目：C11（衔接 A12、B10、B11、B12）
进阶：C7 C8 C9、C12
```

## 与 Part A/B/D 的链接

| Part C | 原理 | 开发 | 现象 |
|--------|------|------|------|
| C3 | A11 | B10 | P11 磁盘 |
| C4 | A12 | B11 | P5 性能 |
| C5 | — | B11 | Part D |
| C11 | A12 | B5/B10/B12 | P3/P4/P5 |
| C10 | — | B9 | Part D 全文 |
