# 冲刺日历全链路整改 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 2026-09-02～12-15 冲刺日历改造成唯一、可执行、可验收的求职入口，并让七个必问维度能从真实项目连续深追和主动引导。

**Architecture:** 先建立数字/边界真相源并修复冲突，再补真实场景深追脚本，随后重排完整日历，最后联动入口规则和反馈闭环。内容审查与编排审查相互独立，任何 P0/P1 发现都必须回修后重验。

**Tech Stack:** Markdown、PowerShell、ripgrep

## Global Constraints

- 冲刺日历是 09-02～12-15 唯一每日执行入口。
- 项目真实用过的必问题必须说明项目具体用法并带钩子；未用过的标“了解级/官方变体”。
- 不编造数字、表结构、故障、实测或 owner 身份。
- `D:\gerrit\iot-server` 只读。
- 每日最多 P0/P1/P2 三项。
- 9 月 2h；10 月工作日 60～90min/休假日 30min；11 月 40min 复习加投递/面试。

---

### Task 1: 修复技术真相并建立唯一索引

**Files:**
- Create: `05-Interview-Prep/数字与边界-唯一索引.md`
- Modify: `05-Interview-Prep/举一反三-超简历追问包.md`
- Modify: `05-Interview-Prep/选型深挖-为什么这么设计.md`
- Modify: `05-Interview-Prep/JVM硬核-L4口播稿.md`

- [ ] 修正设备上报 EventBus 与 Pulsar 级联边界。
- [ ] 修正 operatorCache 为 DeviceOperator/物模型对象树。
- [ ] 分开 8G OOM 案例与 32G GIIC 规划。
- [ ] 写链路、数字四态、角色边界和 ERP 证据边界索引。
- [ ] 用 `rg` 验证三处冲突无残留。

### Task 2: 补七维真实项目深追与钩子

**Files:**
- Create: `05-Interview-Prep/面试连环深追脚本.md`
- Modify: `05-Interview-Prep/带节奏-钩子反抛话术卡.md`
- Modify: `05-Interview-Prep/stories/电商-高并发模块.md`
- Modify: `05-Interview-Prep/通用场景题-L4口播稿.md`
- Modify: `05-Interview-Prep/MySQL硬核-L4口播稿.md`
- Modify: `05-Interview-Prep/Redis硬核-L4口播稿.md`
- Modify: `05-Interview-Prep/JVM硬核-L4口播稿.md`
- Modify: `05-Interview-Prep/面试备战计划书-必问L4.md`

- [ ] 每个维度写入口问、项目用法、数字/证据、机制、Why/代价、3～5 连追、迁移、反抛、边界。
- [ ] 增加 ERP 钩子，但未知事实明确为待本人补证，不编造。
- [ ] 把推荐/广告等弱项目绑定题降为了解级。
- [ ] 给 MySQL/Redis/JVM 高频题增加项目锚点；没有生产使用的明确说了解级。
- [ ] 修正“七维全部 L4”的过度结论。

### Task 3: 补齐口述、模拟和投递闭环文件

**Files:**
- Create: `05-Interview-Prep/口述稿/W7-电商.md`
- Create: `05-Interview-Prep/口述稿/W8-完整串联.md`
- Create: `05-Interview-Prep/口述稿/_复盘模板.md`
- Create: `05-Interview-Prep/口述稿/mock-01-复盘.md`
- Create: `05-Interview-Prep/口述稿/mock-02-复盘.md`
- Create: `05-Interview-Prep/口述稿/mock-03-复盘.md`
- Create: `05-Interview-Prep/口述稿/mock-04-复盘.md`
- Create: `05-Interview-Prep/口述稿/mock-05-复盘.md`
- Create: `05-Interview-Prep/投递跟踪表.md`
- Create: `05-Interview-Prep/面试复盘日志.md`

- [ ] 两份口述稿包含录音记录表和边界提醒。
- [ ] 模拟模板包含被问倒原话、断点、补证据路径、回灌题号、复测日期。
- [ ] 投递表包含岗位状态和下一动作。
- [ ] 真面试复盘支持 24h 内回灌到后续日历。

### Task 4: 重排 09-02～12-15 冲刺日历

**Files:**
- Modify: `05-Interview-Prep/冲刺日历-2026-09-02.md`

- [ ] 重写总使用规则和 P0/P1/P2 定义。
- [ ] 修正 9 月周界、过载、空档和场景轮换。
- [ ] 10 月逐日写具体题号、项目钩子验收和周验收。
- [ ] 11～12 月写固定周节奏、投递 KPI、模拟/真面试复盘和 gap 回灌。
- [ ] 每日任务不超过三项，均有时间、路径、题号/章节和验收。

### Task 5: 统一入口、阶段和每日教练协议

**Files:**
- Modify: `PROGRESS_LOG.md`
- Modify: `README.md`
- Modify: `PLAN.md`
- Modify: `.cursorrules`
- Modify: `.cursor/rules/daily-coach-protocol.mdc`
- Modify: `docs/每日协作约定.md`
- Modify: `05-Interview-Prep/学习路径与面试串讲.md`
- Modify: `05-Interview-Prep/IoT主线规划-填空版.md`

- [ ] 所有入口统一为 `PROGRESS_LOG 快照 → 冲刺日历当天`。
- [ ] 修正 10 月/11 月、W7/W8/W10 日期冲突。
- [ ] 冲刺期不再硬读 W1 手册。
- [ ] 收工时记录录音元数据和 open gap；次日只回灌 Top1。
- [ ] 旧规划标为历史/索引，不再竞争日课入口。

### Task 6: Verification 与双重独立复查

**Files:**
- Modify: 本计划（完成项勾选）
- Modify: 复查发现问题涉及的文件

- [ ] 内容审查：七维九项门禁、真实项目用法、边界、数字证据、连续追问。
- [ ] 编排审查：09-02～12-15 覆盖、每日负载、链接、验收、最终目标。
- [ ] 主 Agent 检查完整 diff 和新增文件。
- [ ] 运行入口、日期、时长、红线、三处技术口径、死链和 `Test-Path` 验证。
- [ ] 回修所有 P0/P1 后重复审查和命令验证。
- [ ] 输出唯一“每天怎么用”交接说明。
