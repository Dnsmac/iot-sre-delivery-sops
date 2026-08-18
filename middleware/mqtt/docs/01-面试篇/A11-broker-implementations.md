# A11 Broker 实现差异

> 优先级: **P1 面试** | 预计阅读 25 分钟 | 深度：已深化 | 学习路径：**D5 | 面试：★★★** | 主路径：[学习路径](../学习路径.md)

## 本章解决什么问题

选型 **Mosquitto vs EMQX vs 云托管**；知道单机开发与 **10W 连接集群** 该用谁，面试能对比不能只会背名字。

---

## 面试常问

1. Mosquitto 和 EMQX 区别？
2. 10W 设备连接选什么？
3. 桥接功能谁提供？
4. 开源 Broker 生产能用吗？
5. MQTT Broker 和 Kafka 能互相替代吗？

---

## 核心知识

| | Mosquitto | EMQX | 云 IoT（各厂商） |
|---|-----------|------|------------------|
| 定位 | 轻量、单机/边缘 | 企业集群、规则引擎 | 托管、按量 |
| 连接规模 | 数千级（视硬件） | 10W+ 集群 | 弹性 |
| 集群 | 弱/桥接为主 | 原生集群 | 托管 |
| 规则/桥接 | 基础桥接 | 丰富 | 产品化 |
| 适用 | **开发、边缘、小规模** | **生产大规模** | 快速上线 |

### 选型路径

```
开发本地 → Mosquitto (本仓 docker)
PoC/中小规模 → Mosquitto 或 EMQX 单节点
生产 1W+ 常在线 → EMQX 集群 + LB
分析归档 → 桥接到 Pulsar/Kafka (C4)
```

---

## 面试标准答案

### 题：为什么开发用 Mosquitto 生产用 EMQX？

> Mosquitto 部署简单、资源占用小，适合本机验证协议和客户端逻辑。生产要上十万连接、要集群高可用、要规则引擎把 MQTT 转内部系统，EMQX 更合适。不是 Mosquitto 不好，是定位不同，类似开发用嵌入式 DB、生产用分布式库。

### 题：Broker 实现不同 QoS 行为一样吗？

> 协议一致，但 **离线队列长度、持久化、性能** 配置不同。测试要在目标 Broker 上验证，不能只在 Mosquitto 测完就上 EMQX。

---

## 生产环境注意点

- 看 **license**（EMQX 开源版 vs 企业版功能）。
- 监控：连接数、消息速率、规则延迟、桥接堆积。

---

## 易错点与反例

1. **Mosquitto 单机扛 10W** — 易 OOM/断连。
2. **以为换 Broker 不用改客户端** — ACL、认证、端口可能不同。
3. **用 Kafka 直接替代 MQTT Broker** — 设备协议不兼容。

---

## 动手验证

```powershell
cd docker; docker compose -f docker-compose-mosquitto.yml up -d
```

EMQX：见 [C1](../03-运维篇/C1-deployment.md)。

---

## 相关章节

- [C1 部署](../03-运维篇/C1-deployment.md) | [C11 压测](../03-运维篇/C11-loadtest-connections.md)
