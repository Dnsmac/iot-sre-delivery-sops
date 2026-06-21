# CoAP 轻量学习仓设计（Phase A · 2026-05-30）

> **学员决策**：**A（Kafka 轻量模式）**，Phase B（实验/Docker/Californium）**以后补**。  
> **状态**：待学员批准 → 再写 `docs/superpowers/plans/2026-05-30-coap-learning-repo.md` 并实施。

---

## 1. Goal

新建外链仓 **`D:\demo\coap`**，补齐猎聘/智联 **「MQTT + CoAP」** JD 防御；结构对齐 **`D:\demo\kafka`**（面试 Part A 为主），**不**在 Phase A 做 Docker/Java 实验。

主仓 `iot-sre-delivery-sops` 只负责：**外链表 + JD雷达/05 + 1 句现网口径**，不重复造 CoAP 大纲。

---

## 2. 非目标（Phase A 不做）

- `docker/`、Californium 示例、`examples/java/`
- Part B/C/D 正文（仅 **INDEX 占位** + `DEEPENING-ROADMAP.md` 列 Phase B）
- 修改 `D:\gerrit\iot-server`（只读引用类名）
- 把 CoAP 写进设备主链路（主链路仍为 **MQTT 1883 → EventBus**）

---

## 3. 现网口径（面试诚实）

| 维度 | 口径 |
|------|------|
| **设备主接入** | **MQTT TCP 1883** → iot-server 内嵌 MqttServer → EventBus |
| **CoAP 在平台** | JetLinks 系 **多协议支持**；gerrit 可见 `official-protocol` / Californium、`GIIC`、软总线 CoAP 配置（**只读核对**） |
| **个人日常** | 主要改 **iot-server MQTT/级联**；CoAP 能讲 **选型 + 平台有支持 + 与 MQTT 差异** |
| **JD 答法** | 「海量长连接实时双向 → MQTT；窄带 UDP/受限设备 → CoAP；我们平台多协议，我主 MQTT 接入，CoAP 学过并对照过现网协议包」 |

---

## 4. 仓结构（Phase A 交付）

```text
D:\demo\coap\
├── README.md
└── docs/
    ├── LEARNING-PATH.md      # 今天/明天、30秒/3分钟面试串讲
    ├── STUDY-TRACKER.md      # 勾选 + 日志（约 10 天 Phase A）
    ├── INDEX.md              # Part A 索引 + P1/P2 标记
    ├── DEEPENING-ROADMAP.md  # Phase B 清单（Californium、Observe 实验…）
    ├── part-a-interview/
    │   ├── A1-CoAP是什么.md
    │   ├── A2-UDP与REST模型.md
    │   ├── A3-资源URI与方法.md
    │   ├── A4-消息类型CON-NON-ACK.md
    │   ├── A5-Observe订阅.md
    │   ├── A6-DTLS与安全.md
    │   ├── A7-LwM2M与多协议网关.md
    │   └── A8-选型与面试题.md
    ├── appendices/
    │   ├── B-MQTT对照.md     # 与 mqtt/附录/B 互链
    │   └── C-现网JetLinks对照.md  # gerrit 只读索引（类名/配置关键词）
    ├── part-b-java-dev/INDEX.md   # Phase B 占位
    ├── part-c-ops/INDEX.md
    └── part-d-problems/INDEX.md
```

**深度标准**：每篇 A **≥1 屏**（定义 + 面试 3 问 + 与 MQTT 一句对照）；A8 含 **10 道简答**。

---

## 5. Part A 章节要点

| 章 | P1 | 核心内容 |
|----|-----|----------|
| A1 | 必学 | CoAP 定位：UDP、RESTful、IoT 受限设备；与 HTTP/MQTT 关系 |
| A2 | 必学 | 无连接 UDP、请求/响应、代理；为何省流量 |
| A3 | 必学 | `coap://host/path`、GET/POST/PUT/DELETE、资源树 |
| A4 | 必学 | CON/NON/ACK/RST；可靠 vs 不可靠；对比 MQTT QoS |
| A5 | 强荐 | Observe 选项 = 服务端推送；对比 MQTT 订阅 |
| A6 | 强荐 | DTLS、PSK/Certificate；对比 MQTT TLS |
| A7 | 按需 | LwM2M 基于 CoAP；多协议网关（MQTT+CoAP 并存） |
| A8 | 必学 | 选型决策树 + 10 面试简答（链 mqtt 附录 B 决策树） |

---

## 6. 互链

