# 附录 H：推荐资源

> 深度：全文加深 ✓ | 按学习阶段使用，避免信息过载

---

## 一、官方文档（优先）

| 资源 | URL | 用途 |
|------|-----|------|
| Apache Pulsar 文档 | https://pulsar.apache.org/docs/ | 概念、配置、API |
| BookKeeper 文档 | https://bookkeeper.apache.org/docs/ | BK 运维与原理 |
| Java Client API | https://pulsar.apache.org/docs/client-libraries-java/ | 开发查阅 |
| Admin REST / CLI | https://pulsar.apache.org/docs/admin-api-overview/ | 运维 |

**版本：** 本仓库示例 **3.2.3**；生产常见 **2.11.x LTS** 或 **3.2.x**，以集群实际版本为准。

---

## 二、必读论文与文章

| 资料 | 说明 |
|------|------|
| BookKeeper 论文（HP 实验室） | 理解 Journal/Ledger、Quorum |
| Pulsar 存储分离设计博客 | StreamNative / Yahoo 工程博客 |

搜索关键词：`Apache BookKeeper design`、`Pulsar storage separation`。

---

## 三、社区与博客

| 来源 | 说明 |
|------|------|
| [StreamNative Blog](https://streamnative.io/blog/) | 实战、版本特性 |
| Apache Pulsar GitHub Discussions | 问题与 RFC |
| Stack Overflow `[apache-pulsar]` | 具体错误 |

---

## 四、与本仓库对照阅读

| 阶段 | 仓库章节 |
|------|----------|
| 面试 | Part A + [附录 A](A-面试题与参考答案.md) |
| 开发 | Part B + 附录 C/D |
| 排障 | Part D + 附录 E |
| 运维 | Part C + 附录 F/G |
| 改造 | B13 + 附录 K + P4 |
| 压测 | C11 + P5 项目 |

---

## 五、工具

| 工具 | 用途 |
|------|------|
| Pulsar Manager | Web 管理（可选） |
| Prometheus + Grafana | 生产监控 [C5](../part-c-ops/C5-监控告警.md) |
| pulsar-perf | 官方压测（Cluster） |
| 本仓库 `pulsar-loadtest` | Java 压测学习 |

---

## 六、版本升级时

1. 阅读目标版本 **Release Notes**
2. 对照 [C9](../part-c-ops/C9-升级迁移.md)
3. 在预发 Cluster 验证 Client 兼容性

---

## 七、不建议初学深挖

- 全部 Broker 源码（先完成 [C12](../part-c-ops/C12-源码导读.md) 路径）
- KoP 全部 Kafka 兼容矩阵（无迁移需求时）
- Oxia 元数据（未使用 3.x Oxia 时）

---

## 相关

- [STUDY-TRACKER](../STUDY-TRACKER.md) | [FRAMEWORK-TECH-LEARNING](../FRAMEWORK-TECH-LEARNING.md)
