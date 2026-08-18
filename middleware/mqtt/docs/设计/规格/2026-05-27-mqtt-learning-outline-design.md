# MQTT 协议学习大纲 — 设计文档 v0.1

> 状态：已确认（Agent 代决策）  
> 框架母版：[FRAMEWORK-TECH-LEARNING](../../FRAMEWORK-TECH-LEARNING.md)（链 Pulsar 仓）

## 决策记录

| 项 | 决策 |
|----|------|
| P1/P2/P3 | 面试 → Java 开发 → Broker 运维/EMQX |
| 协议 | MQTT 3.1.1 主线，5.0 在 A10 |
| Broker | Mosquitto（开发）/ EMQX（集群 P3） |
| Client | Eclipse Paho Java |
| 业务锚点 | 多服务、大数据量、10W 设备连接 |

## Part A 章节目录

A1 是什么与选型 | A2 架构 | A3 主题通配符 | A4 报文连接 | A5 QoS  
A6 会话保活 | A7 Retain/遗嘱 | A8 安全 | A9 Payload | A10 MQTT5  
A11 Broker 对比 | A12 性能规模

## Part B

B1 Paho 基础 | B2 发布 | B3 订阅 | B4 多服务 Topic 规范 | B5 大数据量  
B6 本地 Mosquitto | B7 Spring Integration MQTT | B8 配置  
B9 排障 12 场景 | B10 调优金字塔 | B11 验证 | B12 环境 | B13 推动 QoS/Topic 改造

## Part C / D / 项目

C1~C12 部署/EMQX/桥接/压测/Runbook  
D：断连/丢消息/重复/乱序/积压/OOM(P11)/本地vs生产/K8s  
P1 设备上报 | P2 QoS 升级 | P3 上生产 Broker | P4 从 QoS0+乱主题迁移 | C11 10W 连接压测

## 学习路径

Week 1-2 Part A + 附录 A/B  
Week 3-5 Part B + 示例  
Week 6+ Part C + C11  
全阶段 Part D + TRACKER
