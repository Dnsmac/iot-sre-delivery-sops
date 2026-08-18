# B13 推动 QoS / Topic / 会话策略改造

> 优先级: **P2 开发** | 预计阅读 30 分钟 | 深度：已深化

## 本章解决什么问题

技术同学常发现「全 QoS0、topic 随意、Clean Session 乱用」的风险，但 **产品/业务不愿改**——怕影响在线设备、怕工期。本章提供 **何时可不动、何时必须改、证据化话术、分阶段迁移与评审材料**，并与 [附录 K：一页纸方案](../附录/K-one-page-proposal-template.md)、实战项目 [P4：QoS/Topic 迁移](../../实战项目/P4-migrate-qos-topic.md) 联动，便于在架构评审会上推进变更。

---

## 面试常问

1. 如何说服业务把关键流从 QoS0 升到 QoS1？→ 用丢包率数据 + 幂等成本说明，分阶段灰度。
2. Topic 规范改造要不要停服？→ 双写/双订阅过渡期，见 P4 阶段。
3. Clean Session 改成 false 有什么副作用？→ Broker 队列与存储涨，需容量评估。
4. 改造谁签字？→ 附录 K 一页纸 + 运维/安全/产品会签。

---

## 核心知识

### 决策：何时不用改

| 现状 | 条件 | 可维持 |
|------|------|--------|
| 全 QoS0 | 纯可丢遥测、业务容忍缺口、有 HTTP 补拉 | 维持，仅补监控 |
| 主题已规范 | 符合 B4 层级、ACL 已按前缀 | 补文档与静态检查 |
| Clean Session=true | 产品明确不需要离线 MQTT 投递 | 维持，平台用拉取补发 |
| Mosquitto 开发 | 规模 <1K、无生产承诺 | 维持开发模型，生产另立项换 EMQX |

**原则：** 无 **证据链（指标+事故）** 不推动大改；避免「为最佳实践而最佳实践」。

### 决策：何时必须改

| 现状 | 风险 | 建议 | Part D / 证据 |
|------|------|------|----------------|
| 关键指令 QoS0 | 网络抖丢失控车/配置 | 关键 topic QoS1 + 幂等 | [P1](../04-问题百科/P1-message-loss.md) |
| 主题随意 | ACL/桥接/检索不可维护 | B4 规范 + 迁移期双写 | [P9](../04-问题百科/P9-local-vs-prod.md) |
| 需离线却 clean=true | 上线收不到指令 | false + 稳定 ClientId | [P7](../04-问题百科/P7-offline-message.md) |
| 生产匿名 | 越权订阅/发布 | TLS + 账号 + ACL | [C6](../03-运维篇/C6-security-ops.md) |
| `prod/#` 订阅 | Broker CPU、扩缩容难 | 收窄 + 共享订阅 | [P5](../04-问题百科/P5-performance.md) |
| 单机 Mosquitto 扛 10W | 容量与 HA 不达标 | EMQX 集群立项 | [B12](B12-environment-models.md) |

### 倡导话术（对业务/产品）

1. **先对齐业务诉求，再谈协议：** 「哪些消息丢了会赔钱/合规？哪些丢了大不了？」——把 QoS 与产品表格对齐（附录 K §2）。
2. **用数据不用形容词：** 影子订阅 7 天对账、丢包 seq 缺口率、事故单号写入一页纸 §3。
3. **分阶段降风险：** 「只改一条指令 topic、只升一类设备、可回滚」——链 [P4](../../实战项目/P4-migrate-qos-topic.md) 阶段 0–3。
4. **说清不改代价：** 全 QoS0 在 4G 闪断下丢指令概率；主题混乱导致新功能上线周期 ×2。
5. **资源透明：** 人天、Broker 队列扩容、幂等存储（Redis/DB）一次性成本。

### 迁移阶段（与 P4 对齐）

| 阶段 | 动作 | 产出 |
|------|------|------|
| 0 盘点 | topic 清单、QoS、ClientId、retain、Broker 类型 | 现状表（附录 K §1） |
| 1 规范 | 定 B4 主题、ACL 草案、文档评审 | 规范 v1 + mosquitto/EMQX ACL 试运行 |
| 2 灰度 | 选 1 条关键流 QoS1 + 消费幂等；对比丢包 | [B11](B11-performance-verification.md) 报告 |
| 3 平台 | EMQX 集群、压测、监控、桥接对账 | 附录 K 评审结论 + 生产切换窗口 |

```java
// 阶段 2 双订阅过渡示例（旧 topic + 新 topic 各消费，幂等去重）
client.subscribe("legacy/device001/cmd", 1);
client.subscribe("prod/acme/device001/command", 1);
// dedupKey 含 messageId，两 topic 同一指令只处理一次
```

---

## 面试标准答案

**问：QoS 从 0 升到 1，团队抵触怎么办？**  
答：用附录 K 一页纸固定格式：列业务「必须不丢」项、贴 7 天影子订阅缺口率、给出仅改 1 个 topic 的灰度方案与回滚（改回 QoS0 + 关闭新消费者）。强调 QoS1 带来重复，需 2 人日幂等表，但可避免一次生产事故损失。评审通过后再扩面，见 P4 阶段 2。

---

## 生产环境注意点

- 变更窗口：低峰 + 可回滚配置（Feature Flag 控制 QoS 与 topic 生成器）。
- 与运维对齐：Broker `max_queued_messages`、会话数、规则引擎（[C3](../03-运维篇/C3-broker-tuning.md)）。
- 安全会签：关匿名、TLS、ACL 与 topic 前缀同步上线。
- 沟通模板：直接复制 [附录 K](../附录/K-one-page-proposal-template.md) 八节结构，勿口头提案。

---

## 易错点与反例

1. **未做幂等先全网上 QoS1** → 重复写库事故（[P2](../04-问题百科/P2-duplicate.md)）。
2. **一次性改全部 topic** → 设备固件未升级大面积收不到。
3. **只改云端不改边缘网关** → 网关仍发旧 topic。
4. **无回滚预案** → 评审被拒仍硬上。
5. **压测报告用 Mosquitto** → 容量承诺被架构组驳回。

---

## 动手验证

1. 填写 [附录 K](../附录/K-one-page-proposal-template.md) 草稿（30 分钟）。
2. 对照 [P4](../../实战项目/P4-migrate-qos-topic.md) 勾选阶段 0 盘点项。
3. 预约 30 分钟评审：产品（诉求）+ 运维（Broker）+ 安全（ACL）+ 开发（实现）。

---

## 相关章节

- [附录 K 一页纸](../附录/K-one-page-proposal-template.md)
- [P4 迁移项目](../../实战项目/P4-migrate-qos-topic.md)
- [B4 多服务主题规范](B4-multi-service-conventions.md) | [B10](B10-performance-tuning.md) | [B12](B12-environment-models.md)
- [Part D 索引](../04-问题百科/INDEX.md)
