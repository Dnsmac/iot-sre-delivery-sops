# GIIC 15 万压测参与复盘（面试证据 · 脱敏）

> **状态**：2026-07-23 自现网 `bugfix-readme/giic` **只读同步** + 长稳截图入库  
> **角色边界**：负责 **GIIC CoAP-TCP 网关 / 协议包** 性能改造与压测闭环；**不**写成「全平台 40W 压测方案 owner」  
> **现网原文（只读）**：`D:\gerrit\iot-server\bugfix-readme\giic\`（本仓禁止改现网仓）  
> **关联交付**：W6 手册 [`W1_压测复盘手册.md`](W1_压测复盘手册.md) · 汇总入口 [`40万压测参与复盘.md`](40万压测参与复盘.md) · **运维全栈** [`GIIC-全栈运维优化要点.md`](GIIC-全栈运维优化要点.md)（现网 `docs/ops`）

---

## 0. 30 秒口述版

现网有一条 **GIIC（CoAP-TCP）** 接入路径。压测目标 **15 万在线**（5 台压测机 × 3 万线程），服务端约 **4 节点**。优化前大约 **5 千级**就出现 Login 超时 / Sink 断流，中期曾卡在约 **14.3 万**。我做了连接模型拆分、L1 热缓存、Token 权威改 Redis、Login 写路径减负、Token 异步批写加固等多轮改造；截至 **2026-07-23**，同规模长稳已连续跑满 **4×24h（96h）**，超过验收节点 **72h**。

**加分一句（可选）**：过程中定位过 Redis 慢查询（`KEYS` 扫统计键）、PENDING 队列告警风暴、以及政策禁改 `device-manager` 时的边界取舍；同时入口侧对齐 **Nginx TCP + 内核 sysctl**、库侧 **MySQL 生产档与连接池联动**——面试讲「应用 + 入口 + 库」三层，不只讲改 jar。

---


## 1. 规模与环境（脱敏）

| 项 | 值 |
|----|-----|
| 协议路径 | GIIC over **CoAP-TCP**（非主讲 MQTT 接入线） |
| 目标在线 | **15 万（150k）** |
| 压测模型 | 5 机 × `giic_30k_*`，每机 **30k** 活跃线程 → **合计 150k** |
| 服务端 | 约 **4 节点** Java（khlinks / iot-server 系） |
| 业务路径 | 预注册设备 → PSK → **Login** → Heartbeat / Data / **Refresh** |
| 验收节点（现网口径） | **15W × 72h**；全量目标 **15W × 7D** |
| 本次进度 | 已连续长稳 **4×24h = 96h**（≥72h 节点） |

---

## 2. 四要素（面试主表）

| 项 | 内容 |
|----|------|
| **瓶颈** | ① 全局单管道 Sink 背压；② 热路径 Registry/Redis/DB 风暴；③ 跨节点 L1 token 不一致误杀；④ Login 写 configuration 放大 → 卡在 ~14.3W；⑤ 后期 Token 异步队列 PENDING 堆积 + Redis 慢命令（`KEYS` / 大 HSET） |
| **改动（我负责段）** | `per-connection` 连接模型；GIIC L1 热缓存 + miss/reload；Login persist 减负；Token 权威迁 **Redis**；async 批写 + **r8 队列/日志加固**；公共层 **SCAN 替 KEYS**；**协助** 入口 Nginx/sysctl、MySQL 生产档对齐（见 [`GIIC-全栈运维优化要点.md`](GIIC-全栈运维优化要点.md)） |
| **结果** | 从「~5k 即失败 / 中期卡 14.3W」推到 **15W 在线可长稳**；**96h** 窗口内压测侧线程水位平稳（见 §4 截图） |
| **角色** | **负责** GIIC 协议/网关侧改造与压测验收闭环；入口/MySQL/Nginx·LVS **协助对齐**（非单独 DBA/网工 owner）；**禁改** `device-manager`（见 §3.1） |

---

## 3. 改造时间线（脱敏摘要）

> 细节与开关以现网 hotfix 为准；面试只记 **分层 + 结果**，不背类名全文。

| 轮次 | 内部代号 | 一句话 |
|------|----------|--------|
| v1 | `giic-perf-150k` | 抽公共 `handleExchange`；L1 热缓存；`per-connection`；Skip 热路径多余 persist |
| r2 | `giic-perf-150k-r2` | Login grace / LVS 漂移兜底；验收改为 **72h/7D**；压测配置 = 上线配置 |
| r3 | `giic-l1-auth-r3` | L1 miss 与 hit 对称 reload；防 stale loader 写回 |
| r4 | `giic-login-storm-r4` | invalidate 异步；冷 Login 减 headers；`setConfigs` 批量写 |
| r5 | `giic-login-storm-r5` | Token 权威 → **Redis HASH**（离开 configuration 大字段） |
| r6 | `giic-refresh-prev-access-r6` | Refresh 后 prevAccess 宽限 |
| r7 | `giic-token-async-batch-r7` | L1 先回 + Redis 异步批写（可回滚 sync） |
| r8 | `giic-token-async-flush-r8` | PENDING overloaded **日志限频**；抬高 batch/concurrency/capacity，减轻刷盘跟不上入队 |
| 旁路 | `RedisScanUtils` | `smartKeys`：**SCAN 优先、失败再 KEYS**（缓解 DFX 等统计扫键拖慢 Redis） |
| 运维 | `docs/ops` | 入口 **内核 sysctl + Nginx TCP**；**MySQL 三档生产 cnf** + 连接池联动（详见运维要点文） |

### 3.1 诚实边界（面试必背 · 防吹）

| 项 | 口径 |
|----|------|
| **device-manager** | 曾规划 `refactorHeader` skip、`event-bus-fire-and-forget`；**项目政策禁止改该模块**，已回滚且永不合入。协议侧仍可预填 header（无害）；connector 仍走 `getSelfConfigs` / 等 EventBus 完成 |
| **端侧** | 鉴权失败服务端**不断连**；压测端 2s 重试 / 关 TCP 导致 Offline→无 PSK Refresh，属端/链路策略，不吹成「服务端必改」 |
| **运维** | Nginx hash / 临时端口 / LVS、MySQL 生产档：**协助对齐与文档**（`docs/ops`），不吹「全公司内核/DBA 唯一 owner」 |
| **未做 / 另案** | Refresh 免 PSK、secret 全量预热、大 `HSET pskContext` 字段瘦身（定位过，未必本轮合入） |

### 3.2 分层瓶颈 → 对应手段（白板口述用）

```text
压测端 5×30k ──TCP──► 入口 Nginx（sysctl + Stream 代理）
                         │ hash(ip+port) / 防摘流 / 大 backlog
                         ▼
                    网关 CoAP-TCP（per-connection 队列）
                         │ PSK / Login / HB / Data / Refresh
                         ▼
                    协议包 L1 + Token Redis（async 批写）
                         │ DeviceMessage
                         ▼
                    DeviceMessageConnector → EventBus → ES/MySQL/…
                         │
                    Redis（路由 / token / 统计 KEYS→SCAN）
                    MySQL（生产档 buffer + 连接池联动）
