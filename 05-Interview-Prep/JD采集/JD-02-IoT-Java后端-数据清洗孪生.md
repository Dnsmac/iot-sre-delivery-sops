# JD-02 · IoT Java 后端 · 接入 / 清洗 / 数字孪生

> **采集**：2026-09-02  
> **匹配分**：`—`

---

## 岗位职责

1. **核心模块**开发维护：独立功能、排障、**性能优化**，保障高可用与可扩展。
2. **需求分析、方案设计、API 规范**与技术文档。
3. 第三方平台与设备对接：**MQTT、Modbus、OPC-UA、HTTP、WebSocket**。
4. **实时数据流**：解析、格式转换、**去重、异常值过滤、缺失值填补**、指标聚合；稳定接入与分发。
5. **数字孪生**：为前端孪生大屏供数；多源异构（时序/空间/业务）。
6. **时序库**接入、写入与查询优化；Java/Python **离线清洗**；历史 / **BIM / GIS** 批处理。
7. 基于 **JeecgBoot / RuoYi** 低代码快速开发；部署与安全加固。

---

## 任职要求

| 维度 | 要求 |
|------|------|
| 经验 | 本科；**Java 后端 3～4 年** |
| Java | IO、**多线程**、集合、**JVM**；代码质量与调试 |
| 框架 | **Spring Boot、MyBatis**；微服务与中间件 |
| DB | **MySQL、达梦**；SQL 优化、索引、缓存；**Redis、MongoDB** |
| 协议 | HTTP/HTTPS、WebSocket、TCP/IP；**MQTT / Modbus / OPC-UA 至少一种** |
| MQ | **Kafka**；实时清洗项目经验 |
| 数据清洗 | 乱序、缺失、异常、重复处理；**TSDB**（TDengine/InfluxDB/IoTDB）优先 |
| 低代码 | JeecgBoot 或 RuoYi；Vue/React 基础 |
| 运维 | Linux 部署、**安全扫描加固** |

**加分**：数字孪生、智慧城市、工业互联网；视频流；BIM/GIS/PostGIS；AI 提效。

---

## 关键词

`数据清洗` `数字孪生` `TSDB` `Modbus` `OPC-UA` `达梦` `Kafka` `JeecgBoot`

---

## 与现网证据（初映射）

| JD 点 | 你可讲 | 证据 |
|-------|--------|------|
| MQTT 接入 | 内嵌 MqttServer + GIIC CoAP | W1 全链路 |
| 性能优化 | GIIC 15W · OOM 排查 | 复盘 · 深追 L4 |
| MySQL/达梦 | MySQL 生产档；项目用达梦 | GIIC-全栈 · 画像 |
| ES 时序 | 属性时序 + 450B/msg | 场景题 · Playbook §0.2 |
| 数据清洗 | **弱**（规则引擎/EventBus 边） | 诚实：参与链路，非清洗 owner |
| OpenAPI 拓扑 | 超级设备拓扑 TPS | openapi case |
| Kafka | **Pulsar** 级联口径 | 11-MQ 项目段 |

---

## 本岗必背（待练）

- [ ] 设备上报链路 90s（EventBus 非 Pulsar）  
- [ ] MySQL prod-128g + 池联动 30s  
- [ ] 数字孪生：用 OpenAPI 拓扑 + 物模型 30s 挂井  
