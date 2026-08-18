# 附录 H：MQTT 学习与实践资源

> 与本仓库 [FRAMEWORK-TECH-LEARNING.md](../FRAMEWORK-TECH-LEARNING.md) 配合使用。

---

## 规范与标准

| 资源 | 链接 | 用途 |
|------|------|------|
| MQTT 3.1.1 | https://docs.oasis-open.org/mqtt/mqtt/v3.1.1/mqtt-v3.1.1.html | 面试、报文语义 |
| MQTT 5.0 | https://docs.oasis-open.org/mqtt/mqtt/v5.0/mqtt-v5.0.html | 属性、错误码、共享订阅 |
| MQTT SN | https://www.oasis-open.org/committees/mqtt/ | 网关场景了解 |

---

## 客户端与 Broker

| 资源 | 链接 |
|------|------|
| Eclipse Paho Java | https://www.eclipse.org/paho/index.php?page=clients/java/index.php |
| Paho GitHub | https://github.com/eclipse/paho.mqtt.java |
| Mosquitto | https://mosquitto.org/documentation/ |
| EMQX 文档 | https://www.emqx.io/docs |
| HiveMQ | https://www.hivemq.com/docs/ |

---

## 本仓库章节路径

| 目标 | 章节 |
|------|------|
| 面试 | Part A + [附录 A](A-interview-questions.md) |
| 写代码 | Part B |
| 运维 | Part C |
| 排障 | Part D + [B9](../02-开发篇/B9-troubleshooting.md) |
| 迁移 | [P4](../实战项目/P4-migrate-qos-topic.md) + [附录 K](K-one-page-proposal-template.md) |

---

## 示例代码

| 模块 | 路径 |
|------|------|
| 基础/QoS | `examples/java/mqtt-basics/` |
| 连接压测 | `examples/java/mqtt-loadtest/` |

---

## 工具

| 工具 | 说明 |
|------|------|
| MQTT Explorer | 图形化浏览 topic（开发） |
| mosquitto_pub/sub | [附录 F](F-mosquitto-cli-cheatsheet.md) |
| Wireshark MQTT 解析 | 协议级排障 |
| EMQX Dashboard | 连接、规则、ACL |

---

## 社区与博客（精选）

- EMQX 博客：规则引擎、性能调优案例  
- Mosquitto 邮件列表 / GitHub Issues：ACL、桥接细节  

---

## 学习顺序建议（4 周）

| 周 | 内容 |
|----|------|
| 1 | A1–A7 + mosquitto CLI |
| 2 | B1–B4 + Paho 示例 |
| 3 | B9–B13 + Part D 索引 |
| 4 | C1/C5/C11 + 附录 K 演练 |

---

## 相关

- [INDEX.md](../INDEX.md) | [STUDY-TRACKER.md](../STUDY-TRACKER.md)
