# 中间件原理学习（MQTT · Pulsar · Kafka）

> **定位**：L2 原理补课层 — Part A～D 大纲、附录速查、Docker/Java 示例。  
> **本仓 L1 证据**（叙事 + 数字 + SOP）仍在 `02-EMQX-IoT-Tuning/`、`04-Middleware-Linux/`、`01-K8s-Troubleshooting/cases/`。  
> 总计划见 [`../PLAN.md`](../PLAN.md) §中间件原理学习。

---

## 子目录入口

| 中间件 | 路径 | 主入口 | 全局索引 |
|--------|------|--------|----------|
| **MQTT** | [`mqtt/`](mqtt/README.md) | [学习路径](mqtt/docs/学习路径.md) | [INDEX](mqtt/docs/INDEX.md) |
| **Pulsar** | [`pulsar/`](pulsar/README.md) | [LEARNING-PATH](pulsar/docs/LEARNING-PATH.md) | [INDEX](pulsar/docs/INDEX.md) |
| **Kafka** | [`kafka/`](kafka/README.md) | [LEARNING-PATH](kafka/docs/LEARNING-PATH.md) | [INDEX](kafka/docs/INDEX.md) |

**Kafka ↔ Pulsar 对照**（JD 写 Kafka、现网用 Pulsar 时）：

- [kafka/docs/appendices/B-Pulsar对照.md](kafka/docs/appendices/B-Pulsar对照.md)
- [pulsar/docs/appendices/B-Kafka对照.md](pulsar/docs/appendices/B-Kafka对照.md)

---

## 按周精读（绑本仓 PLAN）

| 周 | 读哪里 | 章节 | 本仓交付（写 L1，不复制大纲） |
|----|--------|------|------------------------------|
| **W1** | mqtt | A2 架构 | `02/IoT全链路白板.md` 骨架 |
| **W2** | mqtt | A4～A7、P6/P7；A11/C7 对照 | `协议卡片_MQTT.md`、`连接治理链路.md`、`EMQX生态对照.md` |
| **W3** | pulsar | P4 积压、C10 runbook | `02/IoT稳定性排查SOP.md` |
| **W6** | pulsar | P4、C10、附录 B | `04/中间件排障手册.md`（Pulsar 章） |
| **按需** | kafka | 附录 B + A1/A5 + P4 lag | 面试被问 Kafka 时；现网口径仍走 Pulsar |

JD 雷达各篇 ↔ 章节对照见 [`../PLAN.md`](../PLAN.md) §JD 雷达包。

---

## 本地实验（可选）

```powershell
# MQTT — Mosquitto
cd middleware\mqtt\docker
docker compose -f docker-compose-mosquitto.yml up -d

# Pulsar — Standalone
cd middleware\pulsar
.\scripts\standalone-up.ps1
.\scripts\setup-dev-tenant.ps1

# Kafka — 单节点 KRaft
docker run -d --name kafka-dev -p 9092:9092 `
  -e KAFKA_NODE_ID=1 -e KAFKA_PROCESS_ROLES=broker,controller `
  -e KAFKA_LISTENERS=PLAINTEXT://:9092,CONTROLLER://:9093 `
  -e KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://localhost:9092 `
  -e KAFKA_CONTROLLER_LISTENER_NAMES=CONTROLLER `
  -e KAFKA_CONTROLLER_QUORUM_VOTERS=1@localhost:9093 `
  apache/kafka:latest
```

---

## 仍在外链（未纳入本目录）

| 仓 | 路径 | 用途 |
|----|------|------|
| IoT 平台全景 | `D:\demo\iot\IoT-Technical-Guide` | 物模型 / 影子 / JD 雷达 |
| CoAP | `D:\demo\coap`（若有） | JD雷达/05 多协议 |
| **现网源码** | `D:\gerrit\iot-server` | **只读** — 见 [`../docs/现网仓库只读约束.md`](../docs/现网仓库只读约束.md) |
