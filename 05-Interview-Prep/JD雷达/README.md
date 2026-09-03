# JD 雷达（猎聘/智联高频 · 面试概念防御）

> 每篇：**三行定稿 + 我们项目怎么做 + 面试追问**（有代码对齐 iot-server；没有的补成熟方案）  
> W1～W6 并行；与压测证据交叉引用时，以 [`GIIC-15万压测参与复盘.md`](../../02-EMQX-IoT-Tuning/GIIC-15万压测参与复盘.md) 为准  
> 详见 [`PLAN.md`](../../PLAN.md) §JD 雷达

| # | 文件 | 状态 | 与现网证据 |
|---|------|------|------------|
| 1 | [01-物模型与设备状态.md](01-物模型与设备状态.md) | **已扩项目实现** | TSL + GIIC 双模型 + EventBus |
| 2 | [02-设备影子与生命周期.md](02-设备影子与生命周期.md) | **已扩项目实现** | 会话三层 + GIIC PSK/Token；Shadow 差距说明 |
| 3 | [03-OTA与固件.md](03-OTA与固件.md) | **已扩项目实现** | push/pull + 状态机 + URL 下发 |
| 4 | [04-时序存储对照.md](04-时序存储对照.md) | **已扩代码链路 + TD 专题** | ES 主 + TD 联调 STAR/10 题 |
| 5 | [05-CoAP与多协议.md](05-CoAP与多协议.md) | **已扩项目实现** | **GIIC CoAP-TCP 主证据线** |
| 6 | [06-规则引擎与流式对照.md](06-规则引擎与流式对照.md) | **已扩项目实现 + Flink 对照** | EventBus 规则 vs Pulsar 级联 |
| 7 | [07-Netty与接入层.md](07-Netty与接入层.md) | **已扩项目实现** | per-connection 背压 + Nginx；Californium≠Netty |

**复习建议**：每周挑 2 篇朗读 30 秒；优先 **05、07、01、03**（和简历最贴）。

**统一口述框架**（每篇末尾都有）：

1. **我们有什么** — 表/类/配置键  
2. **链路怎么走** — 3～5 步数据流  
3. **和业界差什么** — 诚实边界 + 成熟方案一句  
4. **我主责在哪** — 接入/压测/联调，不吹 owner  

**原理参考**：CoAP → `D:\demo\coap` / [`middleware/mqtt`](../../middleware/mqtt/README.md)；Flink → [`middleware/pulsar`](../../middleware/pulsar/docs/appendices/)

**代码仓库**：`d:\gerrit\iot-server`（JetLinks + GIIC 定制）

**真实 JD 采集**：[`../JD采集/README.md`](../JD采集/README.md)
