# Pulsar 学习进度仪表盘

> **路径与串讲（先看）：** [LEARNING-PATH.md](LEARNING-PATH.md) — 今天/明天学什么、面试怎么讲、知识主线  
> 章节索引：[INDEX.md](INDEX.md) | 优先级：**面试 P1 → 开发 P2 → 扩展 P3**

---

## 今日 / 明日（快速导航）

> 根据你当前进度改「今天」；**明天 = 下一行**。

| 你若在第… | 今天建议 | 明天建议 |
|-----------|----------|----------|
| 刚开始 | [A1](part-a-interview/A1-Pulsar是什么.md) + [A2](part-a-interview/A2-核心架构.md) | [A3](part-a-interview/A3-多租户层级.md) + [A4](part-a-interview/A4-Topic体系.md) |
| 第 1 周中 | 见 [LEARNING-PATH 第 1 周表](LEARNING-PATH.md#第-1-周建立骨架g1) | 表中「明日学」列 |
| 第 2 周 | [附录 A](appendices/A-面试题与参考答案.md) 或 B1~B3 | 见 [LEARNING-PATH 第 2 周](LEARNING-PATH.md#第-2-周面试毕业--开发入门g1g2) |
| 面试前 3 天 | 附录 A 每天 10 题 + [3 分钟自述](LEARNING-PATH.md#32-3-分钟结构面试官最常要) | 模拟追问表 [LEARNING-PATH §3.3](LEARNING-PATH.md#33-追问往哪引不要散) |
| 推动改造 | [B13](part-b-java-dev/B13-推动策略改造.md) → [P4](projects/P4-订阅与Topic改造.md) | [附录 K](appendices/K-方案一页纸模板.md) |

完整 38 天表：[LEARNING-PATH §四](LEARNING-PATH.md#四按天路径今天--明天6-周)

---

## 怎么用

1. 打开 [LEARNING-PATH](LEARNING-PATH.md)，确认自己在 **G1/G2/G3** 哪条目标上
2. 按「今日→明日」学，结束在 [每日日志](#每日日志) 写 1 条 + **1 句项目结合**
3. 在 [模块状态表](#模块状态表) 更新：`未学` → `已学` → `已毕业`
4. Part D、附录 G/L、C7~C12：**按需查**；C/D/E/F 作字典

---

## 什么叫「不用再看了」

满足 **4 条至少 3 条**，可标 **已毕业**：

| 标准 | 含义 |
|------|------|
| **能讲** | 不看文档，3 分钟内讲清（用 [LEARNING-PATH 主线](LEARNING-PATH.md#二一条知识主线全仓库串起来)） |
| **能用** | 代码/命令独立完成 |
| **能判** | 能判断「我们 Shared+非分区行不行」 |
| **能排** | 丢/重/乱/慢能定位 Part D 或 B9 |

---

## 模块状态表

> 状态：`未学` | `已学` | `已毕业` | 毕业日期：YYYY-MM-DD

| 模块 | 优先级 | 状态 | 毕业日期 | 备注 |
|------|--------|------|----------|------|
| **G1 Part A** A1~A4 | P1 | | | 骨架 |
| **G1 Part A** A5~A7 | P1 | | | 订阅/ACK/保留 |
| **G1 Part A** A8~A12 | P1 | | | A9/A10 可后置 |
| **G1 总复习** | P1 | | | [毕业考](#part-a-毕业考) + [面试串讲](LEARNING-PATH.md#三面试怎么讲开场--深入--结合项目) |
| **附录 A** 面试题 | P1 | | | 面试前每天 10 题 |
| **附录 B** Kafka 对照 | P1 | | | 有 Kafka 经验必学 |
| **G2 Part B** B1~B8 | P2 | | | 写代码 |
| **G2 Part B** B9~B11 | P2 | | | 排障调优 |
| **G2 Part B** B12 | P2 | | | 上 Cluster 前 |
| **G3** B13 + K + P4 | P2 | | | 推动改造 |
| **附录 C/F** | 字典 | | | 不必毕业 |
| **Part C** C1~C6 | P3 | | | 运维 |
| **Part C** C11 | P3 | | | 压测 |
| **Part C** C7~C12 | P3 | | | 按需 |
| **Part D** | 全阶段 | | | 索引即可 |
| **附录 L** | P2 | | | P2 前 |
| **项目 P1** | — | | | **跳过** |
| **项目 P2** | P2 | | | |
| **项目 P3** | P3 | | | |
| **项目 P4** | P2 | | | |
| **项目 P5~P7** | P3 | | | 按需 |

---

## 6 周日程（详情见 LEARNING-PATH）

与 [LEARNING-PATH 第四节](LEARNING-PATH.md#四按天路径今天--明天6-周) 同步；此处保留过关标志。

### 第 1 周 — G1 骨架

| 天 | 内容 | 当天过关 |
|----|------|----------|
| D1 | [A1](part-a-interview/A1-Pulsar是什么.md) [A2](part-a-interview/A2-核心架构.md) | 架构图 + [30秒开场](LEARNING-PATH.md#31-30-秒开场背熟再改写) 说一遍 |
| D2 | [A3](part-a-interview/A3-多租户层级.md) [A4](part-a-interview/A4-Topic体系.md) | 全路径 + 分区只增不减 |
| D3 | [A5](part-a-interview/A5-订阅模式.md) | 四种订阅 + 你们该用哪种 |
| D4 | [A6](part-a-interview/A6-ACK与投递语义.md) [A7](part-a-interview/A7-保留与清理策略.md) | TTL≠Retention |
| D5 | [A8](part-a-interview/A8-重试与DLQ.md)、浏览 A10/A12 | 写入→ACK→失败 串讲 |
| D6 | [A11](part-a-interview/A11-BookKeeper深入.md) [附录 B](appendices/B-Kafka对照.md) | E-Q-W + Kafka 3 点 |
| D7 | 复习 A1~A7、[附录 A](appendices/A-面试题与参考答案.md) 25 题 | 错题编号 |

### 第 2 周 — G1 毕业 + G2 入门

| 天 | 内容 | 当天过关 |
|----|------|----------|
| D8 | 附录 A 50 题 | 错题 < 10 |
| D9 | [Part A 毕业考](#part-a-毕业考)、[3分钟自述](LEARNING-PATH.md#32-3-分钟结构面试官最常要) | 全勾 + 自述录音 |
| D10 | [B1](part-b-java-dev/B1-Java客户端基础.md) HelloPulsar | 手写一遍 |
| D11 | [B2](part-b-java-dev/B2-生产者.md) [B3](part-b-java-dev/B3-消费者.md) | Demo 跑通 |
| D12 | [B4](part-b-java-dev/B4-多服务协作.md) [B5](part-b-java-dev/B5-大数据量注意点.md) | 命名规范 |
| D13 | [B6](part-b-java-dev/B6-本地开发.md)、附录 F | stats/peek |
| D14 | 复习 B1~B6 | [B 写代码毕业考](#part-b-写代码-b1b8-毕业考) |

### 第 3 周 — G2 排障调优

| 天 | 内容 | 当天过关 |
|----|------|----------|
| D15 | [B9](part-b-java-dev/B9-排障手册.md) 1~4 | 3 步/场景 |
| D16 | B9 5~12 + Demo | MissingAck/Duplicate |
| D17 | [B10](part-b-java-dev/B10-性能调优.md) L0~L3 | 金字塔 |
| D18 | B10 + Benchmark | 解释 batch |
| D19 | [B11](part-b-java-dev/B11-性能验证.md) | stats 对比 |
| D20 | B9~B11 复习 | [B9~B11 毕业考](#part-b-排障调优-b9b11-毕业考) |
| D21 | 休息/补课 | — |

### 第 4 周 — G2 环境 + G3 改造

| 天 | 内容 | 当天过关 |
|----|------|----------|
| D22 | [B12](part-b-java-dev/B12-环境模型.md) [附录 I/J](appendices/I-环境迁移清单.md) | Standalone≠生产 |
| D23 | [B13](part-b-java-dev/B13-推动策略改造.md) | 何时不改 |
| D24 | [附录 K](appendices/K-方案一页纸模板.md) | K 1~4 节 |
| D25 | [P4](projects/P4-订阅与Topic改造.md) 阶段 0 | 盘点表 |
| D26 | P4 阶段 1 | 关 Auto-Create 等 1 项 |
| D27 | P4 阶段 2 设计 | 改动清单 |
| D28 | 复习 | [B12~B13 毕业考](#b12b13--附录-k--p4-毕业考) |

### 第 5~6 周 — 扩展

见 [LEARNING-PATH 第 5~6 周](LEARNING-PATH.md#第-56-周巩固与扩展按需)。

---

## 毕业考

### Part A 毕业考（G1）

- [ ] 白板画架构（A2）
- [ ] [30 秒 + 3 分钟](LEARNING-PATH.md#三面试怎么讲开场--深入--结合项目) 自述各 1 遍
- [ ] 四种订阅 + Shared/Key_Shared 选型（A5）
- [ ] At least once、Cursor vs Offset（A6）
- [ ] TTL / Retention / Compaction 各一句（A7）
- [ ] 附录 A 随机 10 题 ≥ 8 题
- [ ] **项目结合段**：我们现状 + 改造方向（各 2 句）

### Part B 写代码（G2）

- [ ] Hello + Producer + Consumer 手写
- [ ] DLQ + Key_Shared + `blockIfQueueFull`
- [ ] Topic / subscriptionName 规范
- [ ] `topics stats` + `peek-messages`

### Part B 排障调优（G2）

- [ ] 丢/重/乱/慢 各 3 步（链 [附录 E](appendices/E-排查决策树.md)）
- [ ] 调优金字塔 L0~L2
- [ ] BatchCompareBenchmark 能解释

### B12~B13 + K + P4（G3）

- [ ] Standalone 能/不能
- [ ] 附录 I 14 项勾选
- [ ] 附录 K 能讲 2 分钟
- [ ] P4 阶段 0；阶段 1 或 2 至少一项

---

## 最低够用线（时间紧）

- [ ] [LEARNING-PATH 主线](LEARNING-PATH.md#二一条知识主线全仓库串起来) 能讲
- [ ] A2、A5、A6、A4 + 附录 B
- [ ] B2、B3、B9、B10、B12 + 示例
- [ ] B13 + K + P4 阶段 0~1
- [ ] P2（P1 跳过）
- [ ] Part D [INDEX](part-d-problems/INDEX.md)

---

## 每天收工规则

| 情况 | 动作 |
|------|------|
| 达成当天过关 | ✅ 可停 |
| 2 天未过同一项 | ❌ 不新开章，只补课 |
| Part A 已毕业仍刷 A1 | 改刷附录 A 或 [追问表](LEARNING-PATH.md#33-追问往哪引不要散) |

**日志必写两项：** 过关 / 未过关 + **1 句项目结合**（见 LEARNING-PATH §3.4）

---

## 每日日志

> newest first

### YYYY-MM-DD

- **今日（D?）：**
- **明日：**
- **过关：**
- **项目结合 1 句：**
- **模块状态：**

---

## 相关链接

- **[学习目标路径 LEARNING-PATH](LEARNING-PATH.md)** ← 主线
- [INDEX](INDEX.md)
- [README](../README.md)
