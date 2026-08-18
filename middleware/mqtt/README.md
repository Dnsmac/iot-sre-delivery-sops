# MQTT 协议学习仓库

> **本仓索引**：[`../README.md`](../README.md) · **优先级：** 面试 P1 → 开发 P2 → 扩展 P3 | **技术栈：** Java 8+ + Eclipse Paho + Mosquitto 2.x  
> **母版框架：** [FRAMEWORK-TECH-LEARNING.md](FRAMEWORK-TECH-LEARNING.md)（可选对照 [Pulsar 仓](../pulsar/docs/FRAMEWORK-TECH-LEARNING.md)）

## 已替你做的决策

| 项 | 决策 | 理由 |
|----|------|------|
| 学习目标 | 面试 → 开发 → 运维 | 与你 Pulsar 路径一致 |
| 协议版本 | **3.1.1 为主**，5.0 在 A10 扩展 | 工业界 3.1.1 仍最多；5.0 面试加分 |
| Broker | 本地 **Mosquitto**；集群 **EMQX** 在 C 章 | 轻量上手；企业集群再学 EMQX |
| Java 客户端 | **Eclipse Paho** | 事实标准、资料多 |
| 编译 | Java 8 | 与 Pulsar 示例环境一致 |
| 设备规模 | 10W 连接场景写入 C11/P4 | 对齐你业务背景 |

## 文档深度

- [DEPTH-STANDARD](docs/DEPTH-STANDARD.md) | [DEEPENING-ROADMAP](docs/DEEPENING-ROADMAP.md) | [实施 Plan](docs/设计/计划/2026-05-27-mqtt-outline.md)

## 学习入口（按这个顺序）

1. **[学习路径](docs/学习路径.md)** — 今天/明天学什么、28 天顺序、面试开场、知识串联  
2. **[进度勾选](docs/STUDY-TRACKER.md)** — 每日日志与 D1~D28 打勾  
3. **[全局索引](docs/INDEX.md)** — 章节列表与面试权重  
4. **[设计 Spec](docs/设计/规格/2026-05-27-mqtt-learning-outline-design.md)**

## 快速开始

```powershell
cd docker
docker compose -f docker-compose-mosquitto.yml up -d
cd ..\examples\java
mvn -q -pl mqtt-basics compile exec:java "-Dexec.mainClass=com.demo.mqtt.HelloMqtt"
```

连通探测：`mosquitto_pub -h localhost -t dev/test/hello -m ping -q 1`  
TLS 与证书见 [docker/certs/README.md](docker/certs/README.md)、[B6 本地环境](docs/02-开发篇/B6-local-dev.md)。

## 文档目录（中文）

| 目录 | 内容 |
|------|------|
| [docs/01-面试篇](docs/01-面试篇/) | Part A |
| [docs/02-开发篇](docs/02-开发篇/) | Part B |
| [docs/03-运维篇](docs/03-运维篇/) | Part C |
| [docs/04-问题百科](docs/04-问题百科/) | Part D |
| [docs/附录](docs/附录/) | 附录 A~K |
| [docs/实战项目](docs/实战项目/) | P1~P4 |
| [docs/设计](docs/设计/) | Spec / Plan |

## 与 Pulsar 的关系

MQTT 常作为 **设备接入协议**，后端可桥接到 Pulsar/Kafka。学完本仓后建议对照 Pulsar 环境模型做「MQTT 网关 + Pulsar」架构。