```

| 层 | 典型症状 | 手段（你做过的 / 对齐过的） |
|----|----------|----------------------------|
| **入口** | errno 99、no live upstreams、少 IP 打爆单机 | sysctl 临时端口；Nginx hash(ip+port)、max_fails、proxy_timeout |
| 网关管道 | Sink 断流、全局背压 | `per-connection`；Sink reject；skip-persist-on-data |
| 鉴权/Token | Login 风暴、access 不匹配 | L1 + Redis HASH；prevAccess；async 批写 + r8 |
| Registry/DB | 热路径写放大；库连接顶满 | Login 减负；**MySQL 档位 + 池联动**（禁改 connector 后靠上游减负） |
| Redis | OPS 不高但延迟尖刺 | 慢日志：`KEYS dfx:*`、大 HSET；SCAN 优先；观察 PENDING |

### 3.3 关键配置口径（现网可与仓库默认不同）

面试被问「你们开了啥开关」时，只讲**职责**，不背数值：

| 前缀 | 干什么 |
|------|--------|
| `giic.connection-model=per-connection` | 每 TCP 独立队列 |
| `giic.perf.skip-persist-on-data` | Data/HB 跳过会话 PSK 持久化 |
| `giic.security.psk-grace-ms` / `login-pending-grace-ms` | PSK 后 / Login 排队中的放行宽限 |
| `giic.cache.*` | 协议包 L1（改后需重打协议包上传） |
| `giic.token.persist-mode=async` | L1 先回 200，权威源批写 |
| ~~`event-bus-fire-and-forget`~~ | **已删除**；禁改 device-manager |

---

## 4. 长稳证据：4×24h（截图入库）

**截图**：[`evidence/giic-15w-jmeter-dashboard-2026-07-23.png`](evidence/giic-15w-jmeter-dashboard-2026-07-23.png)  
**面板**：Apache JMeter Dashboard · Transaction=`GIIC Heartbeat` · 时间窗 **Last 24 hours**（长稳过程中的日切片）  
**采集日**：2026-07-23

### 4.1 Active Threads（压测侧）

| Application | Active Threads（稳态） |
|-------------|------------------------|
| `giic_30k_1` … `giic_30k_5` | 各 **30,000** |
| **合计** | **150,000** |

→ 与「5×3W = 15W」模型一致，日切片内线程水位平坦。

### 4.2 GIIC Heartbeat TPS（日切片读数）

| Application | Mean（约） | Max（约） | 切片末附近 |
|-------------|------------|-----------|------------|
| `giic_30k_3` | ~16.8 | ~30 | ~19.5 |
| `giic_30k_4` | ~16.7 | ~27 | ~19.4 |
| `giic_30k_5` | ~17.3 | ~95（尖刺） | ~19.6 |

> 面试口径：用 **在线规模 + 长稳时长 + 错误边界**；单机 Heartbeat 曲线作辅助，不把 Max 尖刺吹成「吞吐能力」。

### 4.3 同屏其他应用（勿混叙事）

截图同屏还有 `HA50w-*` 等应用（吞吐更高、Errors=0）。**本复盘主叙事仍是 GIIC 15W**；HA 线另开条目，禁止把两条线拼成「我主导 50W」。

### 4.4 相对验收表的位置

| 阶段 | 现网标准 | 本仓记录（2026-07-23） |
|------|----------|------------------------|
| Ramp | 升至 15W | 已能维持 5×30k 线程 |
| **T-72h** | ≥72h 稳态 | **已超过：连续 96h（4×24h）** |
| T-7D | 168h | **进行中 / 待补最终累计错误表** |

**待你补一句（收工时填）**：96h 累计 JMeter HB/Refresh/Report 失败数是否为 0？服务端四类 error 是否无风暴？

| 项 | 填空 |
|----|------|
| 96h 累计错误（HB/Refresh/Report） | ______ |
| 服务端 error 风暴 | 无 / 有（简述） |
| 是否已进入 / 完成 7D | ______ |

---

## 5. 指标表（W6 §0.1 可直接抄）

| 指标 | 压测前 / 中期 | 调优后（当前） | 单位 |
|------|---------------|----------------|------|
| 在线 / 压测线程 | ~5k 即挂；中期卡 ~14.3W | **15W（5×30k）可维持** | 连接 |
| 长稳时长 | 30min 冒烟不足 | **已跑 96h（4×24h）**；目标 7D | 小时 |
| Heartbeat（日切片） | — | 单机 mean ~17 req/s 量级 | TPS |
| 角色 | — | 协议/网关侧改造负责人（非全平台 owner） | — |

---

## 6. 简历 bullet 草稿（参与表述 · 可投）

- 参与物联网平台 **GIIC（CoAP-TCP）15 万级**长连接压测：负责网关连接模型与协议侧热路径优化（L1 缓存、Token Redis 化、Login 写放大治理），支撑 **15 万在线连续长稳 ≥96h（4×24h）**；证据：本文件 + JMeter 截图。

**禁止写法**：主导 40 万全场 / 独立架构方案 owner / 把 HA50w 吞吐算进个人成果。

---

## 7. 现网只读索引（核对用，勿提交未脱敏原文）

| 文件（现网） | 用途 |
|--------------|------|
| `bugfix-readme/giic/giic-perf-150k-INDEX.md` | 版本索引 |
| `hotfix_giic-perf-150k-readme.md` | v1 冻结 |
| `hotfix_giic-perf-150k-r2-readme.md` | 72h/7D 验收口径 |
| `hotfix_giic-l1-auth-r3-readme.md` … `…-r8-….md` | 后续轮次（含 Token flush / SCAN） |
| `2026-07-11-GIIC-150k-修改项清单.md` | 配置与 T-R / T-72h / T-7D |

---

## 8. 面试追问速答（基于实战）

| 问 | 答（≤40 秒） |
|----|--------------|
| 为什么卡在 14 万？ | Login/写配置风暴 + L1 不一致误杀 + 全局管道背压叠在一起；不是单点「机器不够」 |
| async Token 会丢吗？ | L1 先回，权威源批写；挂了靠 reload/宽限；r8 解决的是 **队列跟不上 + 日志风暴**，不是改协议语义 |
| 为啥不改 EventBus fire-and-forget？ | **禁改 device-manager**；影响是 connector 仍等 publish、仍可能 `getSelfConfigs`；用网关/协议/Redis 侧卸压顶住 |
| KEYS 有什么问题？ | 阻塞式扫键，统计前缀在压测时拖慢 Redis；公共工具改 **SCAN 优先** |
| 为啥还调 Nginx/MySQL？ | 长连接全代理会耗尽出站端口、误摘 upstream；库要 buffer + 连接池联动。**三层齐**才到 15W，详见运维要点文 |
| 和 MQTT 40 万啥关系？ | **不同接入线**；我主讲 GIIC 15W；40W/级联是背景协助，见汇总入口 |

---

## 9. 同步记录

| 日期 | 动作 |
|------|------|
| 2026-07-23 | 从现网 giic 目录脱敏摘要入库；JMeter Dashboard 截图落入 `evidence/`；标明已压 **4×24h** |
| 2026-07-23 | 补 r7/r8、SCAN、device-manager 边界、分层瓶颈与追问速答（对齐近期压测实作） |
| 2026-07-23 | 挂入 `docs/ops`：Nginx/sysctl/MySQL 全栈 → [`GIIC-全栈运维优化要点.md`](GIIC-全栈运维优化要点.md) |
