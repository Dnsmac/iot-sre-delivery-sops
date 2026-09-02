# JD-06 · AI 玩具 · IoT Java 后端

> **采集**：2026-09-02  
> **匹配分**：`—`

---

## 岗位职责

**A. 设备侧**

1. AI 玩具**接入平台**：连接、鉴权、**指令下发、状态监控**。
2. 设备数据**清洗、解析、规则处理**；存储、监控、分析、**AI 训练**供数。
3. **MQTT、WebSocket** 实时双向通信；稳定低延迟。

**B. 消费业务**

4. 对接蚂蚁等后端：订单/交易/用户**实时同步**。
5. 消费数据清洗、建模、分析 API。
6. 支付/订单/会员/设备管理 **API**；支付宝/微信/AI 服务商回调。

**C. 运维**

7. 服务器运维、日志、监控、部署。
8. **GitLab CI / Jenkins / Docker** CI/CD。

---

## 任职要求

**必备**

- **Java** + **Spring Boot / Spring Cloud**
- **MQTT、WebSocket** 设备接入实战
- **MySQL、Redis**；RESTful；HTTP/HTTPS
- IoT **设备认证与安全**基础
- 支付宝/微信开放平台对接了解
- Linux 运维；**Git、Maven、Docker**

**加分**

- AI 玩具/智能硬件/儿童产品
- **大规模设备接入**
- **设备影子、OTA**
- **CoAP、LwM2M**

---

## 关键词

`MQTT` `WebSocket` `CoAP` `LwM2M` `设备影子` `OTA` `Spring Cloud` `CI/CD`

---

## 与现网证据（初映射）

| JD 点 | 你可讲 | 证据 |
|-------|--------|------|
| 大规模接入 | 15W GIIC | 主炮 |
| MQTT | 内嵌 MqttServer | W1 |
| **CoAP** | **GIIC 主责线** | 差异化亮点 |
| WebSocket | 平台有 HTTP 线 | 弱，不吹 |
| 影子/OTA | 会话 Redis 路由 | JD雷达 02/03 |
| 消费支付 API | **ERP** 30s 兜底 | 画像 B9 |
| Docker/K8s | 单例 K8s | 26-云原生 |

---

## 本岗必背（待练）

- [ ] CoAP-TCP GIIC 60s（加分项对齐）  
- [ ] MQTT 下行 Redis 路由 30s  
- [ ] 设备认证：PSK/Login/Token Redis  