| 从 | 到 | 内容 |
|----|-----|------|
| `coap/appendices/B-MQTT对照.md` | `mqtt/docs/附录/B-protocol-comparison.md` | 双向链接 |
| `mqtt/附录/B` 文末 | `coap` LEARNING-PATH | 「深读 CoAP → coap 仓」 |
| `coap/appendices/C-现网JetLinks对照.md` | `iot-sre-delivery-sops` 真相源 | 主链路仍 MQTT |
| `PLAN.md` §外链 | `D:\demo\coap` | 读法见 §7 |
| `JD雷达/05` | coap A1～A4 + 附录 B/C | 三行模板 + 外链 |

**gerrit 只读引用（附录 C，不写密钥）**：

- `khlinks-official-protocol` / `CoapClientTest.java`
- `ProtocolTransferType.CoAP_TCP_GIIC`
- `application.yml` 中 `hmac-include-coap-header`（仅说明存在）

---

## 7. 本计划读法（写入 PLAN 一行）

| 周 | 用法 | 章节 |
|----|------|------|
| **W2 并行** | ~0.5h，不抢 MQTT 主线 | A1 + A2 + 附录 B |
| **W3 或 W6 空档** | JD 防御加深 | A4 + A5 + A8 前 5 题 |
| **W7 前** | 定稿 `JD雷达/05` | A1～A4 + 附录 C 写「现网 30 秒」 |
| **Phase B** | 空档/面试后 | DEEPENING-ROADMAP：Californium、docker-coap、Observe demo |

---

## 8. 主仓改动范围（实施计划 Task）

| 文件 | 操作 |
|------|------|
| `PLAN.md` §外链 | **Modify** 增加 CoAP 行；JD 雷达表 #5 改链 `D:\demo\coap` |
| `README.md` | **Modify** 外链列表加 coap |
| `05-Interview-Prep/JD雷达/README.md` | **Modify** 外链指向 coap |
| `05-Interview-Prep/JD雷达/05-CoAP与多协议.md` | **Create** 三行模板 + 链 coap A1/B/C |
| `docs/文档真相源.md` | **Modify** 外链列表加 coap（可选 1 行） |
| `05-Interview-Prep/个人画像.md` | **Modify** 协议在学：`mqtt/coap/pulsar` 路径补全 |
| `D:\demo\mqtt/docs/附录/B-protocol-comparison.md` | **Modify** 文末加 coap 仓链接 |
| **`D:\demo\coap/**` | **Create** 全文 Phase A 骨架 |

**不改**：W1 周历顺序、设备主链路白板、`.cursorrules` 大改。

---

## 9. 验收标准

- [ ] `D:\demo\coap` 存在且 `README` + `LEARNING-PATH` + **A1～A8 均有正文**（非空壳）
- [ ] mqtt 附录 B ↔ coap 附录 B **双向可点**
- [ ] `PLAN.md` 外链表含 CoAP，JD雷达 #5 指向 coap（非仅 mqtt 附录）
- [ ] `JD雷达/05-CoAP与多协议.md` 已创建（三行模板）
- [ ] 附录 C 含现网口径：**主 MQTT、辅 CoAP 多协议**，无「设备主链路走 CoAP」表述
- [ ] Phase B 仅在 `DEEPENING-ROADMAP.md` 列出，**无** docker/java 目录

---

## 10. Phase B（延后 · 仅记录）

| 项 | 内容 |
|----|------|
| 时间 | Phase A 毕业或 W8 后 |
| 交付 | `docker/docker-compose-coap.yml`、Californium HelloCoAP、`part-b-java-dev/B1`、Observe demo |
| 触发 | 学员说「补 CoAP B」或 JD 面试被 CoAP 动手题打穿 |

---

## 11. Spec 自检

| 检查 | 结果 |
|------|------|
| TBD/占位 | 无关键路径 TBD；Phase B 边界明确 |
| 内部矛盾 | 与真相源「MQTT 主链路」一致 |
| 一次可实施 | Phase A 单次会话可建 coap 仓 + 主仓联动 |
| 学员决策已反映 | A 轻量 + 以后 B ✅ |

---

## 12. 批准后下一步

1. 学员确认本 spec  
2. `writing-plans` → `docs/superpowers/plans/2026-05-30-coap-learning-repo.md`  
3. 实施：先 `D:\demo\coap`，再主仓 `PLAN` / JD雷达 / mqtt 互链  
4. `verification-before-completion`：`rg CoAP` 联动 spot-check
