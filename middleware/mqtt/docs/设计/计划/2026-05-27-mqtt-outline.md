# MQTT 学习仓库 — 实施计划 v1.0

> 对应 Spec：[2026-05-27-mqtt-learning-outline-design.md](../规格/2026-05-27-mqtt-learning-outline-design.md)  
> 标准：[DEPTH-STANDARD.md](../../DEPTH-STANDARD.md)

## 目标

MQTT 3.1.1 + Paho Java + Mosquitto（开发）/ EMQX（文档），支撑面试 P1、开发 P2、运维 P3（文档）。

## 任务清单

| ID | 任务 | 状态 |
|----|------|------|
| T1 | Spec 确认 | done |
| T2 | 脚手架 README/INDEX/TRACKER | done |
| T3 | Part A~D + 附录 + 项目文档深化 | done |
| T4 | 示例 mqtt-basics / loadtest / troubleshooting | done |
| T5 | Docker Mosquitto | done |
| T9 | 文档目录中文化；不依赖 scripts | done |
| T6 | **P0** Plan、DEPTH/ROADMAP 表述、TRACKER 说明、verify 冒烟 | done |
| T7 | **P1** TLS 8883 本地实验、排障 Demo 扩充、P11 OOM、B6/B9 链代码 | done |
| T8 | 学习者按 TRACKER 毕业考自测 | 用户执行 |

## 刻意不在本仓范围（见姊妹技能或业务项目）

- 物模型 / OTA / Netty 网关 / Modbus
- Spring Cloud 全栈、Kafka 消费业务服务
- EMQX 集群 compose（仅文档 P3）

## 验证

```powershell
cd docker; docker compose -f docker-compose-mosquitto.yml up -d
cd examples\java; mvn -q compile
```
