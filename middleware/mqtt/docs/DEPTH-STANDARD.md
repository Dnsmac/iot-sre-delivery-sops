# 文档深度标准（MQTT 仓）

> 与 [Pulsar DEPTH-STANDARD](../../pulsar/docs/DEPTH-STANDARD.md) 对齐（可选参考）。

## 每章最低结构

见 Pulsar 母版；本仓 Part A/B/C/D/项目/附录均已按该结构深化（v1.0）。

## 字数参考（中文）

| 类型 | 最低 |
|------|------|
| Part A 单章 | 1500 字 |
| Part B 写代码章 | 1200 字 + 代码片段 |
| B9 单场景 | 400 字 |
| B10 | 2000 字 + 决策树 |
| Part C 单章 | 800 字 |
| Part D 单篇 | 600 字 |
| **附录 A** | **Top 15 题** 各 3~5 句答法；其余题见 Part A 章节（非 50 题逐条展开） |

## 代码与实验（本仓 MQTT 范围）

| 项 | 要求 |
|----|------|
| mqtt-basics | HelloMqtt / SubscribeDemo / QoSDemo |
| mqtt-troubleshooting | ≥6 个可运行 Demo，对应 B9 |
| mqtt-loadtest | ConnectionLoadTest |
| Docker | 1883 + 8883 TLS（见 [docker/certs/README.md](../docker/certs/README.md)） |
| 验证 | `examples/java` 下 `mvn -q compile`（Broker 已启动时可跑 Demo） |

## 流程产物

| 产物 | 路径 |
|------|------|
| Spec | `docs/设计/规格/2026-05-27-mqtt-learning-outline-design.md` |
| Plan | `docs/设计/计划/2026-05-27-mqtt-outline.md` |
| 进度 | `docs/DEEPENING-ROADMAP.md`、`docs/STUDY-TRACKER.md` |

深化进度：[DEEPENING-ROADMAP.md](DEEPENING-ROADMAP.md)
