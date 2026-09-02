# 资深 Java · IoT 平台 · 10 周回薪仓库（深圳 25K · v3）

> **冲刺入口**：先读 [`PROGRESS_LOG.md`](PROGRESS_LOG.md) §当前快照，再打开 [`05-Interview-Prep/冲刺日历-2026-09-02.md`](05-Interview-Prep/冲刺日历-2026-09-02.md) 的当天行。
> **阶段**：9 月收口证据 · 10 月深度补洞 · **11-01 起主投**；[`PLAN.md`](PLAN.md) 只作总纲。
> **定位**：5 年+ **Java 后端（IoT 平台）** — 11 年 Java（电商/社区）+ 1 年+ IoT 现网  
> 画像：[`05-Interview-Prep/个人画像.md`](05-Interview-Prep/个人画像.md)

---

## 目录

| 路径 | 用途 |
|------|------|
| **[`PROGRESS_LOG.md`](PROGRESS_LOG.md)** | **当前快照**：phase、active_schedule、今日 P0、open gaps Top1 |
| **[`05-Interview-Prep/冲刺日历-2026-09-02.md`](05-Interview-Prep/冲刺日历-2026-09-02.md)** | **09-02～12-15 唯一每日执行入口** |
| [`05-Interview-Prep/学习路径与面试串讲.md`](05-Interview-Prep/学习路径与面试串讲.md) | 知识路径与面试串讲索引，不再排当天日课 |
| [`02-EMQX-IoT-Tuning/W1_全景信心手册.md`](02-EMQX-IoT-Tuning/W1_全景信心手册.md) | 历史 W1 证据材料，冲刺期不按它排课 |
| [`05-Interview-Prep/JD雷达/`](05-Interview-Prep/JD雷达/) | 猎聘高频词 · W1～W6 并行 |
| [`05-Interview-Prep/行业雷达/`](05-Interview-Prep/行业雷达/) | **特办** · 跑脚本 + **读 L1 ≤5min**（[`tools/industry-radar/`](tools/industry-radar/)） |
| [`05-Interview-Prep/stories/电商-高并发模块.md`](05-Interview-Prep/stories/电商-高并发模块.md) | 11 年 Java 信用 · W7 定稿 |
| [`05-Interview-Prep/带节奏-钩子反抛话术卡.md`](05-Interview-Prep/带节奏-钩子反抛话术卡.md) | **带面试官节奏**（6 钩子 + 3 反抛 + 开场 30s） |
| [`05-Interview-Prep/通用场景题-L4口播稿.md`](05-Interview-Prep/通用场景题-L4口播稿.md) | **11 道通用场景 L4 口播**（秒杀/TopK/一致性哈希…） |
| [`05-Interview-Prep/Notes口播深挖-数据库与网络.md`](05-Interview-Prep/Notes口播深挖-数据库与网络.md) | **Notes 加厚**（MySQL 10 题 + 网络 8 题 L4） |
| [`05-Interview-Prep/场景题-容量预估L4-GIIC15W标准用例.md`](05-Interview-Prep/场景题-容量预估L4-GIIC15W标准用例.md) | **场景题模板**（容量/故障两型可复用） |
| **[`05-Interview-Prep/面试备战计划书-必问L4.md`](05-Interview-Prep/面试备战计划书-必问L4.md)** | **备战总纲**（简历反推 7 必问维度 · L4 刻度 · gap 分析 · 每日节奏） |
| [`05-Interview-Prep/面试题库-按简历倒逼.md`](05-Interview-Prep/面试题库-按简历倒逼.md) | **按简历反推 80+ 题**（A 必背 / B 分模块 / C 全文背诵） |
| [`05-Interview-Prep/深追L4-套题-GIIC-OOM-MySQL-队列-JVM.md`](05-Interview-Prep/深追L4-套题-GIIC-OOM-MySQL-队列-JVM.md) | **50 题五段卡片**（一句话+数字+展开+追问+证据） |
| [`01-K8s-Troubleshooting/W1_每日学习手册.md`](01-K8s-Troubleshooting/W1_每日学习手册.md) | **W4** 才用 |
| [`docs/每日复习与串联指南.md`](docs/每日复习与串联指南.md) | 复习：7 问 / 90 秒 IoT 串讲 |
| [`docs/文档真相源.md`](docs/文档真相源.md) | **现网口径唯一真相**（冲突时优先） |
| [`docs/现网仓库只读约束.md`](docs/现网仓库只读约束.md) | **`D:\gerrit\iot-server` 只读 · 证据只写本仓** |
| [`PLAN.md`](PLAN.md) | v3 总览（含 `middleware/` 原理学习），不另排冲突日课 |
| [`docs/每日协作约定.md`](docs/每日协作约定.md) | **问「今天干什么」→ 快照 → active schedule 当天 → P0/P1/P2** |
| **[`skills/`](skills/)** | **BSP `/bsp` Skills** · BUG 修复编排（同事安装用） |
| [`02-EMQX-IoT-Tuning/`](02-EMQX-IoT-Tuning/) | W1～W3、W6 压测参与 |
| [`02-EMQX-IoT-Tuning/iot-server模块故事.md`](02-EMQX-IoT-Tuning/iot-server模块故事.md) | **主炮故事**（W4～W5 定稿，已落地） |
| [`02-EMQX-IoT-Tuning/IoT稳定性排查SOP.md`](02-EMQX-IoT-Tuning/IoT稳定性排查SOP.md) | **故事 #3**（operatorCache OOM 五段） |
| [`01-K8s-Troubleshooting/`](01-K8s-Troubleshooting/) | W4～W5 |
| [`03-Observability/`](03-Observability/) | W6 监控 |
| [`04-Middleware-Linux/`](04-Middleware-Linux/) | W3/W6 Pulsar 现网 SOP |
| [`middleware/`](middleware/) | **MQTT / Pulsar / Kafka 原理学习**（L2 补课） |
| [`05-Interview-Prep/`](05-Interview-Prep/) | 9 月收口、10 月深度补洞、11-01～12-15 主投 |

