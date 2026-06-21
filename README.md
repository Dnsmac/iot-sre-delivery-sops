# 资深 Java · IoT 平台 · 10 周回薪仓库（深圳 25K · v3）

> **W1 启动**：2026-06-02（5 月末可提前）· **每天 2h** · [`PLAN.md`](PLAN.md)（**6～9 月攒证据，10 月面试**）  
> **定位**：5 年+ **Java 后端（IoT 平台）** — 11 年 Java（电商/社区）+ 1 年+ IoT 现网  
> 画像：[`05-Interview-Prep/个人画像.md`](05-Interview-Prep/个人画像.md)

---

## 目录

| 路径 | 用途 |
|------|------|
| **[`05-Interview-Prep/学习路径与面试串讲.md`](05-Interview-Prep/学习路径与面试串讲.md)** | **今天/明天学什么 · 面试怎么串（主路径）** |
| **[`02-EMQX-IoT-Tuning/W1_全景信心手册.md`](02-EMQX-IoT-Tuning/W1_全景信心手册.md)** | **W1 日课** |
| [`05-Interview-Prep/JD雷达/`](05-Interview-Prep/JD雷达/) | 猎聘高频词 · W1～W6 并行 |
| [`05-Interview-Prep/行业雷达/`](05-Interview-Prep/行业雷达/) | **特办** · 跑脚本 + **读 L1 ≤5min**（[`tools/industry-radar/`](../tools/industry-radar/)） |
| [`05-Interview-Prep/stories/电商-高并发模块.md`](05-Interview-Prep/stories/电商-高并发模块.md) | 11 年 Java 信用 · W7 定稿 |
| [`01-K8s-Troubleshooting/W1_每日学习手册.md`](01-K8s-Troubleshooting/W1_每日学习手册.md) | **W4** 才用 |
| [`docs/每日复习与串联指南.md`](docs/每日复习与串联指南.md) | 复习：7 问 / 90 秒 IoT 串讲 |
| [`docs/文档真相源.md`](docs/文档真相源.md) | **现网口径唯一真相**（冲突时优先） |
| [`docs/现网仓库只读约束.md`](docs/现网仓库只读约束.md) | **`D:\gerrit\iot-server` 只读 · 证据只写本仓** |
| [`PLAN.md`](PLAN.md) | v3 总览（外链 mqtt/pulsar 仓） |
| [`docs/每日协作约定.md`](docs/每日协作约定.md) | **问「今天干什么」→ P0口述→P1主任务** |
| [`PROGRESS_LOG.md`](PROGRESS_LOG.md) | 进度 · **§当前快照**（Agent 先读） |
| [`02-EMQX-IoT-Tuning/`](02-EMQX-IoT-Tuning/) | W1～W3、W6 压测参与 |
| [`01-K8s-Troubleshooting/`](01-K8s-Troubleshooting/) | W4～W5 |
| [`03-Observability/`](03-Observability/) | W6 监控 |
| [`04-Middleware-Linux/`](04-Middleware-Linux/) | W3/W6 Pulsar |
| [`05-Interview-Prep/`](05-Interview-Prep/) | W7～W10 |

**外链学习仓**（原理深度）：`D:\demo\mqtt` · `D:\demo\pulsar` · `D:\demo\kafka`（见 PLAN §外链）

**现网源码（只读）**：`D:\gerrit\iot-server` — 禁止修改；读代码 → 写本仓证据。见 [`docs/现网仓库只读约束.md`](docs/现网仓库只读约束.md)

---

## 你现在在哪一周？

| 周 | 主文档 / 交付 | 日历（可顺延） |
|----|---------------|----------------|
| **W1** | [`W1_全景信心手册.md`](02-EMQX-IoT-Tuning/W1_全景信心手册.md) | 全链路骨架 + JD雷达 ≥2 |
| W2 | 全链路定稿 + MQTT + 连接治理 | 06-09～ |
| W3 | IoT 稳定性 SOP | 06-16～ |
| W4～W5 | K8s + **模块故事定稿** | 06-23～07-06 |
| W6 | Pulsar 章 + 监控 + **压测参与复盘** | 07-07～ |
| W7～W8 | JD 雷达 + 简历 + 三故事录音 | **09-15～09-30** |
| **W9～W10** | 投递 / 谈薪 | **10-01～11-09** |

解锁：每周 §9 ≥8/9。W1～W6 可在职顺延，**9/30 前须完成 W8 之前全部证据**。

---

## 10 周终局

1. 核心证据（见 PLAN §核心证据，含 JD 雷达 + 压测**参与**复盘）  
2. 简历 6 条 bullet → 终版（W7）  
3. **3 旗舰故事**各 3min：电商 Java → IoT 平台模块 → 稳定性  
4. **10 月起**投递 ≥24 条（理想 28）+ 复盘  
5. ≥1 次 23～28K 谈薪或 offer  

---

## 生产组件（IoT 全链路）

```text
[设备] --MQTT:1883--> MetalLB VIP --> iot-web(nginx透传) --> iot-server(EventBus)
                                                                    |→ ES / MySQL / Redis
```

→ [`02-EMQX-IoT-Tuning/IoT全链路白板.md`](02-EMQX-IoT-Tuning/IoT全链路白板.md)（**已录入现网梳理**）
