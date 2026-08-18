# C7 EMQX 规则引擎

> 优先级: **P3 运维** | 预计阅读 35 分钟 | 深度：已深化

## 本章解决什么问题

用 EMQX **规则引擎 SQL** 在 Broker 侧完成过滤、富化、路由到 Pulsar/Kafka/HTTP/Republish，减少自研网关代码；同时理解规则执行语义、失败重试与测试方法，避免「一条 SQL 拖垮集群」。

---

## 面试常问

1. EMQX 规则引擎和 Kafka Streams 的定位差异？
2. 规则里如何解析 JSON Payload？
3. 规则执行失败会怎样？会丢消息吗？
4. 如何做规则灰度？
5. Mosquitto 有规则引擎吗？

---

## 核心知识

### 处理链路

```text
PUBLISH 命中 FROM 主题
    → SQL SELECT / WHERE / 函数
        → 动作：republish | Pulsar | Webhook | 存储 ...
```

### SQL 示例（概念）

```sql
SELECT
  payload.temp AS temp,
  clientid AS device_id,
  timestamp AS ts
FROM "prod/+/telemetry"
WHERE json_decode(payload)['temp'] > 80
```

- **FROM**：主题过滤器，支持 `+`、`#`（注意性能）。
- **函数**：`json_decode`、`base64_decode`、`now()` 等（以 EMQX 5.x 文档为准）。
- **动作**：写 Pulsar 时配置 endpoint、topic、auth；HTTP 动作注意超时。

### 与 Mosquitto 对比

| | Mosquitto | EMQX |
|---|-----------|------|
| 规则引擎 | 无 | 内置 SQL |
| 开发替代 | 自研消费者 | 规则 + 轻量脚本 |

开发阶段可在 Mosquitto 用 **Java 订阅** 模拟规则逻辑，上线前迁 EMQX SQL。

### 运维要点

- 规则 **独立 ID**、版本注释、变更走 Git（导出 JSON）。
- 单条规则 **避免** 全站 `#` 无 WHERE；高 TPS 主题单独规则。
- **动作异步失败** 进入重试队列 → 监控 backlog（[C5](C5-monitoring.md)）。

---

## 生产环境注意点

- 新规则先在 **影子主题** `staging/...` 验证，再切 `prod/...`。
- Payload 异常（非 JSON）要 **判空**，否则规则抛错中断该条。
- 与 [C4 桥接](C4-bridge.md) 统一：写 Pulsar 的 Key、Schema 由规则输出字段固定。
- 升级 EMQX 前导出规则备份（[C9](C9-upgrade.md)）。
- 权限：规则 API 仅运维角色可改。

---

## 易错点与反例

1. **SELECT * 转发超大 Payload** — 规则 CPU 与出口带宽爆炸。
2. **多条规则重复订阅同一主题** — 重复写 Pulsar（见 [P2](../04-问题百科/P2-duplicate.md)）。
3. **WHERE 未索引式过滤** — 每条消息 JSON 解析全量字段。
4. **HTTP 动作同步阻塞** — 拖慢 MQTT 投递线程。
5. **以为规则 exactly-once** — 仍按至少一次设计幂等。

---

## 动手验证

1. EMQX Dashboard → **规则** → 创建 FROM `dev/rule/#` → 动作 **Republish** 到 `dev/rule/out`。
2. `mosquitto_pub -t dev/rule/in -m '{"temp":90}'`（若桥到 Mosquitto 仅作概念；生产直连 EMQX）。
3. 用 `mosquitto_sub -t dev/rule/out -v` 或 Dashboard **规则命中统计** 确认计数增加。

---

## 相关章节

- [C4 桥接](C4-bridge.md) | [C5 监控](C5-monitoring.md) | [C10 Runbook](C10-failure-runbook.md)
- [B2 发布](../02-开发篇/B2-publish.md) | [P4 积压](../04-问题百科/P4-slow-backlog.md)
