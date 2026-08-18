# 技术学习框架（本仓入口）

完整母版见仓库根目录：

**[../FRAMEWORK-TECH-LEARNING.md](../FRAMEWORK-TECH-LEARNING.md)**

若本地有 Pulsar 姊妹仓，也可对照：[../../pulsar/docs/FRAMEWORK-TECH-LEARNING.md](../../pulsar/docs/FRAMEWORK-TECH-LEARNING.md)

## MQTT 特化摘要

| 框架块 | MQTT 特化 |
|--------|-----------|
| Part A | QoS、Retain、遗嘱、通配符、Clean Session |
| Part B | Paho、mosquitto_pub/sub、弱网 |
| B13 | QoS0 滥用、主题无规范、Clean Session 误用 |
| Part C | EMQX 集群、桥接 Pulsar/Kafka |
| C11 | 10W 连接 + QoS 组合压测 |
| Plan | [设计/计划/2026-05-27-mqtt-outline.md](设计/计划/2026-05-27-mqtt-outline.md) |