**中间件原理**（L2）：[`middleware/`](middleware/) — mqtt · pulsar · kafka（见 [`middleware/README.md`](middleware/README.md)）

**现网源码（只读）**：`D:\gerrit\iot-server` — 禁止修改；读代码 → 写本仓证据。见 [`docs/现网仓库只读约束.md`](docs/现网仓库只读约束.md)

---

## 你现在在哪一周？

| 周 | 主文档 / 交付 | 日历（可顺延） |
|----|---------------|----------------|
| **SPRINT** | [`冲刺日历-2026-09-02.md`](05-Interview-Prep/冲刺日历-2026-09-02.md) | **09-02～12-15 唯一每日入口** |
| W1（历史） | [`W1_全景信心手册.md`](02-EMQX-IoT-Tuning/W1_全景信心手册.md) | 全链路骨架 + JD雷达 ≥2；仅作证据回看 |
| W2 | 全链路定稿 + MQTT + 连接治理 | 06-09～ |
| W3 | IoT 稳定性 SOP | 06-16～ |
| W4～W5 | K8s + **模块故事定稿** | 06-23～07-06 |
| W6 | Pulsar 章 + 监控 + **压测参与复盘** | 07-07～ |
| W7～W8 | JD 雷达 + 简历 + 三故事录音 | **09-15～09-30**（并入冲刺日历执行） |
| **10 月** | MySQL/Redis/网络/Netty/JVM/七维二轮 | **10-01～10-31 深度补洞月** |
| **W9～W10** | 投递 / 谈薪 | **11-01～12-15** |

解锁：每周 §9 ≥8/9。W1～W6 可在职顺延，**9/30 前须完成 W8 之前全部证据**。

---

## 10 周终局

1. 核心证据（见 PLAN §核心证据，含 JD 雷达 + 压测**参与**复盘）  
2. 简历 6 条 bullet → 终版（W7）  
3. **3 旗舰故事**各 3min：电商 Java → IoT 平台模块 → 稳定性  
4. **11-01 起**投递 ≥24 条（理想 28）+ 复盘（10 月深度补洞，不赶投递 KPI）
5. ≥1 次 23～28K 谈薪或 offer  

---

## 生产组件（IoT 全链路）

```text
[设备] --MQTT:1883--> MetalLB VIP --> iot-web(nginx透传) --> iot-server(EventBus)
                                                                    |→ ES / MySQL / Redis
```

→ [`02-EMQX-IoT-Tuning/IoT全链路白板.md`](02-EMQX-IoT-Tuning/IoT全链路白板.md)（**已录入现网梳理**）
